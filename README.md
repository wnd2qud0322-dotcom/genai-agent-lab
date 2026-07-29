# GenAI Agent Lab

생성형 AI의 원리와 대규모 언어모델(LLM)의 이해를 바탕으로, LangChain·LangGraph 기반 AI Agent를 직접 설계하고 구현하며 기록하는 저장소입니다.

## 배경

AI Agent 개발 실전 과정(Python 기초 → OpenAI SDK → LangChain/RAG → LangGraph/Single Agent → Multi-Agent) 수강 후, 진도를 스스로 복습하며 개념 정리와 실습 프로젝트를 병행하고 있습니다.

## 학습 로드맵

| Day | 주제 | 상태 |
|---|---|---|
| 01 | Python 기초 — 변수/제어문/함수/클래스/데코레이터/예외처리 | ✅ 완료 |
| 02 | OpenAI SDK 기반 AI 서비스 구현 — 프롬프트/컨텍스트 엔지니어링, 공공API 활용 | ✅ 완료 |
| 03 | LangChain & RAG — Tool Calling, Output Parser, LCEL, RAG 파이프라인 | 🔄 진행 중 |
| 04 | LangGraph & Single Agent — StateGraph, ReAct 패턴, CRAG/HyDE | ⬜ 예정 |
| 05 | LangSmith & Multi-Agent — Orchestrator-Worker, 최종 프로젝트 | ⬜ 예정 |

## 기술 스택

`Python` · `OpenAI SDK` · `LangChain` · `LangGraph` · `LangSmith` · `Streamlit` · `Chroma / FAISS`

## 폴더 구조

```
├── README.md
├── notes/            # Day별 학습 개념 정리 ("왜 AI Agent 개발에 필요한가" 관점)
│   ├── Day01_학습정리.md
│   ├── Day02_학습정리.md
│   └── ...
├── practice/         # 강의를 따라가며 직접 코드를 연습해보는 공간
│   └── ...
└── projects/         # 직접 설계·구현한 AI Agent 프로젝트
    └── ...
```

- **notes/**: 강의에서 배운 개념을 그대로 옮기는 대신, Python/LLM 개념이 실제 Agent 개발(도구 설계, State 관리, RAG, Multi-Agent 등)과 어떻게 연결되는지를 정리합니다.
- **practice/**: 노트에 정리한 개념을 바탕으로 직접 코드를 쳐보며 연습하는 공간입니다. Day별 폴더로 구분합니다.
- **projects/**: 연습한 내용을 응용해 직접 설계·구현한 완성된 프로젝트를 담습니다. 각 프로젝트 폴더에는 별도 README로 목적·구조·실행 방법을 기록합니다.

## 진행 기록

학습 개념 정리는 `notes/`, 코드 연습은 `practice/`, 직접 구현한 프로젝트는 `projects/` 폴더에서 확인할 수 있습니다.

## 업데이트 규칙

- **항상 로컬에서만 수정합니다.** GitHub 웹 에디터로 직접 파일을 고치지 않습니다 (로컬과 원격이 어긋나 충돌이 생기는 걸 방지하기 위함).
- 수정 후에는 아래 순서로 반영합니다:

```
git add .
git commit -m "커밋 메시지"
git push
```

- 만약 `push`가 거부되면(`rejected`), 아래 순서로 해결합니다:

```
git pull
git push
```
