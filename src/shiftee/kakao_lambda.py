"""AWS Lambda용 카카오톡 메시지 전송 모듈.

Secrets Manager에서 토큰을 관리하며, 기존 Kakao 클래스와 동일한 인터페이스를 제공합니다.
"""

import json
import logging
import os

import boto3
import requests

logger = logging.getLogger("shiftee-lambda")


class KakaoLambda:
    """Secrets Manager 기반 카카오톡 메시지 전송 클래스."""

    def __init__(self):
        client = boto3.client("secretsmanager")
        secret_name = os.environ.get("KAKAO_SECRET_NAME", "shiftee/kakao-token")

        response = client.get_secret_value(SecretId=secret_name)
        self.tokens = json.loads(response["SecretString"])
        self.app_key = self.tokens["app_key"]
        self._secret_name = secret_name
        self._client = client

    def refresh_token(self) -> bool:
        """카카오 액세스 토큰 갱신 후 Secrets Manager에 저장."""
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.app_key,
            "refresh_token": self.tokens["refresh_token"],
        }

        response = requests.post(url, data=data)
        result = response.json()

        if "access_token" in result:
            self.tokens["access_token"] = result["access_token"]
            logger.info("Access token refreshed")
        else:
            logger.error(f"Token refresh failed: {result}")
            return False

        if "refresh_token" in result:
            self.tokens["refresh_token"] = result["refresh_token"]

        # Secrets Manager에 갱신된 토큰 저장
        self._client.put_secret_value(
            SecretId=self._secret_name,
            SecretString=json.dumps(self.tokens, ensure_ascii=False),
        )
        logger.info("Tokens saved to Secrets Manager")
        return True

    def send_to_me(self, text: str) -> bool:
        """나에게 카카오톡 메시지 전송."""
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {"Authorization": "Bearer " + self.tokens["access_token"]}
        content = {
            "object_type": "text",
            "text": text,
            "link": {"mobile_web_url": "https://www.example.com"},
        }
        data = {"template_object": json.dumps(content, ensure_ascii=False)}

        res = requests.post(url, headers=headers, data=data)
        result = res.json()

        if "result_code" in result and result["result_code"] == 0:
            logger.info("KakaoTalk message sent successfully")
            return True

        logger.error(f"KakaoTalk message failed: {result}")
        return False

    def send_message(self, text: str) -> bool:
        """토큰 갱신 후 메시지 전송."""
        if not self.refresh_token():
            return False
        return self.send_to_me(text)
