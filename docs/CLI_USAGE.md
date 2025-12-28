# CLI 사용 가이드

`shiftee-analyze` 명령어 사용법을 안내합니다.

## 설치

```bash
# 패키지 설치
pip install -e .

# 브라우저 설치 (최초 1회)
playwright install chromium
```

## 기본 사용법

```bash
shiftee-analyze [옵션]
```

## 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--download` | Shiftee 데이터 자동 다운로드 | - |
| `--start` | 분석 시작 날짜 (`YYYY-MM-DD`) | 이번 달 1일 |
| `--end` | 분석 종료 날짜 (`YYYY-MM-DD`) | 어제 |
| `--send-kakao` | 위험 직원 목록 카카오톡 전송 | - |
| `--output` | 결과 파일 경로 지정 | `output/report_YYYYMMDD.xlsx` |

## 추천 사용 예시

### 1. 자동 다운로드 및 분석 (추천)
가장 일반적으로 사용하는 명령어입니다. 이번 달 1일부터 어제까지의 데이터를 다운로드하여 분석합니다.

```bash
shiftee-analyze --download
```

### 2. 특정 월/기간 분석
지난달 데이터를 분석하고 싶을 때 사용합니다.

```bash
shiftee-analyze --download --start 2025-11-01 --end 2025-11-30
```

### 3. 카카오톡 보고서 전송
분석 완료 후 위험 직원 명단을 카카오톡으로 즉시 전송합니다.

```bash
shiftee-analyze --download --send-kakao
```

### 4. 파일만 분석 (다운로드 생략)
이미 `data/` 폴더에 엑셀 파일(`shiftee_data1.xlsx`, `shiftee_data2.xlsx`)이 있는 경우 사용합니다.

```bash
shiftee-analyze
```

## 문제 해결

### 명령어를 찾을 수 없음 (Command not found)
설치가 정상적으로 되지 않았을 수 있습니다. 다음 명령어로 다시 설치하세요.
```bash
pip install -e .
```

### 로그인 실패
프로젝트 루트의 `.env` 파일에 아이디와 비밀번호가 올바르게 설정되어 있는지 확인하세요.
```bash
SHIFTEE_ID=your-email@example.com
SHIFTEE_PASSWORD=your-password
```
