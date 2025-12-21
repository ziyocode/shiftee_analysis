# KakaoTalk 메시지 전송 모듈

위험 직원 목록을 카카오톡으로 자동 전송하는 모듈입니다.

## 파일 구성

- **`kakao_refresh_token.py`**: 메인 모듈, `Kakao` 클래스 정의
- **`kakao_get_token.py`**: 초기 토큰 발급 스크립트 (1회 실행)
- **`message_formatter.py`**: 메시지 포맷터 함수
- **`kakao_token.json`**: 토큰 저장 파일 (자동 생성, git 제외)
- **`kakao_token.json.example`**: 토큰 파일 템플릿

## 빠른 시작

### 1. 초기 설정 (최초 1회만)

자세한 설정 방법은 [docs/KAKAO_SETUP.md](../docs/KAKAO_SETUP.md)를 참조하세요.

1. 카카오 개발자 콘솔에서 애플리케이션 생성
2. REST API 키 발급 및 환경변수 설정:
   ```bash
   export KAKAO_APP_KEY="your_rest_api_key"
   ```
3. 인증 코드 받기
4. `kakao_get_token.py` 수정 후 실행하여 초기 토큰 발급

### 2. 사용 예제

```python
from kakao_send import Kakao, format_risk_message
import pandas as pd
from datetime import datetime

# DataFrame과 날짜 정보 준비
df = pd.read_excel("output/report.xlsx")
start_date = datetime(2025, 11, 1)
end_date = datetime(2025, 11, 30)

# 메시지 생성
message = format_risk_message(df, start_date, end_date)

# 카카오톡 전송
kakao = Kakao()
kakao.send_message(message)  # 토큰 자동 갱신 + 전송
```

### 3. CLI에서 사용

```bash
# 분석 후 위험 직원 목록 전송
python scripts/calculate_risk_direct.py --send-kakao

# 요약만 전송
python scripts/calculate_risk_direct.py --kakao-summary

# 다운로드 + 분석 + 전송
python scripts/calculate_risk_direct.py --download --send-kakao
```

## API 문서

### Kakao 클래스

```python
class Kakao:
    def __init__(self, app_key: str = None)
    def refresh_token(self) -> bool
    def send_to_me(self, text: str) -> bool
    def send_message(self, text: str) -> bool  # 자동 갱신 + 전송
```

#### `__init__(app_key: str = None)`

Kakao 클래스 초기화

**Parameters:**
- `app_key`: 카카오 REST API 키 (선택사항, 환경변수 `KAKAO_APP_KEY`에서 자동 로드)

**Raises:**
- `ValueError`: API 키를 찾을 수 없는 경우
- `FileNotFoundError`: `kakao_token.json` 파일을 찾을 수 없는 경우

#### `refresh_token() -> bool`

액세스 토큰 갱신

**Returns:**
- `bool`: 갱신 성공 여부

#### `send_to_me(text: str) -> bool`

나에게 카카오톡 메시지 전송

**Parameters:**
- `text`: 전송할 메시지 내용

**Returns:**
- `bool`: 전송 성공 여부

#### `send_message(text: str) -> bool`

토큰 자동 갱신 후 메시지 전송 (권장)

**Parameters:**
- `text`: 전송할 메시지 내용

**Returns:**
- `bool`: 전송 성공 여부

### 메시지 포맷터

```python
def format_risk_message(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime,
    show_all: bool = False
) -> str
```

위험 직원 목록을 카카오톡 메시지 형식으로 변환

**Parameters:**
- `df`: 분석 결과 DataFrame
- `start_date`: 분석 시작 날짜
- `end_date`: 분석 종료 날짜
- `show_all`: True이면 전체 직원 목록, False이면 위험 직원만 (기본값: False)

**Returns:**
- `str`: 카카오톡 메시지 형식의 문자열

---

```python
def format_summary_message(
    df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime
) -> str
```

요약 메시지만 생성 (위험 직원 목록 제외)

**Parameters:**
- `df`: 분석 결과 DataFrame
- `start_date`: 분석 시작 날짜
- `end_date`: 분석 종료 날짜

**Returns:**
- `str`: 요약 메시지

## 토큰 관리

### 토큰 자동 갱신

- `send_message()` 메서드 사용 시 자동으로 토큰 갱신
- 액세스 토큰은 6시간마다 만료
- 리프레시 토큰은 약 2개월간 유효

### 토큰 만료 시

리프레시 토큰이 만료되면 초기 설정 과정을 다시 진행:

1. 인증 코드 재발급
2. `kakao_get_token.py` 실행
3. 새로운 `kakao_token.json` 생성

## 보안 주의사항

⚠️ **중요**: 다음 파일들은 절대 git에 커밋하지 마세요:
- `kakao_token.json` (토큰 정보 포함)
- REST API 키를 포함한 `.env` 파일

## 문제 해결

자세한 문제 해결 방법은 [docs/KAKAO_SETUP.md](../docs/KAKAO_SETUP.md)의 "문제 해결" 섹션을 참조하세요.

## 참고 자료

- [카카오 메시지 API 공식 문서](https://developers.kakao.com/docs/latest/ko/message/rest-api)
- [설정 가이드](../docs/KAKAO_SETUP.md)
- [CLI 사용 가이드](../docs/CLI_USAGE.md)
