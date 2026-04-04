"""Slack Incoming Webhook 메시지 전송 모듈."""

import json
import requests


class SlackWebhook:
    """Slack Incoming Webhook으로 메시지를 전송합니다."""

    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("Slack Webhook URL이 필요합니다.")
        self.webhook_url = webhook_url

    def send_message(self, text: str) -> bool:
        """텍스트 메시지를 Slack 채널로 전송.

        Args:
            text: 전송할 메시지 (Slack mrkdwn 형식)

        Returns:
            bool: 전송 성공 여부
        """
        payload = {"text": text}
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 200 and response.text == "ok":
                print("   ✓ Slack 메시지 전송 성공!")
                return True
            else:
                print(f"   ✗ Slack 메시지 전송 실패: {response.status_code} {response.text}")
                return False
        except requests.RequestException as e:
            print(f"   ✗ Slack 전송 오류: {e}")
            return False
