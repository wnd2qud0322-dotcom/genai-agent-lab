
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 API 키와 모델명 불러오기
load_dotenv()

kakao_api_key = os.getenv("KAKAO_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_DEFAULT_MODEL")


# OpenAI 클라이언트 생성
client = OpenAI(api_key=openai_api_key)


# 사용자 질문에서 장소 검색에 필요한 지역명과 키워드 추출
def extract_search_terms(question):
    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": """
                다음 질문에서 장소 검색에 필요한 지역명과 키워드를 추출하라.
                반드시 JSON 형식으로만 답하라.
                형식:
                {
                 "location": "지역명",
                 "keyword": "장소 키워드"
                }"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0,
        max_output_tokens=300,
        top_p=1
    )

    return json.loads(response.output_text)


# 카카오 장소 검색 API로 실제 장소 목록 조회
def search_kakao_places(location, keyword, size=5):
    searching = f"{location} {keyword}"

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    # 카카오 REST API 키를 헤더에 포함
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }

    # 검색어와 검색 개수 설정
    params = {
        "query": searching,
        "size": size
    }

    # 카카오 API 요청
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()

    # 검색 결과 중 장소 목록만 반환
    data = resp.json()
    return data.get("documents", [])


# 검색된 장소 목록을 ChatGPT가 읽기 쉬운 텍스트로 변환
def make_context(places):
    return "\n".join(
        f"{i}) {p.get('place_name', '')}, "
        f"{p.get('address_name', '')}, "
        f"{p.get('category_name', '')}, "
        f"{p.get('place_url', '')}"
        for i, p in enumerate(places, 1)
    )


# 검색 결과를 근거로 사용자 질문에 대한 최종 답변 생성
def answer_user_question(question, context):
    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": """당신은 친절한 여행 가이드입니다.
                        아래 검색 결과를 참고하여 사용자의 질문에 답변하세요.
                        """
            },
            {
                "role": "user",
                "content": f"검색 결과:\n{context}\n\n질문: {question}"
            }
        ],
        temperature=0.9,
        max_output_tokens=1024,
        top_p=1
    )

    return response.output_text
