# Day 04 — LangGraph & Single Agent

Day03에서 배운 LCEL(일직선 체인)만으로는 "필요하면 반복하고, 상황에 따라 다른 길로 가는" Agent를 만들 수 없다. Day04는 LangGraph로 그 반복·분기를 구현하고, `create_agent()`가 그걸 어떻게 자동화해주는지 정리한 노트다.

<br>

---

<br>

## 01. LangChain vs LangGraph

**필요성**: 이 둘을 혼동하면 "무엇을 배우고 있는지"가 헷갈린다. LangChain은 부품, LangGraph는 그 부품을 반복·분기 구조로 조립하는 틀이라는 구분이 이후 모든 내용의 전제가 된다.

| | LangChain | LangGraph |
|---|---|---|
| 정체 | 프롬프트/LLM/파서/도구 등 **부품 제공** | 부품들을 **Node(함수)+Edge(연결)**로 엮는 범용 워크플로우 프레임워크 |
| 기본 구조 | `prompt \| llm \| parser` — 한 방향으로만 흐름 | State를 주고받으며 정해진 순서·조건에 따라 실행. **반복(루프)과 분기 모두 가능** |
| 한계/특징 | 반복·조건 분기 불가 | LLM 전용이 아님 — 임의의 함수(Node)를 상태 기반으로 연결하는 범용 도구 (카운터처럼 LLM 없는 그래프도 가능) |

**ReAct(Reasoning+Acting) 패턴**은 LangGraph로 만들 수 있는 여러 그래프 모양 중 하나일 뿐이다 — "ReAct vs LangGraph"가 아니라 **"LangGraph로 ReAct를 구현한다"**가 정확한 관계다.

<br>

---

<br>

## 02. `create_agent()` — 기본 사용법

**필요성**: Day03의 Function Calling에서 "도구 필요 판단 → 실행 → 결과 재전달"을 직접 반복문으로 짰던 것을, `create_agent()`는 함수 하나로 자동화해준다.

```python
agent = create_agent(
    model=model,        # LLM
    tools=[tool1, tool2],  # 사용할 도구 리스트
    system_prompt="..."    # 행동 지침
)

response = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
print(response["messages"][-1].content)
```

- 입출력은 항상 `{"messages": [...]}` 형태 — `HumanMessage`/`AIMessage`/`ToolMessage` 리스트
- 도구가 여러 개면 LLM이 질문 내용을 보고 **어떤 도구를 쓸지 스스로 판단**

**ReAct 패턴의 동작 원리**:
```
① 추론(Reasoning): 이 질문엔 어떤 도구가 필요한가? LLM이 판단만 함
② 행동(Acting): 필요하다고 판단되면, 코드가 실제로 그 도구(함수)를 실행
③ 관찰(Observation): 실행 결과를 LLM에게 다시 전달
④ 답이 안 나왔으면 ①~③ 반복, 나왔으면 최종 답변
```
**중요**: LLM은 "이 도구를 써야 한다"는 텍스트 요청만 만들 뿐, **도구를 직접 실행하는 주체는 항상 코드**다. Tool Calling의 핵심 원칙(Day03)이 여기서도 그대로 적용된다.

**좋은 시스템 프롬프트 설계**: 역할(Role)·톤앤매너·제한사항을 XML 태그 등으로 구조화해서 명시하면 Agent의 행동이 훨씬 안정적으로 통제된다 (Day02 R-T-C-F의 실전 적용).
```python
CUSTOMER_SERVICE_PROMPT = """당신은 온라인 쇼핑몰의 고객 서비스 담당자입니다.
<역할> ... </역할>
<톤앤매너> ... </톤앤매너>
<제한사항> ... </제한사항>"""
```

<br>

---

<br>

## 03. StateGraph 기초

**필요성**: `create_agent()`가 내부에서 실제로 조립하는 것이 바로 이 StateGraph다. 껍데기(create_agent) 말고 알맹이(StateGraph)를 알아야 Agent의 동작을 근본적으로 이해할 수 있다.

**기본 뼈대** — 이후 모든 LangGraph 코드가 이 순서를 따른다:
```
라이브러리 임포트 → State 정의 → 노드 함수 정의
→ StateGraph 생성 + add_node → add_edge(+조건부) → compile() → invoke()/stream()
```

```python
class MyState(TypedDict):
    count: int
    msg: str

def counter(state: MyState):
    state["count"] += 1
    return state

workflow = StateGraph(MyState)
workflow.add_node("Node1", counter)
workflow.add_edge(START, "Node1")
workflow.add_edge("Node1", END)

app = workflow.compile()      # ← 설계도를 "실행 가능한 객체"로 변환
result = app.invoke({"count": 0, "msg": "hello"})
```

- **State**: 각 노드가 주고받는 데이터 그릇. `messages`만 있는 게 아니라, `count`/`msg`처럼 임의의 필드를 직접 정의해 쓸 수도 있음 (LangGraph는 LLM 전용이 아님을 보여주는 예)
- **`compile()`**: `add_node`/`add_edge`로 쌓은 건 아직 "설계도"일 뿐 — `compile()`을 거쳐야 실제로 `invoke()` 가능한 객체가 됨
- **순서 보장**: 실행 순서는 `add_edge`가 강제하는 것이지, 상태값(예: 카운터)으로 "증명"되는 게 아님 — state는 그 상태가 노드 사이에서 끊기지 않고 이어받아 누적된다는 걸 보여줄 뿐
- **`invoke()` vs `stream()`**: `invoke()`는 최종 결과만 반환, `stream()`은 `{"노드이름": {...}}` 형태로 각 노드가 끝날 때마다 중간 결과를 순서대로 반환

<br>

---

<br>

## 04. 조건부 엣지 (Conditional Edges)

**필요성**: `add_edge()`만으로는 무조건 정해진 다음 노드로만 갈 수 있다. "상황에 따라 다른 노드로 분기"하려면 조건부 엣지가 필요하고, 이게 Agent가 "도구를 쓸지 말지" 스스로 판단하게 만드는 메커니즘의 정체다.

```python
workflow.add_conditional_edges(
    "weather",          # ① 분기가 시작되는 노드
    forecast_weather,   # ② 조건 함수 — State를 보고 "키"(문자열) 하나를 반환
    {                   # ③ 라우팅 맵 — 그 키를 실제 노드 이름으로 매핑
        "option_a": "rainy",
        "option_b": "sunny",
    },
)
```

- **조건 함수의 반환값 ≠ 실제 노드 이름**인 경우가 많다 — 그래서 라우팅 맵으로 "키 → 실제 노드"를 따로 연결해줌 (조건 함수와 실제 노드를 분리해서 유연하게 만든 설계)
- 2갈래뿐 아니라 **3갈래 이상**도 가능하고, `"__else__"` 같은 키로 예상 밖 값에 대한 기본 경로도 만들 수 있음
- **`add_edge("tools", "call_model")`처럼 "되돌아가는" 엣지를 추가하면, 분기가 반복(루프)으로 이어진다** — 이게 조건부 엣지와 ReAct 루프의 연결고리

<br>

---

<br>

## 05. ReAct 패턴 수동 구현

**필요성**: `create_agent()`가 자동으로 해주는 걸 직접 만들어봐야, 그 함수의 파라미터가 내부적으로 뭘 조작하는지 보인다.

**역할 분담 3가지**:

| 구성 요소 | 역할 |
|---|---|
| `llm.bind_tools(tools)` | LLM에게 "이런 도구들이 있다"고 알려줌 (Day03에서 배운 것) |
| `call_model` (노드) | 대화 이력을 보고 **판단만** — 답변 또는 도구 호출 요청 생성 |
| `should_continue` (조건 함수) | `call_model`이 만든 마지막 메시지에 `tool_calls`가 있는지 보고 `"tools"`/`END` 결정 |
| `ToolNode(tools)` | LLM 대신 **실제로 도구(파이썬 함수)를 실행**하는 prebuilt 노드 |

```python
tools = [search, calculator]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: MessagesState) -> dict:
    response = llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [response]}

def should_continue(state: MessagesState) -> Literal["tools", END]:
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

tool_node = ToolNode(tools)

workflow = StateGraph(MessagesState)
workflow.add_node("call_model", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", should_continue)
workflow.add_edge("tools", "call_model")   # ← 루프의 핵심

react_agent = workflow.compile()
```

**주의**: `should_continue`은 `add_node()`로 등록된 적이 없어서 **그래프 시각화(`draw_mermaid`)에 박스로 안 보인다** — `call_model`에서 나가는 점선 분기 화살표로만 흔적이 남는다. 노드로 등록된 것(`call_model`, `tools`)만 박스로 그려진다.

`ToolNode`가 없다면 "도구 이름 찾기 → 실행 → `ToolMessage`로 포장"을 직접 반복문으로 짜야 하는데, 그 과정을 미리 만들어둔 것이 `ToolNode`다. LLM은 절대 실행하지 않고, 실행은 항상 `ToolNode`(또는 우리가 짠 코드) 몫이라는 원칙은 변하지 않는다.

<br>

---

<br>

## 06. `create_agent()` vs 수동 LangGraph

**필요성**: 언제 자동화 함수를 쓰고 언제 직접 짜야 하는지 판단 기준이 필요하다.

```python
prebuilt_agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

print(react_agent.get_graph().draw_mermaid())     # 수동으로 만든 그래프
print(prebuilt_agent.get_graph().draw_mermaid())   # create_agent가 만든 그래프
```
두 결과가 노드 이름(`call_model` vs `model`)만 다르고 **구조적으로 동일** — `create_agent()`는 별개 기술이 아니라, 우리가 직접 짠 것과 같은 LangGraph 그래프를 내부에서 자동 조립해서 반환하는 함수일 뿐이다. 매번 다른 구조를 "판단해서" 만드는 게 아니라, 항상 같은 표준 ReAct 그래프(판단→필요시 실행→다시 판단→...→종료)를 고정된 코드로 찍어낸다.

만들어진 뒤에도 `.get_graph().draw_mermaid()`로 언제든 내부 구조를 확인할 수 있다.

| 상황 | 선택 |
|---|---|
| 표준 "질문→도구→답변" 패턴 | `create_agent()` (짧고 검증됨, 권장) |
| 도구 실행 전 사람 승인(Human-in-the-loop) | 수동 LangGraph |
| 도구 결과 평가 후 재검색/분기 (RAG 검증 등) | 수동 LangGraph |
| `messages` 외 커스텀 State (비용 추적 등) | 수동 LangGraph |
| 루프 횟수 제한, 특정 도구 강제 호출 등 흐름 제어 | 수동 LangGraph |

<br>

---

<br>

## 07. Agent 루프를 세밀하게 제어·관찰하는 도구들

**필요성**: 표준 ReAct 루프가 익숙해진 다음, 실무에서 필요해지는 심화 기능들 — 지금 당장 실습하지 않았더라도 존재를 알아두면 나중에 찾아 쓸 수 있다.

| 기능 | 핵심 개념 |
|---|---|
| **Middleware** | Agent 실행 중간에 끼어드는 훅(hook). `@wrap_model_call`(LLM 호출 전후), `@wrap_tool_call`(도구 실행 전후, 에러를 안전하게 처리), `@dynamic_prompt`(상황별 프롬프트 생성). Day01 데코레이터 패턴과 같은 원리 — 원래 함수를 감싸서 앞뒤에 로직 추가 |
| **Memory & State 관리** | `InMemorySaver`(Checkpointer)로 대화 상태를 저장·재개. 커스텀 State 필드로 `messages` 외 데이터(사용자 정보, 누적 비용 등)도 함께 추적 가능. 프로덕션에선 DB 기반 Checkpointer 사용 |
| **Structured Output** | Day03 Output Parser의 Agent 버전. 최종 답변을 자유 텍스트 대신 Pydantic 모델 형태로 강제 반환 (`ToolStrategy` vs `ProviderStrategy` 두 구현 방식) |
| **Streaming (그래프 단위)** | `chain.stream()`과 달리 **그래프의 각 노드 단위**로 중간 상태를 관찰. `updates` 모드(변경분만) / `values` 모드(전체 상태) 등 |

<br>

---

<br>

## 08. 흔한 실수 메모

- **State 필드 오타**: `TypedDict`에 선언한 필드 이름(예: `user_intent`)과 노드 함수가 실제로 `return`하는 키 이름이 정확히 일치해야 한다. 스키마에 없는 키로 반환하면 조용히 무시되고 `None`으로 남는다 — 에러가 안 나서 발견이 까다로운 버그
- **venv/커널 불일치**: 노트북이 실제로 쓰는 커널(venv)과 터미널에서 패키지를 설치한 환경이 다르면 설치가 반영 안 된다 — 가장 안전한 방법은 노트북 셀 안에서 `!pip install`로 설치하는 것
