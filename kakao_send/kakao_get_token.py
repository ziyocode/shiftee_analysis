"""카카오톡 초기 토큰 발급 스크립트

카카오 개발자 콘솔에서 받은 인증 코드를 사용하여 초기 토큰을 발급받습니다.

사용 방법:
    1. https://developers.kakao.com 에서 애플리케이션 생성
    2. REST API 키 확인
    3. 플랫폼 설정 > Web > Redirect URI 등록: https://www.example.com/oauth
    4. 동의항목 설정 > 카카오톡 메시지 전송(talk_message) 동의 필수
    5. 아래 URL로 접속하여 인증 코드 받기:
       https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri=https://www.example.com/oauth&response_type=code
    6. 리다이렉트된 URL에서 code 파라미터 값 복사
    7. 아래 코드의 client_id와 code를 수정 후 실행
"""

import requests
import json
import os

# 카카오 REST API 키 입력
CLIENT_ID = "YOUR_REST_API_KEY_HERE"

# 인증 코드 입력 (위 URL로 받은 code 파라미터 값)
AUTH_CODE = "YOUR_AUTHORIZATION_CODE_HERE"

# 토큰 발급 요청
url = "https://kauth.kakao.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "redirect_uri": "https://www.example.com/oauth",
    "code": AUTH_CODE,
}

response = requests.post(url, data=data)
tokens = response.json()

# 토큰을 파일로 저장하기
token_path = os.path.join(os.path.dirname(__file__), "kakao_token.json")

if "access_token" in tokens:
    with open(token_path, "w", encoding="utf-8") as fp:
        json.dump(tokens, fp, ensure_ascii=False, indent=2)
    print("✓ 토큰 저장 성공:", token_path)
    print("\n발급받은 토큰:")
    print(f"  - Access Token: {tokens['access_token'][:20]}...")
    print(f"  - Refresh Token: {tokens['refresh_token'][:20]}...")
    print(f"  - Expires In: {tokens['expires_in']}초 ({tokens['expires_in']//3600}시간)")
else:
    print("✗ 토큰 발급 실패:")
    print(tokens)
    print("\n다음 사항을 확인하세요:")
    print("  1. REST API 키가 올바른지")
    print("  2. 인증 코드가 유효한지 (만료되지 않았는지)")
    print("  3. Redirect URI가 일치하는지")
    print("  4. 카카오톡 메시지 전송 권한이 활성화되었는지")
