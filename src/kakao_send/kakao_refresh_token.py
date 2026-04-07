"""KakaoTalk 메시지 전송 모듈

카카오톡 API를 사용하여 나에게 메시지를 전송합니다.
토큰 갱신 및 메시지 전송 기능을 제공합니다.
"""

import requests
import json
import os


class Kakao:
    """카카오톡 메시지 전송 클래스

    카카오톡 REST API를 사용하여 토큰 관리 및 메시지 전송을 수행합니다.
    """

    def __init__(self, app_key: str = None, access_token: str = None, refresh_token: str = None):
        """Kakao 클래스 초기화

        Args:
            app_key: 카카오 REST API 키
            access_token: 카카오 액세스 토큰
            refresh_token: 카카오 리프레시 토큰
        """
        self.app_key = app_key

        if not self.app_key:
            raise ValueError(
                "카카오 REST API 키가 필요합니다. "
                ".env 파일의 SHIFTEE_KAKAO_APP_KEY를 설정하세요."
            )

        self.token_path = os.path.join(os.path.dirname(__file__), "kakao_token.json")

        if access_token and refresh_token:
            self.tokens = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        elif os.path.exists(self.token_path):
            with open(self.token_path, "r", encoding="utf-8") as fp:
                self.tokens = json.load(fp)
        else:
            raise FileNotFoundError(
                "카카오 토큰을 찾을 수 없습니다.\n"
                ".env 파일의 SHIFTEE_KAKAO_ACCESS_TOKEN/SHIFTEE_KAKAO_REFRESH_TOKEN을 설정하거나,\n"
                "kakao_get_token.py를 실행하여 토큰 파일을 생성하세요."
            )

    def refresh_token(self) -> bool:
        """카카오 액세스 토큰 갱신

        refresh_token을 사용하여 새로운 access_token을 발급받습니다.

        Returns:
            bool: 갱신 성공 여부
        """
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.app_key,
            "refresh_token": self.tokens["refresh_token"],
        }

        response = requests.post(url, data=data)
        result = response.json()

        # 갱신 된 내용으로 파일 업데이트
        if "access_token" in result:
            self.tokens["access_token"] = result["access_token"]
            print("   ✓ 액세스 토큰 갱신 성공")
        else:
            print("   ✗ 토큰 갱신 실패:")
            print(f"   {result}")
            return False

        if "refresh_token" in result:
            self.tokens["refresh_token"] = result["refresh_token"]

        # 토큰 파일 업데이트 (다음 실행을 위해)
        try:
            with open(self.token_path, "w", encoding="utf-8") as fp:
                json.dump(self.tokens, fp, ensure_ascii=False, indent=2)
        except OSError:
            pass  # 파일 쓰기 불가 환경(Lambda 등)에서는 무시

        return True

    def send_to_me(self, text: str) -> bool:
        """나에게 카카오톡 메시지 전송

        Args:
            text: 전송할 메시지 내용

        Returns:
            bool: 전송 성공 여부
        """
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {"Authorization": "Bearer " + self.tokens["access_token"]}
        content = {
            "object_type": "text",
            "text": text,
            "link": {"mobile_web_url": "https://www.example.com"},
        }

        data = {"template_object": json.dumps(content, ensure_ascii=False)}
        res = requests.post(url, headers=headers, data=data)

        # 응답 확인
        result = res.json()
        if "result_code" in result and result["result_code"] == 0:
            print("   ✓ 카카오톡 메시지 전송 성공!")
            return True
        else:
            print("   ✗ 카카오톡 메시지 전송 실패:")
            print(f"   {result}")
            return False

    def send_message(self, text: str) -> bool:
        """토큰 자동 갱신 후 메시지 전송

        토큰을 갱신한 후 메시지를 전송합니다.

        Args:
            text: 전송할 메시지 내용

        Returns:
            bool: 전송 성공 여부
        """
        # 토큰 갱신
        if not self.refresh_token():
            return False

        # 메시지 전송
        return self.send_to_me(text)
