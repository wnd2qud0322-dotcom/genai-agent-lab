# Day 03 — LangChain & RAG

OpenAI SDK를 직접 다루던 Day02에서 한 단계 올라와, LangChain으로 "프롬프트→LLM→후처리"를 표준화된 체인으로 구성하고, 마지막엔 LLM이 모르는 외부 문서를 검색해서 답하게 만드는 RAG까지 정리한 노트입니다.

<br>

---

<br>

## 01. LangChain 기초 — LCEL

**필요성**: OpenAI SDK를 직접 쓰면 "프롬프트 조립 → API 호출 → 응답 파싱"을 매번 손으로 짜야 한다. LangChain은 이 흐름을 `|`(파이프) 하나로 표준화해서, 프롬프트/모델/후처리를 자유롭게 갈아끼울 수 있는 조립식 구조로 만들어준다.

**LCEL(LangChain Expression Language) 기본 패턴**
```python
chain = prompt | llm | output_parser
response = chain.invoke({"topic": "..."})
```
- `prompt`: 입력을 완성된 지시문으로 변환
- `llm`: 그 지시문을 받아 답변 생성
- `output_parser`: 답변(AIMessage)에서 필요한 형태만 추출

**실행 방식 4종류** — 같은 체인, 호출법만 다름

| 메서드 | 용도 |
|---|---|
| `invoke()` | 입력 1개 → 결과 1개 |
| `stream()` | 결과를 토큰 단위로 실시간 출력 |
| `batch([...])` | 여러 입력을 한 번에 처리 |
| `ainvoke()` / `abatch()` | 비동기(`await`) 버전 |

<br>

---

<br>

## 02. RunnablePassthrough / RunnableParallel — RAG의 기초 구조

**필요성**: 체인 안에서 "이 값은 검색해서 가공하고, 저 값은 그대로 전달하고 싶다"는 요구가 항상 생긴다. 이 두 Runnable이 그 분기 처리를 담당하며, 이 구조 자체가 뒤에 나오는 RAG의 핵심 골격이다.

- **RunnablePassthrough**: 입력을 가공 없이 그대로 다음 단계에 전달
- **RunnableParallel**: 입력 하나를 받아 여러 갈래로 동시에 처리(검색은 검색대로, 원문은 원문대로)

```python
setup_and_retrieval = RunnableParallel(
    {
        "context": retriever,               # 질문으로 문서 검색
        "question": RunnablePassthrough()   # 질문은 그대로 통과
    }
)
chain = setup_and_retrieval | prompt | llm | output_parser
```

```
질문 입력
   ├─ context  ← retriever가 검색한 관련 문서
   └─ question ← 입력 그대로
   ↓
prompt에 {context}/{question} 채워짐 → llm → 답변
```

이 구조가 "LLM의 기본 지식 + 벡터DB에 저장된 새 문서"를 함께 참고해서 답하게 만드는 RAG의 뼈대다.

<br>

---

<br>

## 03. 멀티턴 대화 & 입력 다루기

**필요성**: LLM 호출 하나하나는 이전 대화를 기억하지 못한다(stateless). "그거", "아까 그거"같은 연속 질문을 이해시키려면, 이전 대화 기록을 매번 프롬프트에 다시 포함시켜줘야 한다.

- `ChatMessageHistory`로 대화 기록(`HumanMessage`/`AIMessage`)을 저장·누적
- `MessagesPlaceholder(variable_name="chat_history")`를 프롬프트 안에 끼워넣으면, 호출 시 이전 대화가 자동으로 그 자리에 채워짐
- 매 턴마다 `chat_history.append(...)`로 방금 주고받은 질문/답변을 계속 누적해야 다음 질문에서 맥락이 유지됨
- **주의**: `messages = []`처럼 중간에 기록을 초기화하면 그 이후 LLM은 이전 맥락을 완전히 잃는다

**InMemoryCache**: 같은 입력으로 다시 호출하면 API를 재호출하지 않고 캐시된 응답을 즉시 반환 — 세션 전체에 적용되는 전역 스위치(`set_llm_cache`)이지, 셀 단위로 켜고 끄는 게 아니다.

**비동기 처리(`async`/`await`)**: 질문 여러 개를 순서대로 하나씩 기다리지 않고, `ainvoke()`/`abatch()`로 한꺼번에 던져서 동시에 처리 — 전체 대기 시간이 크게 줄어든다.

**토큰 사용량 추적**: `get_openai_callback()`으로 감싸서 호출하면 그 안에서 실행된 요청들의 토큰 수·비용을 자동 집계해준다.
```python
from langchain_community.callbacks import get_openai_callback

with get_openai_callback() as cb:
    result = chain.invoke({...})
    print(cb.total_tokens, cb.total_cost)
```

<br>

---

<br>

## 04. Function / Tool Calling

**필요성**: 순수 LLM 호출은 실시간 정보·특정 도메인 데이터에서 신뢰할 수 없는 답(환각)을 만든다. Tool Calling은 "LLM은 어떤 도구가 필요한지 판단만 하고, 실제 실행은 우리 코드가 담당"하게 해서 진짜 데이터 기반으로 답하게 만든다.

```
① LLM: "get_weather(location='서울')가 필요하다" — 요청(텍스트)만 생성
② 코드: get_weather("서울") 실제 실행 — 진짜 데이터 획득
③ LLM: 실행 결과를 자연스러운 문장으로 정리
```

LangChain에서는 `@tool` 데코레이터가 함수의 docstring+타입힌트를 읽어 자동으로 도구 스펙(JSON Schema)을 만들고, `bind_tools()`로 LLM에 연결한다.

> 상세 내용(OpenAI SDK 방식 vs LangChain 방식 비교, 코드 전체)은 [Day03_02_Function&ToolCalling_정리.md](./Day03_02_Function%26ToolCalling_정리.md) 참고

<br>

---

<br>

## 05. Output Parser

**필요성**: LLM은 항상 자유형 텍스트로 답한다. 이후 코드에서 그 답을 안전하게 다루려면(리스트로 순회하거나, 특정 필드를 꺼내 쓰거나) 타입이 보장된 Python 객체로 변환하는 과정이 필요하다.

| 파서 | 역할 |
|---|---|
| `PydanticOutputParser` | Pydantic 모델(필드명·설명 정의)에 맞춰 구조화된 객체로 변환 |
| `CommaSeparatedListOutputParser` | 쉼표로 구분된 텍스트를 파이썬 리스트로 변환 |
| `JsonOutputParser(pydantic_object=Model)` | 지정한 필드명을 강제하는 JSON 파싱 |
| `JsonOutputParser()` (스키마 없음) | 필드명은 LLM이 자유롭게 정함, 형식만 JSON 보장 |
| Custom(`BaseOutputParser` 상속) | `.parse(self, text)` 메서드 하나만 구현하면 직접 파서 제작 가능 |

**작동 원리**: `parser.get_format_instructions()`가 "이런 형식으로 답하라"는 지시문을 자동 생성 → `prompt.partial(format_instructions=...)`로 프롬프트에 삽입 → LLM이 그 형식대로 답변 → 파서가 파싱.

```python
class CommaSeparatedListOutputParser(BaseOutputParser):
    def parse(self, text: str) -> list:
        return [item.strip() for item in text.strip().split(",")]
```
직접 만든 파서도 `prompt | llm | parser` 체인에 똑같이 끼워 쓸 수 있다 — 결국 파서는 "텍스트를 받아 원하는 형태로 가공해 돌려주는 함수" 하나일 뿐이다.

<br>

---

<br>

## 06. RAG (Retrieval-Augmented Generation)

**필요성**: LLM은 학습 시점 이후의 정보나 회사 내부 문서를 전혀 모른다. 매번 파인튜닝하는 대신, 질문할 때마다 관련 문서를 검색해서 옆에 쥐어주는 방식으로 최신·전문 지식에 답하게 만드는 기법이다.

```
[사전 준비 — 한 번만]
문서 → 청킹(chunk) → 임베딩(벡터화) → 벡터DB에 저장

[질문마다 반복]
질문 → 임베딩 → 벡터DB에서 유사 청크 검색(retriever)
     → 검색된 문서(context) + 질문 → 프롬프트
     → LLM이 "이 문서에 근거해서만 답하라"는 지시와 함께 답변 생성
```

### 핵심 용어

| 용어 | 의미 |
|---|---|
| 청킹(Chunking) | 문서를 작은 조각으로 자르는 것. 검색 정확도(주제 혼재 방지)와 LLM 입력 크기 제한 때문에 필요 |
| 임베딩(Embedding) | 텍스트 → 의미를 담은 숫자 벡터로 변환. 의미가 비슷하면 벡터도 가까워짐 |
| 벡터DB | 임베딩을 저장하고 "질문과 가까운 벡터"를 빠르게 찾아주는 저장소(Chroma, FAISS 등) |
| Retriever | 벡터DB에서 검색 기능만 뽑아낸 인터페이스. `.invoke(질문)` → 관련 청크 리스트 반환 |

### 문서 로더 종류

| 로더 | 용도 |
|---|---|
| `TextLoader` | 일반 텍스트(.txt) 파일 |
| `DirectoryLoader` | 폴더 안 여러 파일을 `glob` 패턴으로 한 번에 로드 (`*.txt` 등) |
| `PyPDFLoader` | 일반적인 텍스트 기반 PDF |
| `PDFPlumberLoader` | 표·레이아웃 보존이 필요한 PDF |
| `UnstructuredPDFLoader` | 스캔 이미지·복잡한 포맷의 PDF (OCR 필요) |
| `WebBaseLoader` | 웹페이지 URL |

### 청킹(Splitter) 방식 비교

| Splitter | 특징 |
|---|---|
| `RecursiveCharacterTextSplitter` | 여러 구분자(`\n\n`→`\n`→공백 순)를 차례로 시도해 의미 단위를 최대한 보존 — 실무 기본값 |
| `CharacterTextSplitter` | 구분자 하나로만 단순 분할 (기본값 `\n\n`) |
| `TokenTextSplitter` | 글자 수가 아니라 토큰 수 기준으로 분할 |

### 검색 방식 비교

| 방식 | 기준 | 특징 |
|---|---|---|
| `similarity_search` | 유사도 순위만 | 빠르고 정확하지만 비슷한 내용이 중복 선택될 수 있음 |
| `MMR`(max_marginal_relevance) | 유사도 + 다양성 | `fetch_k`개 후보를 유사도로 먼저 뽑고, 그중 `k`개를 중복 없이 다양하게 최종 선택 |
| `MultiQueryRetriever` | 질문을 LLM이 여러 형태로 변형해 동시 검색 | 표현이 달라 놓치던 문서까지 폭넓게 포착 |
| 하이브리드 검색 | 벡터 검색 + BM25(키워드) | 의미 기반 검색과 정확한 단어 매칭을 `EnsembleRetriever`로 결합, `weights`로 비율 조절 |

### 파이프라인 요약

```
문서 파일
  ↓ TextLoader / PyPDFLoader / WebBaseLoader
Document 리스트
  ↓ RecursiveCharacterTextSplitter
청크(Chunk) 리스트
  ↓ OpenAIEmbeddings
벡터
  ↓ Chroma.from_documents()
벡터 DB (로컬 저장)
  ↓ .as_retriever()
Retriever
  ↓ LCEL 체인 {context: retriever|format_docs, question: ...} | prompt | llm | parser
답변
```

### RAG 출처 표시

**필요성**: 답변만 보여주면 실제로 문서에 근거한 답인지 확인할 방법이 없다. 어떤 청크를 참고했는지 함께 보여주면 신뢰성을 검증할 수 있다.

```python
rag_chain_with_source = RunnableParallel(
    context=retriever,
    question=RunnablePassthrough()
).assign(
    answer=(lambda x: {"context": format_docs(x["context"]), "question": x["question"]})
           | prompt | llm | StrOutputParser()
)
```
`.assign()`으로 기존 딕셔너리(`context`, `question`)에 `answer` 필드를 추가 — 결과에 답변과 참고 문서가 함께 담겨 반환된다.

### 한계

- 검색이 틀리면(관련 없는 청크를 찾으면) 답도 틀린다 — **검색 품질이 곧 답변 품질**
- LLM이 context를 요약하며 왜곡할 가능성은 여전히 남는다
- 프롬프트에 "문서에 없으면 모른다고 답하라" 제약을 넣는 것이 필수 (Day02의 R-T-C-F 중 Constraints)
