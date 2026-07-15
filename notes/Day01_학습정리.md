# Day 01. Python 기초 — 이게 AI Agent 개발에 왜 필요한가

Python 문법 자체보다 **"이 개념이 나중에 LangChain/LangGraph의 어떤 부분이 되는지"**를 중심으로 정리한 복습 노트입니다.

---

## 1차시. 변수와 자료형 / 타입 힌트

**핵심 개념**: 파이썬은 동적 타이핑이라 변수 타입을 선언하지 않아도 되지만, `city: str`처럼 타입 힌트를 붙일 수 있다.

**AI Agent와의 연결**
- LangChain의 `@tool` 데코레이터는 함수의 **타입 힌트를 읽어서 LLM에게 전달할 JSON Schema를 자동 생성**한다.
- 타입 힌트가 없으면 LLM이 도구에 잘못된 타입의 인자를 넣을 위험이 커진다 (예: 숫자 대신 문자열을 넣어 `TypeError` 발생).

**왜 필요한가**: 도구 함수의 안정성은 결국 "타입을 정확히 선언했는가"에서 시작된다.

---

## 2차시. 조건문과 반복문

**핵심 개념**: `if/elif/else`로 분기, `while`/`for`로 반복, `break`/`continue`로 흐름 제어.

**AI Agent와의 연결**
- **`while` 루프 = Agent의 핵심 동작 원리 그 자체.** ReAct 패턴(추론→행동→관찰을 반복)과 LangGraph의 그래프 실행 모두 "종료 조건(FINISH/END)에 도달할 때까지 반복"하는 구조다.
- `if/elif`는 "어떤 도구를 호출할지" 판단하는 로직의 단순화 버전 (실제로는 LLM이 이 판단을 수행).
- `max_steps` 같은 안전장치는 실제 프레임워크의 `ModelCallLimitMiddleware`와 동일한 역할 — 무한 루프로 인한 API 비용 폭증을 막는다.
- `try/except` + `while`을 결합한 재시도(Retry) 로직은 `ToolRetryMiddleware`가 내부적으로 하는 일과 같다.

**왜 필요한가**: Agent를 "안정적으로 멈출 줄 아는 존재"로 만드는 게 바로 이 반복/조건 제어다.

**부록 — AI 서비스 개발의 3계층** (이 강의 전체를 관통하는 개념)
| 계층 | 하는 일 | 배우는 시점 |
|---|---|---|
| 프롬프트 엔지니어링 | 모델에게 "무엇을 하라" 지시 | Day02 |
| 컨텍스트 엔지니어링 | 모델에게 "무엇을 보여줄지" 설계 (RAG 등) | Day03~04 |
| 하네스 엔지니어링 | 모델 호출을 감싸는 인프라 (루프, 재시도, 메모리) | Day04~05 — 오늘 배운 if/while이 이 계층의 뼈대 |

---

## 3차시. 리스트·딕셔너리·집합·JSON

**핵심 개념**: list(순서 있음)/dict(key-value)/set(중복 제거)/tuple(수정 불가+언패킹), 그리고 `json.dumps`/`json.loads`.

**AI Agent와의 연결**
- **LangChain/LangGraph에서 오가는 모든 데이터는 결국 "dict를 담은 list"다.** `agent.invoke({"messages": [{"role": "user", "content": "..."}]})` 형태가 그 실체.
- LLM의 도구 호출 응답(`tool_calls`)은 dict 안에 dict가 들어있는 중첩 구조 (`{"name": ..., "args": {"city": "서울"}}`).
- **LLM API는 실제로는 JSON 문자열로 통신**한다. `json.dumps()`(보낼 때)/`json.loads()`(받을 때)가 dict ↔ 문자열 변환의 핵심.
- tuple 언패킹(`kind, content = plan[step]`)은 2차시 Agent Loop에서 이미 사용한 패턴이고, LangChain의 `("user", "...")` 메시지 축약 문법과도 동일한 원리.

**왜 필요한가**: 이 자료형들을 모르면 LLM 응답 구조를 읽거나 도구 호출 인자를 다루는 코드 자체를 이해할 수 없다.

---

## 4차시. 함수와 클래스

**핵심 개념**: 함수(기본값, `*args`/`**kwargs`), docstring, 클래스(`__init__`, 속성/메서드), 상속.

**AI Agent와의 연결**
- **LangChain의 도구(tool)는 결국 함수이고, Agent의 메모리·State는 결국 클래스다.**
- docstring은 LLM에게 "이 도구가 언제, 왜 필요한지" 알려주는 설명서 역할 — **docstring을 잘 쓰는 것 자체가 프롬프트 엔지니어링의 일부**.
- 클래스로 만든 `ConversationMemory` 같은 구조가 "최근 N개 메시지만 유지"하는 슬라이딩 윈도우 방식의 메모리 관리 기본 원리.
- 상속(`BaseAgent` → `WeatherAgent`, `MathAgent`)은 여러 전문 Agent를 구조화하는 방법 — **Day05 Multi-Agent의 Orchestrator-Worker 패턴의 뼈대**가 여기서 이미 만들어진다.

**왜 필요한가**: "함수 = 도구", "클래스 = 상태/메모리/Agent 객체"라는 대응관계를 알면 이후 프레임워크 코드가 낯설지 않다.

---

## 5차시. 데코레이터와 모듈

**핵심 개념**: 데코레이터(함수를 감싸 기능 추가), `@dataclass`(클래스용 데코레이터), 모듈(`.py` 파일 = import 가능한 코드 묶음).

**AI Agent와의 연결**
- **`@tool`의 정체가 바로 데코레이터.** 평범한 함수를 감싸서 "LLM이 호출 가능한 도구"로 등록하는 역할을 한다.
- **`@dataclass`는 LangGraph의 State 정의 표준 방식.** 속성만 선언하면 `__init__`을 자동 생성해준다.
- 도구는 `tools.py`, 상태는 `state.py`처럼 **역할별로 모듈을 나누는 것**이 실전 프로젝트의 기본 구조.
- `inspect.getmembers()`로 모듈 안 함수/클래스를 자동 탐색하는 방식은 프레임워크가 도구를 자동 등록하는 원리와 같다.

**왜 필요한가**: "포장지(데코레이터)로 기능을 덧씌운다"는 개념 하나로 `@tool`, `@dataclass` 등 프레임워크의 각종 `@` 문법을 다 이해할 수 있다.

---

## 6차시. 예외 처리와 파일 입출력

**핵심 개념**: `try/except/finally`, 커스텀 예외(`class MyError(Exception)`), `with open(...)`으로 파일 읽기/쓰기.

**AI Agent와의 연결**
- 도구 호출은 네트워크 오류, 잘못된 입력 등으로 **언제든 실패할 수 있다.** `try/except` 없이는 실패 하나가 Agent 전체를 멈춰 세운다.
- 커스텀 예외(`ToolExecutionError`)로 "이건 우리 도구 실행 에러"라고 구분해서 처리할 수 있다.
- 파일 입출력은 **Manus AI 방식**의 핵심 — 긴 작업의 진행 상황을 `todo.md` 같은 파일에 기록해두면, 매번 AI의 컨텍스트(기억)에 다 담아두지 않아도 돼서 부담이 줄어든다.
- try/except + 파일 로깅을 합친 "안전한 실행기"는 `ToolRetryMiddleware`, `LangSmith Tracing`(실행 기록 추적)의 단순화 버전.

**왜 필요한가**: 실패해도 안 죽고, 기록을 남기는 것 — 이 두 가지가 "안정적인 Agent"의 최소 조건이다.

---

## 한 장 요약

| Python 개념 | Agent 세계에서의 정체 |
|---|---|
| 변수/타입 힌트 | 도구 함수 인자의 타입 스펙 (`@tool`의 JSON Schema 근거) |
| 조건문/반복문 | Agent Loop(ReAct, LangGraph 그래프 실행) 그 자체 |
| list/dict/JSON | LLM과 주고받는 메시지·도구 호출의 실제 데이터 형태 |
| 함수 | 도구(tool) |
| 클래스 | 메모리/State/Agent 객체 |
| 상속 | 여러 전문 Agent(Worker) 구조화 |
| 데코레이터 | `@tool`, `@dataclass`의 원리 |
| 모듈 | `tools.py`/`state.py`로 역할별 코드 분리 |
| 예외처리 | 도구 실패에도 Agent가 멈추지 않게 하는 안전장치 |
| 파일 입출력 | 작업 기록/State를 파일로 저장 (Manus AI 방식) |
