import os
from dotenv import load_dotenv
# .env 파일 안의 비밀번호들을 불러옴
load_dotenv()
import tweepy
import requests

# ---------------------------------------------------------
# 1. 설정값 세팅
# ---------------------------------------------------------
# 계정의 토큰을 리스트나 딕셔너리로 관리하면 편합니다.
ACCOUNT_TOKENS = [
    os.environ.get("twt_token1")
    # ... 추가는 , 를 사이에 넣고 추가해요
]

NOTION_TOKEN = os.environ.get("NOTION_TOKEN_ttb")
DATABASE_ID = os.environ.get("DATABASE_ID_ttb")

headers_notion = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# ---------------------------------------------------------
# 2. 계정별로 돌면서 북마크 가져오기
# ---------------------------------------------------------
for i, token in enumerate(ACCOUNT_TOKENS):
    print(f"\n--- {i+1}번째 계정 북마크 가져오는 중 ---")
    
    # Tweepy 클라이언트 생성 (이 클라이언트가 해당 계정인 척을 합니다)
    client = tweepy.Client(bearer_token=token)
    
    # API v2로 북마크 요청 (한 번에 최대 100개, 본문/날짜 등 추가 정보 요청)
    # 페이징(Pagination) 처리가 필요하지만 테스트를 위해 일단 첫 페이지 100개만 가져옵니다.
    response = client.get_bookmarks(
        max_results=100, 
        tweet_fields=["created_at"],
        expansions=["attachments.media_keys"],
        media_fields=["url"]
    )
    
    if not response.data:
        print("이 계정에는 북마크가 없습니다.")
        continue

    # 미디어(이미지) 데이터를 쉽게 찾기 위해 딕셔너리로 정리
    media_dict = {}
    if response.includes and 'media' in response.includes:
        for media in response.includes['media']:
            media_dict[media.media_key] = media.url

    # ---------------------------------------------------------
    # 3. 노션으로 데이터 쏘기 (기존 로직 재사용)
    # ---------------------------------------------------------
    for tweet in response.data:
        tweet_id = tweet.id
        full_text = tweet.text
        created_at = tweet.created_at # 이미 datetime 객체로 나옵니다.
        notion_date = created_at.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # 이미지 URL 추출 로직 (v2 API 방식에 맞게 수정)
        image_urls = []
        if tweet.attachments and 'media_keys' in tweet.attachments:
            for media_key in tweet.attachments['media_keys']:
                if media_key in media_dict and media_dict[media_key] is not None:
                    image_urls.append(media_dict[media_key])

        notion_files = []
        for idx, url in enumerate(image_urls):
            notion_files.append({
                "name": f"photo_{idx}.jpg",
                "type": "external",
                "external": {"url": url}
            })

        # 노션 Payload
        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "본문": {"title": [{"text": {"content": full_text[:2000]}}]},
                "트윗 ID": {"rich_text": [{"text": {"content": str(tweet_id)}}]},
                "날짜": {"date": {"start": notion_date}},
                "유형": {"select": {"name": "북마크"}}, # 유형을 북마크로 고정
                "URL": {"url": f"https://twitter.com/user/status/{tweet_id}"},
                "이미지": {"files": notion_files}
            }
        }

        # 노션에 전송 (딜레이 필수!)
        res = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers_notion)
        import time
        time.sleep(0.5)

print("\n🎉 모든 계정의 북마크 정리가 완료되었습니다!")
