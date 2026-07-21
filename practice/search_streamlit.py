import streamlit as st
from search_places import(
    extract_search_terms,
    search_kakao_places,
    make_context,
    answer_user_question
)


def make_place_rows(places):
    rows = []

    for i, p in enumerate(places, 1):
        rows.append({
            "순번": i,
            "장소명": p.get("place_name", ""),
            "주소": p.get("address_name", ""),
            "카테고리": p.get("category_name", ""),
            "전화": p.get("phone", ""),
            "URL": p.get("place_url", "")
        })

    return rows


def main():
    st.set_page_config(page_title="카카오 장소 추천", page_icon="🔎")

    st.title("🔎 카카오 장소 추천 with ChatGPT")

    question = st.text_area(
        "질문을 입력하세요",
        value="성수에 있는 레스토랑을 두세개 추천해줘.",
        height=100
    )

    result_count = st.slider(
        "검색 결과 개수",
        min_value=3,
        max_value=15,
        value=5,
        step=1
    )

    if st.button("검색 및 답변 생성"):
        if not question.strip():
            st.warning("질문을 입력해주세요.")
            return
        
        try:
            with st.spinner("질문에서 지역명과 키워드를 추출하는 중..."):
                terms = extract_search_terms(question)

            location = terms["location"]
            keyword = terms["keyword"]

            st.info(f"추출된 검색어: {location} {keyword}")

            with st.spinner("카카오 API로 장소를 검색하는 중..."):
                places = search_kakao_places(location, keyword, result_count)

            if not places:
                st.warning("검색 결과가 없습니다.")
                return
            
            st.subheader("📍 검색 결과")
            rows = make_place_rows(places)
            st.dataframe(rows, use_container_width=True)

            context = make_context(places)

            with st.spinner("ChatGPT가 답변을 생성하는 중..."):
                answer = answer_user_question(question, context)

            st.subheader("🤖 추천 답변")
            st.write(answer)

            with st.expander("사용된 검색 context 보기"):
                st.code(context, language="text")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
                            