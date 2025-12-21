# 카카오톡 메시지 전송 설정 가이드

이 문서는 위험 직원 목록을 카카오톡으로 자동 전송하는 기능을 설정하는 방법을 안내합니다.

## 개요

분석 완료 후 위험 직원 목록을 카카오톡 '나에게 보내기'로 자동 전송할 수 있습니다.
카카오 REST API를 사용하여 메시지를 전송합니다.

## 사전 준비

1. **카카오 개발자 계정**: https://developers.kakao.com
2. **Python requests 패키지**: `pip install requests` (이미 requirements.txt에 포함됨)

## 설정 단계

### 1단계: 카카오 애플리케이션 생성

1. https://developers.kakao.com 접속 및 로그인
2. **내 애플리케이션** → **애플리케이션 추가하기**
3. 앱 이름 입력 (예: "Shiftee 분석 알림")
4. **저장** 클릭

### 2단계: REST API 키 확인

1. 생성된 애플리케이션 클릭
2. **앱 키** 섹션에서 **REST API 키** 복사
3. 환경변수 또는 `.env` 파일에 저장:

```bash
# .env 파일에 추가
KAKAO_APP_KEY=your_rest_api_key_here
```

또는 직접 환경변수로 설정:

```bash
export KAKAO_APP_KEY="your_rest_api_key_here"
```

### 3단계: Redirect URI 설정

1. 애플리케이션 설정 → **플랫폼** → **Web 플랫폼 등록**
2. **Redirect URI** 등록: `https://www.example.com/oauth`
3. **저장** 클릭

### 4단계: 카카오톡 메시지 전송 권한 활성화

1. 애플리케이션 설정 → **동의항목**
2. **카카오톡 메시지 전송(talk_message)** 찾기
3. **설정** → **필수 동의**로 변경
4. **저장** 클릭

### 5단계: 인증 코드 발급

1. 아래 URL을 웹 브라우저에서 열기 (REST API 키를 본인 것으로 교체):

```
https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri=https://www.example.com/oauth&response_type=code
```

예시:
```
https://kauth.kakao.com/oauth/authorize?client_id=14a74c4d5dae813d9244b8a587696a11&redirect_uri=https://www.example.com/oauth&response_type=code
```

2. 카카오 계정 로그인 및 동의
3. 리다이렉트된 URL에서 `code` 파라미터 복사:

```
https://www.example.com/oauth?code=OkwcdO5piN26am0uIxKSQXIiGVjwR4xQjrwDvdxsRCGXx4ws3OSKFAAAAAQKFzVXAAABmdf8HGDUNEQ5evY1pg
```

→ `OkwcdO5piN26am0uIxKSQXIiGVjwR4xQjrwDvdxsRCGXx4ws3OSKFAAAAAQKFzVXAAABmdf8HGDUNEQ5evY1pg` 부분이 인증 코드

### 6단계: 초기 토큰 발급

1. `kakao_send/kakao_get_token.py` 파일 수정:

```python
# 카카오 REST API 키 입력
CLIENT_ID = "your_rest_api_key_here"  # 본인의 REST API 키로 교체

# 인증 코드 입력 (5단계에서 받은 code)
AUTH_CODE = "your_authorization_code_here"  # 본인의 인증 코드로 교체
```

2. 스크립트 실행:

```bash
cd /Users/ryancho/Documents/workspaces/python/shiftee_analysis
python kakao_send/kakao_get_token.py
```

3. 성공 메시지 확인:

```
✓ 토큰 저장 성공: /Users/ryancho/Documents/workspaces/python/shiftee_analysis/kakao_send/kakao_token.json

발급받은 토큰:
  - Access Token: 1h-I6XDbBJmlERcFZv...
  - Refresh Token: irZ8BBbvZDBnLcavg5...
  - Expires In: 21599초 (5시간)
```

4. `kakao_send/kakao_token.json` 파일이 생성되었는지 확인

## 사용 방법

### 기본 사용 (위험 직원 목록 전송)

```bash
python scripts/calculate_risk_direct.py --send-kakao
```

### 요약 메시지만 전송

```bash
python scripts/calculate_risk_direct.py --kakao-summary
```

### 다운로드 + 분석 + 카카오톡 전송 한 번에

```bash
python scripts/calculate_risk_direct.py --download --send-kakao
```

### 특정 기간 분석 후 전송

```bash
python scripts/calculate_risk_direct.py --start 2025-11-01 --end 2025-11-30 --send-kakao
```

## 메시지 형식

### 위험 직원 목록 메시지 (`--send-kakao`)

```
📊 초과근로 적정성 분석 결과
📅 분석 기간: 2025-11-01 ~ 2025-11-30

━━━━━━━━━━━━━━━━━━
📈 전체 현황
━━━━━━━━━━━━━━━━━━
총 직원: 46명
  ✅ 정상: 43명 (93.5%)
  ⚠️ 위험: 3명 (6.5%)
  🚨 법규기준초과: 0명 (0.0%)

━━━━━━━━━━━━━━━━━━
⚠️ 주의 필요 직원 목록
━━━━━━━━━━━━━━━━━━

⚠️ 위험 직원:
  • 이상훈 (뱅킹IS팀)
    초과근로: 45.38h / 법정기준: 42.86h
  • 박근혁 (뱅킹IS팀)
    초과근로: 44.43h / 법정기준: 42.86h
  • 이준우 (뱅킹IS팀)
    초과근로: 44.12h / 법정기준: 42.86h

━━━━━━━━━━━━━━━━━━
생성일시: 2025-12-21 15:30:45
```

### 요약 메시지 (`--kakao-summary`)

```
📊 초과근로 적정성 분석 완료

📅 기간: 2025-11-01 ~ 2025-11-30

총 46명
✅ 정상: 43명 (93.5%)
⚠️ 위험: 3명 (6.5%)
🚨 법규초과: 0명 (0.0%)

생성: 2025-12-21 15:30:45
```

## 토큰 자동 갱신

- 액세스 토큰은 6시간마다 만료됩니다
- 메시지 전송 시 자동으로 토큰이 갱신되므로 별도 관리 불필요
- 리프레시 토큰은 약 2개월간 유효합니다
- 리프레시 토큰 만료 시 5단계부터 다시 진행하여 새로운 토큰 발급 필요

## 문제 해결

### 토큰 파일을 찾을 수 없습니다

**원인**: `kakao_token.json` 파일이 생성되지 않았습니다.

**해결**:
1. 6단계 (초기 토큰 발급)를 다시 진행하세요
2. `kakao_send/kakao_get_token.py` 실행 시 오류가 있었는지 확인하세요

### 토큰 갱신 실패

**원인**: 리프레시 토큰이 만료되었거나 REST API 키가 잘못되었습니다.

**해결**:
1. `KAKAO_APP_KEY` 환경변수가 올바른지 확인
2. 5단계부터 다시 진행하여 새로운 인증 코드 및 토큰 발급

### 카카오톡 메시지 전송 실패

**원인**:
- 토큰이 만료됨
- 카카오톡 메시지 전송 권한이 활성화되지 않음
- 네트워크 오류

**해결**:
1. 4단계에서 카카오톡 메시지 전송 권한이 활성화되었는지 확인
2. 인터넷 연결 상태 확인
3. 토큰 갱신 실패 메시지가 있는지 확인

### requests 패키지를 불러올 수 없습니다

**원인**: `requests` 패키지가 설치되지 않았습니다.

**해결**:
```bash
pip install requests
```

또는 전체 의존성 재설치:
```bash
pip install -r requirements.txt
```

## 보안 주의사항

1. **토큰 파일 관리**:
   - `kakao_send/kakao_token.json` 파일은 git에 커밋하지 마세요
   - `.gitignore`에 이미 추가되어 있습니다

2. **REST API 키 관리**:
   - `KAKAO_APP_KEY`는 환경변수로 관리하세요
   - 코드에 직접 하드코딩하지 마세요

3. **인증 코드 만료**:
   - 인증 코드는 발급 후 짧은 시간 내에 사용해야 합니다
   - 사용하지 않은 코드는 만료되어 재발급이 필요합니다

## 추가 참고

- 카카오 개발자 문서: https://developers.kakao.com/docs/latest/ko/message/rest-api
- 토큰 관리: https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#refresh-token
- 메시지 전송: https://developers.kakao.com/docs/latest/ko/message/rest-api#default-template-msg-me

## 커스터마이징

메시지 형식을 변경하려면 `kakao_send/message_formatter.py` 파일을 수정하세요:

- `format_risk_message()`: 위험 직원 목록 메시지 형식
- `format_summary_message()`: 요약 메시지 형식

예시:
```python
# 이모지 변경
message += "🔔 알림: 초과근로 분석 완료\n"

# 추가 정보 포함
message += f"평균 초과근로: {df['O_실제초과근로_조기출근제외'].mean():.2f}h\n"

# 메시지 링크 변경
content = {
    "object_type": "text",
    "text": text,
    "link": {"mobile_web_url": "https://your-dashboard-url.com"},
}
```
