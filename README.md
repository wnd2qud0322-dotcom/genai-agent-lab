# GenAI Agent Lab

생성형 AI의 원리와 대규모 언어모델(LLM)의 이해를 바탕으로, LangChain·LangGraph 기반 AI Agent를 직접 설계하고 구현하며 기록하는 저장소입니다.

## 배경

AI Agent 개발 실전 과정(Python 기초 → OpenAI SDK → LangChain/RAG → LangGraph/Single Agent → Multi-Agent) 수강 후, 진도를 스스로 복습하며 개념 정리와 실습 프로젝트를 병행하고 있습니다.

## 학습 로드맵

| Day | 주제 | 상태 |
|---|---|---|
| 01 | Python 기초 — 변수/제어문/함수/클래스/데코레이터/예외처리 | ✅ 완료 |
| 02 | OpenAI SDK 기반 AI 서비스 구현 — 프롬프트/컨텍스트 엔지니어링, 공공API 활용 | 🔄 진행 중 |
| 03 | LangChain & RAG — Tool Calling, Output Parser, LCEL, RAG 파이프라인 | ⬜ 예정 |
| 04 | LangGraph & Single Agent — StateGraph, ReAct 패턴, CRAG/HyDE | ⬜ 예정 |
| 05 | LangSmith & Multi-Agent — Orchestrator-Worker, 최종 프로젝트 | ⬜ 예정 |

## 기술 스택

`Python` · `OpenAI SDK` · `LangChain` · `LangGraph` · `LangSmith` · `Streamlit` · `Chroma / FAISS`

## 폴더 구조

```
├── README.md
├── notes/            # Day별 학습 개념 정리 ("왜 AI Agent 개발에 필요한가" 관점)
│   ├── Day01_학습정리.md
│   └── ...
└── projects/         # 직접 설계·구현한 AI Agent 프로젝트
    └── ...
```

- **notes/**: 강의에서 배운 개념을 그대로 옮기는 대신, Python/LLM 개념이 실제 Agent 개발(도구 설계, State 관리, RAG, Multi-Agent 등)과 어떻게 연결되는지를 정리합니다.
- **projects/**: 실습을 응용해 직접 설계·구현한 프로젝트를 담습니다. 각 프로젝트 폴더에는 별도 README로 목적·구조·실행 방법을 기록합니다.

## 진행 기록

학습 개념 정리는 `notes/`, 직접 구현한 프로젝트는 `projects/` 폴더에서 확인할 수 있습니다.
