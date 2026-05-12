import os
from dotenv import load_dotenv
import requests
import time
from openai import OpenAI

load_dotenv()

# ==========================================
# 🔑 1. API 키 및 설정 (여기를 채워주세요!)
# ==========================================
NOTION_TOKEN = os.environ.get("NOTION_TOKEN_ttb")
DATABASE_ID = os.environ.get("DATABASE_ID_ttb")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 노션 헤더 설정
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 🌟 찌꺼기 공백 방지 안전장치 적용!
client = OpenAI(api_key=OPENAI_API_KEY.strip())

# ==========================================
# 📥 2. 노션에서 '북마크'라고 임시 저장된 데이터 가져오기
# ==========================================
def get_unclassified_bookmarks():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # 유형이 '북마크'인 것만 쏙쏙 골라옵니다.
    payload = {
        "filter": {
            "property": "유형",
            "select": {
                "equals": "북마크"
            }
        },
        "page_size": 100 # 노션의 최대치입니다!
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print("❌ 노션 통신 에러:", response.text)
        return []
        
    return response.json().get('results', [])

# ==========================================
# 🧠 3. ChatGPT(gpt-4o-mini)에게 분류 맡기기
# ==========================================
def classify_text_with_openai(text):
    system_prompt = """
    너는 트위터 북마크를 분류해주는 똑똑한 AI 비서야.
    사용자가 트윗 본문을 주면, 내용을 읽고 반드시 아래의 [카테고리 목록] 중 딱 하나의 단어만 정확하게 골라서 대답해.
    설명이나 마침표는 절대 쓰지 마.
    
    [카테고리 목록]
    - 공부
    - 만화 애니
    - 서브컬쳐
    - 유머
    - 밈
    - 요리
    - 생활 꿀팁
    - IT
    - 정보
    - 기타
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 🌟 빠르고 저렴한 최고 가성비 모델!
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"이 트윗을 분류해줘: {text}"}
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI 에러 발생: {e}")
        return "기타"

# ==========================================
# 📝 4. 분류 결과를 노션에 업데이트하기
# ==========================================
def update_notion_category(page_id, category_name):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    payload = {
        "properties": {
            "유형": {
                "select": {"name": category_name}
            }
        }
    }
    
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ 업데이트 성공 ➔ [{category_name}]")
    else:
        print(f"❌ 업데이트 실패: {response.text}")

# ==========================================
# 🚀 메인 실행 로직
# ==========================================
print("데이터를 가져오는 중입니다...")
bookmarks = get_unclassified_bookmarks()

if not bookmarks:
    print("🎉 분류할 '북마크' 태그가 없거나 모두 완료되었습니다!")
else:
    print(f"총 {len(bookmarks)}개의 북마크 분류를 시작합니다. (자본주의의 속도! 🚀)\n")

    for idx, page in enumerate(bookmarks, 1):
        page_id = page['id']
        
        try:
            text = page['properties']['본문']['title'][0]['text']['content']
        except (KeyError, IndexError):
            text = "텍스트 없음"
            
        preview_text = text[:30].replace('\n', ' ') + "..." if len(text) > 30 else text
        print(f"[{idx}/{len(bookmarks)}] 트윗 확인: {preview_text}")
        
        ai_category = classify_text_with_openai(text)
        update_notion_category(page_id, ai_category)
        
        # 🌟 노션 API 자체 제한(1초에 3번)을 피하기 위한 최소한의 휴식 (0.5초)
        time.sleep(0.5) 

    print("\n🏁 모든 작업이 완료되었습니다!")
