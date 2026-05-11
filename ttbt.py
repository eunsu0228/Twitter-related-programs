import os
from dotenv import load_dotenv
 # .env 파일 안의 비밀번호들을 불러옴
load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import tweepy

# 1단계에서 발급받은 키를 입력하세요.
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")

# OAuth 2.0 인증 객체 생성 (북마크 읽기 권한 등 명시)
oauth2_user_handler = tweepy.OAuth2UserHandler(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scope=["tweet.read", "users.read", "bookmark.read", "offline.access"],
    client_secret=CLIENT_SECRET
)

# 1. 로그인할 수 있는 URL을 화면에 출력합니다.
print("아래 링크를 클릭해서 트위터에 로그인하고 '앱 승인'을 누르세요:")
print(oauth2_user_handler.get_authorization_url())

# 2. 승인 후 브라우저 주소창에 뜨는 전체 URL을 복사해서 터미널에 붙여넣습니다.
authorization_response = input("승인 후 리디렉션된 전체 URL을 붙여넣으세요: ")

# 3. 입력받은 URL을 이용해 최종 Access Token을 발급받습니다.
access_token = oauth2_user_handler.fetch_token(authorization_response)

print("\n🎉 발급 성공! 아래 토큰 정보를 저장해두세요:")
print(f"Access Token: {access_token['access_token']}")
# offline.access 스코프를 넣었으므로 Refresh Token도 나옵니다.
print(f"Refresh Token: {access_token['refresh_token']}")