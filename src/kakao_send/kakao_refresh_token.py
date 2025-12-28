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

    def __init__(self, app_key: str = None):
        """Kakao 클래스 초기화

        Args:
            app_key: 카카오 REST API 키 (선택사항)
                    제공되지 않으면 환경변수 KAKAO_APP_KEY에서 읽습니다.
        """
        self.app_key = "14a74c4d5dae813d9244b8a587696a11"

        if not self.app_key:
            raise ValueError(
                "카카오 REST API 키가 필요합니다. "
                "app_key 파라미터로 전달하거나 KAKAO_APP_KEY 환경변수를 설정하세요."
            )

        self.token_path = os.path.join(os.path.dirname(__file__), "kakao_token.json")

        # 토큰 파일이 없으면 안내 메시지 출력
        if not os.path.exists(self.token_path):
            raise FileNotFoundError(
                f"토큰 파일을 찾을 수 없습니다: {self.token_path}\n"
                "kakao_get_token.py를 실행하여 초기 토큰을 생성하세요."
            )

        with open(self.token_path, "r", encoding="utf-8") as fp:
            self.tokens = json.load(fp)

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

        with open(self.token_path, "w", encoding="utf-8") as fp:
            json.dump(self.tokens, fp, ensure_ascii=False, indent=2)

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
