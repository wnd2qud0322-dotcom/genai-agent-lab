# Day 05 — LangSmith & Multi-Agent

Day04까지는 Agent 하나를 어떻게 만드는지 배웠다면, Day05는 그 Agent를 **"눈으로 관찰하는 도구(LangSmith)"**와, 여러 Agent를 **"조합해서 쓰는 두 가지 패턴(MoA, Orchestrator-Worker)"**을 정리한 노트다.

<br>

---

<br>

## 01. LangSmith — LLM 앱 추적(Observability)

**필요성**: 지금까지 체인/에이전트 내부가 궁금할 때마다 `print()`를 넣어 확인했다. LangSmith는 이 `print()` 디버깅을 대체하는 전용 웹 대시보드로, 코드 수정 없이 모든 실행을 자동 기록한다.

```python
os.environ["LANGSMITH_API_KEY"] = langsmith_key
os.environ["LANGSMITH_TRACING"] = "true"            # 이 한 줄로 모든 실행이 추적된다
os.environ["LANGSMITH_PROJECT"] = "langsmith-basic"  # 대시보드에서 실행을 묶는 단위
```
이 환경변수 3줄만 기존 코드 앞에 추가하면, 그 아래 실행되는 **모든 LangChain/LangGraph 코드가 코드 수정 없이 자동 추적**된다 — 기존에 작성해둔 체인이나 Agent라도 예외 없이 적용된다.

**사용 목적**: 프롬프트를 바꿔가며 **답변 품질·토큰 비용을 비교(A/B 테스트)**하기 위함이다.

`run_name`/`tags`/`metadata`는 실제 동작에는 영향을 주지 않는, **대시보드에 붙이는 이름표**다.
```python
config = RunnableConfig(
    run_name="qa_chain",
    tags=["demo", "qa", "v1"],
    metadata={"prompt_version": "v1", "model_name": "gpt-4o-mini"},
)
chain.invoke({"question": q}, config=config)
```
나중에 대시보드 필터에서 `Tags=v1`처럼 걸러보기 위한 용도다 (State가 실제 데이터를 담는 "택배 내용물"이라면, 이건 "택배 겉면 송장 스티커"에 가깝다).

<br>

---

<br>

## 02. LangSmith로 Agent 추적하기

**필요성**: 체인 Trace는 한 줄로 흐르지만, Agent는 Day04에서 배운 대로 "판단→행동→판단"을 반복하는 **루프**라서 Trace 모양도 다르다.

```
agent (root)
├─ model 호출 1  → tool_calls [get_weather, calculate]   ← 판단
├─ get_weather   → 입력/출력 확인 가능                    ← 행동
├─ calculate     → 입력/출력 확인 가능
└─ model 호출 2  → 최종 답변                              ← 종합
```

**확인할 것 4가지**:
1. **루프 횟수** — `model` 호출이 몇 번인가 (최소 2회: 판단 + 최종답변)
2. **도구 입출력** — LLM이 도구에 넘긴 인자가 의도대로 만들어졌는지 (도구 호출 실패의 대부분은 "LLM이 잘못된 인자를 만든 것"이며, 콘솔 출력으로는 안 보이고 Trace에서만 정확히 보인다)
3. **단계별 토큰** — 도구 결과가 대화 기록에 누적되므로, 뒤로 갈수록(반복이 늘수록) input 토큰이 커진다 → 비용이 가속되는 이유
4. **태그 필터** — 01에서 배운 방식 그대로 원하는 실행만 필터링

**선택적 추적** — 전부 추적하면 노이즈가 쌓이므로, 평소엔 꺼두고 필요한 구간만 켠다:
```python
os.environ["LANGSMITH_TRACING"] = "false"          # 전역으로 끔

with tracing_v2_enabled(project_name="..."):        # 이 블록 안에서만 켬
    result = agent.invoke(...)

os.environ["LANGSMITH_TRACING"] = "true"            # 다시 켬
```

**배치 실행으로 비교 분석**: 여러 질문을 `for`문으로 순서대로 실행하고, 각각 다른 `run_name`/`tags`를 붙여서 대시보드에서 나란히 비교한다 (도구 0개/1개/2개 질문의 토큰 차이 비교 등). 실행이 백그라운드로 비동기 전송되므로, 스크립트가 먼저 끝나 데이터가 유실되지 않도록 마지막에 `wait_for_all_tracers()`로 전송 완료를 보장한다.

<br>

---

<br>

## 03. MoA (Mixture of Agents) — 병렬 멀티에이전트

**필요성**: 하나의 질문을 여러 관점에서 동시에 조사해서, 더 균형 잡힌 답을 만들고 싶을 때 쓰는 패턴이다.

```
              +-> market_research    (시장 분석)   +
START --------+-> risk_research      (리스크 분석) +-> aggregator -> END
              +-> opportunity_research(기회 탐색)   +
```

**핵심 — Fan-out / Fan-in**: 지금까지의 `add_conditional_edges`는 "여러 갈래 중 하나만" 골랐지만, 이건 `add_edge`를 START에서 여러 번 반복해 **3개를 동시에(병렬로)** 실행(Fan-out)한 뒤, 전부 `aggregator`로 모은다(Fan-in). 조건부 분기가 아니라 **병렬 실행 구조**라는 게 핵심이다.

**State 설계**: 3개 에이전트가 동시에 실행되므로, 같은 필드에 쓰면 서로 덮어쓴다. 그래서 `market_report`/`risk_report`/`opportunity_report`처럼 **각자 전용 필드**를 따로 둔다.

**사용한 API 2가지**:
- **ChatOpenAI(GPT)**: 3개 리서치 에이전트 + aggregator, **4곳 전부**에서 "생각하는 뇌" 역할
- **EXA**: AI 리서치에 특화된 유료 웹 검색 API. 3개 리서치 에이전트만 도구로 사용 (aggregator는 사용하지 않음)

**Middleware 실전 활용**:
```python
ToolCallLimitMiddleware(tool_name="exa_search", thread_limit=5, run_limit=5)  # 호출 횟수/속도 제한
ToolRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0)      # 실패 시 자동 재시도
```
Day04에서 개념만 배운 Middleware가 **외부 API를 안전하게 호출하기 위한 실전 도구**로 쓰인다.

**"3단계 구성"의 이유**: `prompt 작성 → _agent_core(create_agent) 생성 → def wrapper 함수` 순서로 한 단계 더 있는 이유는, `MoAState`가 표준 `messages` 필드가 아니라 `user_input`/`market_report` 같은 커스텀 필드를 쓰기 때문이다. `create_agent`는 항상 `{"messages": [...]}` 형식으로 입출력하므로, 그래프의 State(다른 필드 이름)와 그 사이를 통역해주는 wrapper 함수(`state에서 값 꺼내기 → messages로 변환 → agent 호출 → content 추출 → 반환`)가 추가로 필요하다.

**`aggregator`는 Agent가 아니라 평범한 LLM 호출 하나**다 — 도구도, `create_agent()`도 없다. 이미 3개 에이전트가 검색해서 만들어둔 리포트 텍스트를 프롬프트에 다 넣고 종합만 하면 되기 때문이다.

<br>

---

<br>

## 04. Orchestrator-Worker (Supervisor 패턴) — 계층형 멀티에이전트

**필요성**: MoA는 항상 3개를 동시에 실행하지만, 실무에서는 "이번엔 리서치만 필요, 저번엔 리서치+분석+작성이 다 필요" 처럼 **상황에 따라 다른 조합**이 필요할 때가 많다. Supervisor 패턴은 관리자가 상황을 보고 필요한 전문가에게만, 필요한 순서로 일을 시키는 구조다.

**핵심 트릭 — "에이전트 전체를 도구로 감싸기"**:
```python
research_agent = create_agent(llm, tools=[search_web, search_news], system_prompt=RESEARCH_AGENT_PROMPT)

@tool
def research_topic(request: str) -> str:
    """주제를 리서치하여 핵심 발견사항을 정리합니다."""
    result = research_agent.invoke({"messages": [{"role": "user", "content": request}]})
    return result["messages"][-1].content   # 최종 응답만 반환, 중간 과정은 숨김
```
지금까지 `@tool`은 `calculator`처럼 **생각 없는 단순 함수**를 감쌌지만, 여기선 **그 자체로 완전한 ReAct 루프를 가진 에이전트(`research_agent`)를 통째로 감싼다.** Supervisor 입장에선 "도구 하나 부른 것"처럼 보이지만, 실제로는 그 안에서 하위 에이전트가 "도구를 쓸지 말지"를 또 스스로 판단하는 미니 루프가 통째로 돌아간다.

**3단 구조**:
```
Supervisor (create_agent)
   └─ tools = [research_topic, write_section, run_code]   ← 각각 "agent를 감싼 tool"
        ├─ research_topic → research_agent (EXA 웹/뉴스 검색)
        ├─ write_section  → writer_agent (마크다운 작성 + 자체 품질 검증)
        └─ run_code       → code_agent (E2B 샌드박스 코드 실행)
```
Research/Writer/Code 세 Sub-agent는 **동등한 자격의 완전한 agent**다 (도구 개수만 다를 뿐). "agent를 tool로 감싸는" 트릭은 Supervisor 계층에서만 쓰이고, 그 하위(Sub-agent가 실제로 쓰는 도구: `search_web`, `validate_markdown_section`, `e2b_code_interpreter`)는 다시 평범한 단순 함수 도구다 — 무한히 에이전트가 에이전트를 감싸는 구조는 아니다.

**MoA와의 결정적 차이**:

| | MoA | Orchestrator-Worker |
|---|---|---|
| 실행 방식 | 3개 다 **동시에** 병렬 실행 | Supervisor가 **필요한 것만, 순서대로** 위임 |
| 복합 요청 | 항상 3개 다 실행 | "리서치→분석→작성"처럼 **단계적으로 체인** |

**`E2B` 샌드박스**: LLM이 만든 Python 코드를 실행할 **격리된 클라우드 가상 환경**. Day03~04의 `safe_eval`(위험한 연산을 아예 못 만들게 제한)과 접근이 다르다 — E2B는 **"코드는 자유롭게 실행하게 두되, 실행 장소 자체를 내 컴퓨터가 아닌 격리된 곳으로 옮기는" 방식**이다. 사용 후 비용 절감을 위해 `sandbox.kill()`로 종료해야 한다.

**(심화) `ToolRuntime`/`InjectedState`**: 기본적으로 Sub-agent는 Supervisor가 전달한 `request` 문자열만 본다. `Annotated[dict, InjectedState]`를 쓰면 Supervisor의 **전체 대화 맥락**(예: "대상 독자는 AI 엔지니어")까지 Sub-agent에게 전달할 수 있다.

<br>

---

<br>

## 05. Human-in-the-Loop (HITL) — 실행 중 사람 승인

**필요성**: 코드 실행처럼 위험할 수 있는 작업은, 실행 전에 사람이 한 번 확인하고 넘어가게 만들고 싶을 때 쓴다.

```python
code_agent_with_review = create_agent(
    llm, tools=[e2b_code_interpreter], system_prompt=CODE_AGENT_PROMPT,
    middleware=[HumanInTheLoopMiddleware(interrupt_on={"e2b_code_interpreter": True}, ...)],
)

supervisor_with_hitl = create_agent(
    llm, tools=[research_topic, write_section, run_code_reviewed],
    system_prompt=SUPERVISOR_PROMPT,
    checkpointer=InMemorySaver(),   # 일시중지/재개 상태 저장에 필수
)
```
- `interrupt_on`에 지정된 **그 도구가 호출되려는 순간에만** 실행이 멈춘다. 다른 도구(리서치, 글쓰기)는 그대로 자유롭게 실행된다.
- 질문 자체가 코드 실행이 필요 없다면(예: 단순 웹조사+글쓰기), Supervisor가 그 도구를 아예 안 부르므로 **HITL이 걸릴 기회 자체가 없다** — 정상 동작이다.
- `checkpointer`는 **멈춘 상태를 저장했다가, 승인 후 그 지점부터 이어서 실행**하기 위해 최상위 에이전트(Supervisor)에만 필요하다.

**승인 재개**:
```python
resume = {interrupt_.id: {"decisions": [{"type": "approve"}]} for interrupt_ in interrupts}
supervisor_with_hitl.stream(Command(resume=resume), config)
```
**주의**: 여기서 `{"type": "approve"}`처럼 코드에 값을 미리 고정해두면, 이건 "사람이 실시간으로 결정하는 것"이 아니라 **그냥 자동 승인 코드**일 뿐이다. 진짜로 그때그때 사람에게 물어보려면 `input()`으로 실시간 입력을 받아야 한다:
```python
answer = input("이 작업을 승인하시겠습니까? (y/n): ")   # 여기서 실제로 멈추고 기다림
decision = "approve" if answer.lower() == "y" else "reject"
```
`approve`를 `reject`로 바꾸는 것만으로는 "다르게 고정된 자동 응답"이 될 뿐, `input()`을 넣어야 비로소 실행 중간에 진짜 사람의 실시간 판단을 받는 것이다.
