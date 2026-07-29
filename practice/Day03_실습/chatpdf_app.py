# chatpdf_app.py
# 실행: streamlit run chatpdf_app.py

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# ─── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="ChatPDF",
    page_icon="📄",
    layout="wide",  # 넓은 레이아웃: 사이드바 + 메인 영역
)
st.title("📄 ChatPDF")
st.caption("PDF 파일을 업로드하고 내용에 대해 자유롭게 질문하세요.")

# ─── PDF 처리 함수 (캐시: 성능 최적화) ─────────────────────────
@st.cache_resource(show_spinner="PDF를 분석하는 중...")
def process_pdf(file_bytes: bytes, filename: str):
    """
    업로드된 PDF를 처리해서 RAG를 위한 벡터 스토어를 반환합니다.

    @st.cache_resource: 
      - 같은 파일을 다시 업로드하면 재처리하지 않음
      - 성능 향상: PDF 분석은 시간이 걸리므로 캐싱이 필수
    """
    # 임시 파일로 저장 (Streamlit에 업로드된 파일은 메모리에만 있음)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    # Step 1. PDF 로드
    pages = PyPDFLoader(tmp_path).load()

    # Step 2. 청킹 (텍스트 분할)
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50
    ).split_documents(pages)

    # Step 3. 임베딩 & 벡터 DB
    persist_dir = tempfile.mkdtemp()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=persist_dir,
    )

    # 임시 파일 삭제
    os.unlink(tmp_path)

    return vectorstore, len(pages), len(chunks)

def build_chain(vectorstore):
    """
    벡터 스토어로부터 RAG + 멀티턴 체인을 구성합니다.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    # streaming=True: 글자가 하나씩 나오는 효과
    llm = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0,
        streaming=True
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 PDF 문서 전문 분석가입니다.\n"
         "아래 제공된 PDF 문서 내용을 바탕으로만 질문에 정확하게 답하세요.\n"
         "문서에 없는 내용은 '이 문서에서 확인되지 않는 내용입니다'라고 명확히 답하세요.\n\n"
         "[PDF 문서 내용]\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ])

    def format_docs(docs):
        return "\n\n".join(
            f"[페이지 {doc.metadata.get('page', '?')+1}] {doc.page_content}"
            for doc in docs
        )

    return (
        {
            "context": (lambda x: x["question"]) | retriever | format_docs,
            "question": lambda x: x["question"],
            "chat_history": lambda x: x.get("chat_history", []),
        }
        | prompt | llm | StrOutputParser()
    )

# ─── 사이드바: PDF 업로드 ──────────────────────────────────────
with st.sidebar:
    st.header("📁 PDF 업로드")
    uploaded = st.file_uploader("PDF 파일을 선택해주세요", type="pdf")

    if uploaded:
        vectorstore, n_pages, n_chunks = process_pdf(
            uploaded.read(), uploaded.name
        )
        st.success(f"✅ PDF 분석 완료!")
        st.info(f"📊 {n_pages}페이지 → {n_chunks}개 청크로 분할됨")

        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    else:
        st.warning("⚠️ 좌측의 파일 업로더에서 PDF를 선택해주세요.")

# ─── 대화 히스토리 초기화 ──────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── 대화 표시 (이전 대화 내역) ────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ─── 사용자 입력 처리 ──────────────────────────────────────────
if user_input := st.chat_input("PDF 내용에 대해 질문하세요..."):
    if not uploaded:
        st.warning("⚠️ 먼저 PDF를 업로드해주세요.")
        st.stop()

    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # LangChain 메시지 형식으로 변환 (이전 대화 기록)
    lc_history = []
    for m in st.session_state.messages[:-1]:  # 현재 질문 제외
        if m["role"] == "user":
            lc_history.append(HumanMessage(content=m["content"]))
        else:
            lc_history.append(AIMessage(content=m["content"]))

    # AI 응답 생성 (스트리밍)
    chain = build_chain(vectorstore)
    with st.chat_message("assistant"):
        # st.write_stream: 응답을 스트리밍으로 표시
        # 글자가 하나씩 나타나는 효과
        response = st.write_stream(
            chain.stream({
                "question": user_input,
                "chat_history": lc_history
            })
        )

    # 대화 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": response})