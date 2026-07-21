# Day 01 — 파이썬 프로그래밍

## 01. 변수와 자료형

**필요성**: LangChain의 `@tool` 데코레이터는 함수의 type hint와 docstring을 읽어서 LLM에게 전달할 JSON Schema를 자동으로 생성한다. 즉, 타입과 설명을 정확히 써두지 않으면 LLM이 도구를 엉뚱한 형식으로 호출하게 되므로, type hint는 도구 설계의 가장 기초가 된다.

<br>

- **type hint**: 변수·함수의 매개변수/반환값에 어떤 자료형을 기대하는지 표시하는 문법
  - `city: str = "부산"`
  - `def get_weather_with_hint(city: str) -> str:`
- **f-string**: 변수를 문자열에 바로 삽입
  - `print(f"{city}의 기온은 {temperature:.1f}도 입니다")`
  - `return f"[도구: {tool_name}] 결과 -> {result}"`

<br>

---

<br>

## 02. 조건문과 반복문

**필요성**: 모든 AI Agent는 결국 "할 일이 남았는가?"를 반복해서 확인하는 반복문으로 동작한다. ReAct 패턴(추론→행동→관찰)도, LangGraph의 그래프 실행도 결국은 조건문과 반복문으로 만들어진 Loop 구조일 뿐이라서, if/while/for를 다루는 감각이 곧 Agent Loop를 이해하는 감각이 된다.

<br>

- `if~else` : 어떤 도구(tool)를 선택할지 판단
- `while` : ReAct(Reasoning + Acting) — 답이 나올 때까지 Loop 반복
- `for` + (`break`/`continue`) : 여러 도구를 순회하면서, 실패는 건너뛰기
- 재시도 로직 : `try`로 최대 재시도 횟수만큼 반복

<br>

---

<br>

## 03. 리스트·딕셔너리·집합과 JSON

**필요성**: LangChain과 LangGraph에서 주고받는 메시지, 도구 호출 인자, 도구 실행 결과는 전부 `dict` 형태로 표현된다. 다시 말해 Agent가 LLM과 대화하는 형식 자체가 "dict를 담은 list"이기 때문에, 이 자료형들을 모르면 Agent 내부에서 오가는 데이터를 전혀 읽을 수 없다.

<br>

| 자료형 | 특징 |
|---|---|
| `list [ ]` | 순서 있음, 중복 가능, 추가 가능 |
| `tuple ( )` | 순서 있음, 중복 가능 → **unpacking** = tuple 값들을 여러 변수에 한 번에 나눠 담는 문법 |
| `dict { }` | key : value 형태 — ex) `student.get("동아리", "없음")` → 없는 key도 안전하게 처리 가능 |
| `set { }` | 순서 없음, 중복 불가 |

**dict ↔ JSON 변환**
- `json.dumps(dict)` : dict → JSON 변환 — Agent에게 보낼 때
- `json.loads(문자열)` : JSON 문자열 → dict — Agent에게서 받을 때
- LLM API가 결국 JSON 형태로 요청/응답을 주고받는다.

<br>

---

<br>

> ### AI Agent의 3계층
> 1) **Prompt engineering** — 모델에게 "~을 해라" 지시하는 계층
>    - System prompt : 역할·페르소나 정의
>    - Few-shot 예시 : 원하는 형식·스타일 정의
>    - Chain-of-thought : 단계별 추론 유도
>    - 원하는 형식 명시 : JSON·표 형식 명시
> 2) **Context engineering** — 모델에게 "~을 보여주기" (RAG)
> 3) **Harness engineering** — 모델 호출을 감싸는 인프라를 설계하는 계층

<br>

---

<br>

## 04. 함수와 클래스

**필요성**: LangChain의 도구(tool)는 결국 함수로 정의되고, Agent의 메모리와 state는 결국 클래스로 정의된다. 함수가 "동작"을 담당한다면 클래스는 "데이터와 동작을 함께" 담는 그릇이라서, 이 차이를 이해해야 프레임워크 코드가 낯설지 않다.

<br>

**함수**
1) `*args` : 남은 위치 인자를 tuple로 받음 / `**kwargs` : 남은 키워드 인자를 dict로 받음
   - `def search(query: str, top_k: int = 3) -> str:`
   - `def call_tool(name: str, *args, **kwargs):`
2) docstring과 type hint = 도구 설명서
   - docstring → LLM에게 "이 도구가 뭘 하는지" 전달
   - ★ docstring을 잘 쓰는 건 prompt engineering

**클래스** = 데이터와 동작을 하나로 묶는다.
1) 단일 구조 : `class Agent: def 동작정의1(): / def 동작정의2():`
2) 복합 구조(상속) :
   ```python
   class BaseAgent:
       def __init__(self): ...
       def run(self): ...

   class WeatherAgent(BaseAgent):
       def run(self): ...

   class MathAgent(BaseAgent):
       def run(self): ...
   ```

<br>

---

<br>

## 05. 데코레이터와 모듈

**필요성**: LangChain에서 `@tool`은 평범한 함수를 감싸서 "LLM이 호출할 수 있는 도구"로 바꿔주고, `@dataclass`는 평범한 클래스를 감싸서 "state 정의"로 바꿔준다. 이렇게 데코레이터로 기능이 덧붙여진 함수와 클래스는, 실전 프로젝트에서는 `tools.py`, `state.py`처럼 역할별 모듈 파일로 나눠 관리하기 때문에 데코레이터와 모듈 개념을 같이 알아야 실제 프로젝트 구조가 이해된다.

<br>

**decorator의 기본 구조**
```python
def decorator(func):              # ← 포장지
    def wrapper(*args, **kwargs):     # ← 함수에 기능 확장
        # 추가 기능
        return func(*args, **kwargs)
    return wrapper                 # ← 새 함수 반환
```

> **[Python 개념이 실제 AI Agent에 어떻게 적용되는지]**
> - 데코레이터 : 평범한 함수를 AI가 실행할 수 있는 도구로 바꿈
> - 모듈 : 도구는 `tools.py`, 상태는 `state.py`처럼 분리 관리
> - inspect 리플렉션 : 프레임워크가 사용 가능한 도구를 자동으로 찾아냄
> - orchestrator 패턴 : 날씨 관련 질의는 날씨 Agent, 계산 관련 질의는 계산 Agent에 전달

<br>

---

<br>

## 06. 예외처리와 파일입출력

**필요성**: 도구 호출은 네트워크 오류나 잘못된 입력 등으로 언제든 실패할 수 있는데, 예외처리를 해두지 않으면 그 실패 하나 때문에 Agent 전체가 멈춰버린다. `try/except`로 실패를 감싸줘야 Agent가 안정적으로 계속 동작한다.

<br>

- `try, except, finally` → 도구 실행 실패가 전체 Agent를 멈추지 않게 한다.
- 커스텀 예외 → Agent 전용 에러 타입으로 의미 있는 처리

<br>

---

<br>

## 07. Streamlit

Python 코드만으로 웹 화면을 만드는 framework다.

**형태**
```python
%%writefile mini_app.py
import streamlit as st

st.title("...")
user_input = st.text_input("...")
if user_input:
    st.write(f"...")
```
→ `mini_app.py`가 파일로 저장됨 → `streamlit run mini_app.py`
