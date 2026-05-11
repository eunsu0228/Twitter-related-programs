import os
from dotenv import load_dotenv
# .env 파일 안의 비밀번호들을 불러옴
load_dotenv()
import json
import requests
from datetime import datetime
import time  # 🌟 추가됨: 시간을 제어하는 라이브러리
# ==========================================
# 1. 설정값 입력 (나중에 여기에 본인 값을 넣으세요)
# ==========================================
NOTION_TOKEN = os.environ.get("NOTION_TOKEN_ttt")
DATABASE_ID = os.environ.get("DATABASE_ID_ttt")
JS_FILE_PATH = r"\tweets.js" # 다운받은 파일 경로

# 노션 API 통신을 위한 헤더 설정
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ==========================================
# 2. 트위터 js 파일 읽고 순수 JSON으로 변환
# ==========================================
with open(JS_FILE_PATH, 'r', encoding='utf-8') as f:
    raw_data = f.read()

# 'window.YTD.tweets.part0 = ' 이 부분을 찾아서 삭제
# (버전이나 파일명에 따라 part0 변수명이 조금 다를 수 있으니 실제 파일을 꼭 확인하세요!)
json_str = raw_data[raw_data.find('['):] 
tweets = json.loads(json_str)

# ==========================================
# 3. 데이터 추출 및 노션으로 전송
# ==========================================
print(f"총 {len(tweets)}개의 트윗을 발견했습니다. 노션 업로드를 시작합니다...")

# 🌟 수정됨: [:5]를 지우고, 진행 상황을 보기 위해 enumerate를 씌웠습니다.
for i, item in enumerate(tweets): 
    tweet_info = item['tweet']

    # 1. 기본 텍스트 및 ID 뽑아내기
    tweet_id = tweet_info['id_str']
    full_text = tweet_info['full_text']
    
    # 2. RT(리트윗) 분류 로직
    if full_text.startswith("RT @"):
        tweet_type = "RT"
    else:
        tweet_type = "내가 쓴 트윗"
    
    # 3. 날짜 형식 변환
    raw_date = tweet_info['created_at']
    parsed_date = datetime.strptime(raw_date, '%a %b %d %H:%M:%S %z %Y')
    notion_date = parsed_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    # 4. 이미지 URL 추출하기 (진짜 원본 이미지 주소 찾기)
    image_urls = []
    if 'extended_entities' in tweet_info and 'media' in tweet_info['extended_entities']:
        for media in tweet_info['extended_entities']['media']:
            if media['type'] == 'photo':
                image_urls.append(media['media_url_https'])
    
    # 5. 추출한 이미지를 노션 양식에 맞게 포장하기 (에러가 났던 부분!)
    # 이미지가 없으면 빈 리스트([])가 되어서 에러 없이 통과합니다.
    notion_files = []
    for i, url in enumerate(image_urls):
        notion_files.append({
            "name": f"photo_{i}.jpg",
            "type": "external",
            "external": {"url": url}
        })

    # 6. 노션에 보낼 데이터 양식(Payload) 조립하기
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "본문": { 
                "title": [{"text": {"content": full_text[:2000]}}]
            },
            "트윗 ID": { 
                "rich_text": [{"text": {"content": tweet_id}}]
            },
            "날짜": { 
                "date": {"start": notion_date}
            },
            "유형": { 
                "select": {"name": tweet_type}
            },
            "URL": { 
                "url": f"https://twitter.com/user/status/{tweet_id}"
            },
            "이미지": { # 🌟 파일과 미디어 속성 추가
                "files": notion_files
            }
        }
    }

    # 7. 노션 API로 전송(POST 요청)
    response = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"성공: {tweet_id} 업로드 완료")
    else:
        print(f"실패: {tweet_id} / 에러: {response.text}")

    # 🌟 가장 중요한 부분: 한 번 보내고 0.4초 쉬기 (초당 2.5개 속도)
    time.sleep(0.4) 

print("작업이 완료되었습니다!")