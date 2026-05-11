import os
from dotenv import load_dotenv
# .env 파일 안의 비밀번호들을 불러옴
load_dotenv()
import requests
import json
import time
import google.generativeai as genai

# ==========================================
# 🔑 1. API 키 및 설정 (여기를 채워주세요!)
# ==========================================
NOTION_TOKEN = os.environ.get("NOTION_TOKEN_ttb")
DATABASE_ID = os.environ.get("DATABASE_ID_ttb")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 노션 헤더 설정
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 제미나이 설정
genai.configure(api_key=GEMINI_API_KEY.strip()) # 🌟 공백 방지 안전장치 추가!
model = genai.GenerativeModel('gemini-2.5-flash') # 🌟 확인하신 최신 모델 이름으로 변경!

# ==========================================
# 📥 2. 노션에서 '분류 안 된' 북마크 가져오기
# ==========================================
def get_unclassified_bookmarks():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    

    payload = {
        "filter": {
            "property": "유형",
            "select": {
                "equals": "북마크"  # 🌟 "유형이 '북마크'라고 되어있는 애들만 싹 다 데려와!" 로 변경
            }
        },
         "page_size": 100
       }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print("❌ 노션에서 데이터를 가져오는 중 에러 발생:", response.text)
        return []
        
    return response.json().get('results', [])

# ==========================================
# 🧠 3. 제미나이 AI에게 분류 맡기기
# ==========================================
def classify_text_with_gemini(text):
    prompt = f"""
    너는 트위터 북마크를 분류해주는 똑똑한 AI 비서야.
    아래 [트윗 본문]을 읽고 반드시 아래의 [카테고리 목록] 중 딱 하나의 단어만 정확하게 골라서 대답해. 
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

    [트윗 본문]
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        # AI가 대답한 텍스트 앞뒤 공백을 자르고 반환
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ 제미나이 에러 발생: {e}")
        return "기타" # 에러가 나면 안전하게 '기타'로 분류

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
# 🚀 메인 실행 로직 (여기서부터 프로그램 시작)
# ==========================================
print("데이터를 가져오는 중입니다...")
bookmarks = get_unclassified_bookmarks()

if not bookmarks:
    print("🎉 분류할 북마크가 없거나 모두 완료되었습니다!")
else:
    print(f"총 {len(bookmarks)}개의 북마크 분류를 시작합니다.\n")

    for idx, page in enumerate(bookmarks, 1):
        page_id = page['id']
        
        # 1. 노션 데이터에서 본문 텍스트 추출 (속성 이름이 다르면 수정 필요)
        try:
            # 트윗 내용이 들어있는 속성 이름이 '이름' 또는 '본문'인지 확인하세요.
            text = page['properties']['본문']['title'][0]['text']['content']
        except (KeyError, IndexError):
            text = "텍스트 없음"
            
        # 본문이 너무 길면 화면에 다 출력하지 않고 앞부분만 잘라서 보여줌
        preview_text = text[:30].replace('\n', ' ') + "..." if len(text) > 30 else text
        print(f"[{idx}/{len(bookmarks)}] 트윗 확인: {preview_text}")
        
        # 2. 제미나이에게 물어보기
        ai_category = classify_text_with_gemini(text)
        
        # 3. 노션 업데이트
        update_notion_category(page_id, ai_category)
        
        # 4. 🌟 제미나이 무료 API 제한 안 걸리게 4.1초 쉬기!
        time.sleep(4.1)

    print("\n🏁 모든 작업이 완료되었습니다!")