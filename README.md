# Shiftee 급여 보고서 자동화 도구

Shiftee.io에서 데이터를 다운로드하고 Excel 보고서를 자동으로 생성하는 도구입니다.

## 주요 기능

- 🔐 Shiftee.io 자동 로그인
- 📥 REALTIME-REPORT 및 PAYROLL 파일 자동 다운로드
- 📊 Excel 템플릿 기반 보고서 자동 생성
- 📋 공지용 시트 준비 (수동 작업 최소화)
- ✅ 생성된 보고서 자동 검증
- 🔄 Excel 수식 자동 재계산 설정

## 설치

### 필수 요구사항

- Python 3.10 이상
- pip (Python 패키지 관리자)

### 의존성 설치

```bash
pip install -r requirements.txt
```

### Playwright 브라우저 설치

```bash
playwright install chromium
```

## 설정

### 1. 환경 변수 설정

프로젝트 루트 디렉터리에 `.env` 파일을 생성하거나 `config/settings.toml` 파일을 사용합니다:

```bash
# .env 파일
SHIFTEE_ID=your-email@example.com
SHIFTEE_PASSWORD=your-password
SHIFTEE_HEADLESS=true
```

또는

```toml
# config/settings.toml
SHIFTEE_ID = "your-email@example.com"
SHIFTEE_PASSWORD = "your-password"
SHIFTEE_HEADLESS = true
```

### 2. 템플릿 파일 준비

Excel 템플릿 파일을 준비합니다. 템플릿은 다음 시트를 포함해야 합니다:

- `shiftee데이타`: REALTIME-REPORT 데이터용
- `shiftee데이타2`: PAYROLL 데이터용
- `계산`: 계산 수식 시트
- `정리`: 정리 수식 시트
- `공지용`: 공지용 시트 (수동 작성)

## 사용법

### 기본 명령어 구조

```bash
python shiftee_analysis.py [명령어] [옵션]
```

### 1. 전체 워크플로우 실행

다운로드 + 보고서 생성을 한 번에 실행합니다:

```bash
python shiftee_analysis.py full --template template.xlsx
```

#### 옵션

- `--template TEMPLATE`: 템플릿 Excel 파일 경로 (필수)
- `--output OUTPUT`: 출력 파일 경로 (기본: `output/report_YYYYMMDD_HHMMSS.xlsx`)
- `--data-dir DATA_DIR`: 다운로드 데이터 디렉터리 (기본: `data`)
- `--skip-download`: 다운로드 건너뛰기 (기존 파일 사용)
- `--overwrite`: 기존 출력 파일 덮어쓰기
- `--no-validate`: 검증 단계 건너뛰기
- `--no-headless`: 브라우저 표시 (디버깅용)

#### 예시

```bash
# 전체 워크플로우 실행 (다운로드 + 보고서 생성)
python shiftee_analysis.py full --template ~/Downloads/template.xlsx

# 이미 다운로드된 파일로 보고서 생성
python shiftee_analysis.py full --template ~/Downloads/template.xlsx --skip-download

# 출력 경로 지정 및 덮어쓰기
python shiftee_analysis.py full --template ~/Downloads/template.xlsx --output report.xlsx --overwrite

# 브라우저 표시 (디버깅)
python shiftee_analysis.py full --template ~/Downloads/template.xlsx --no-headless
```

### 2. 다운로드만 수행

Shiftee에서 데이터만 다운로드합니다:

```bash
python shiftee_analysis.py download
```

#### 옵션

- `--data-dir DATA_DIR`: 다운로드 데이터 디렉터리 (기본: `data`)
- `--no-headless`: 브라우저 표시 (디버깅용)

#### 예시

```bash
# 기본 다운로드
python shiftee_analysis.py download

# 브라우저 표시하며 다운로드
python shiftee_analysis.py download --no-headless
```

### 3. 보고서 생성만 수행

이미 다운로드된 파일로 보고서를 생성합니다:

```bash
python shiftee_analysis.py generate --template template.xlsx
```

#### 옵션

- `--template TEMPLATE`: 템플릿 Excel 파일 경로 (필수)
- `--realtime REALTIME`: REALTIME-REPORT 파일 경로 (자동 검색 시 생략 가능)
- `--payroll PAYROLL`: PAYROLL 파일 경로 (자동 검색 시 생략 가능)
- `--output OUTPUT`: 출력 파일 경로 (기본: `output/report_YYYYMMDD_HHMMSS.xlsx`)
- `--data-dir DATA_DIR`: 데이터 디렉터리 (자동 검색 시 사용, 기본: `data`)
- `--overwrite`: 기존 출력 파일 덮어쓰기
- `--no-validate`: 검증 단계 건너뛰기

#### 예시

```bash
# 자동 파일 검색으로 보고서 생성
python shiftee_analysis.py generate --template ~/Downloads/template.xlsx

# 파일 경로 직접 지정
python shiftee_analysis.py generate \
  --template ~/Downloads/template.xlsx \
  --realtime data/SHIFTEE-REALTIME-REPORT-20251201-20251231.xlsx \
  --payroll data/SHIFTEE-PAYROLL-BY-SHIFT-AND-ATTENDANCE-20251201-20251212.xlsx \
  --output output/report.xlsx

# 검증 없이 생성
python shiftee_analysis.py generate --template ~/Downloads/template.xlsx --no-validate
```

### 4. 보고서 검증

생성된 보고서를 검증합니다:

```bash
python shiftee_analysis.py validate output/report.xlsx
```

#### 옵션

- `--validate-notice`: 공지용 시트도 검증 (기본: 건너뛰기)

#### 예시

```bash
# 기본 검증
python shiftee_analysis.py validate output/report.xlsx

# 공지용 시트도 검증
python shiftee_analysis.py validate output/report.xlsx --validate-notice
```

### 공통 옵션

모든 명령어에서 사용 가능한 옵션:

- `-v, --verbose`: 상세 로깅 활성화
- `-q, --quiet`: 최소 로깅 (경고만 표시)
- `--config CONFIG`: 설정 파일 경로 (기본: `.env`)
- `-h, --help`: 도움말 표시

#### 예시

```bash
# 상세 로깅으로 실행
python shiftee_analysis.py -v generate --template ~/Downloads/template.xlsx

# 최소 로깅으로 실행
python shiftee_analysis.py -q download
```

## 프로젝트 구조

```
shiftee_analysis/
├── shiftee_analysis.py          # 메인 CLI 진입점
├── src/
│   └── shiftee/
│       ├── __init__.py
│       ├── __main__.py           # 모듈 직접 실행 진입점
│       ├── cli.py                # CLI 로직
│       ├── workflow.py           # 워크플로우 통합
│       ├── settings.py           # 설정 관리
│       ├── login.py              # Shiftee 로그인
│       ├── attendance.py         # 파일 다운로드
│       ├── excel_processor.py    # Excel 처리
│       ├── template.py           # 템플릿 관리
│       ├── data_mapper.py        # 데이터 매핑
│       ├── report_generator.py   # 보고서 생성
│       └── validator.py          # 보고서 검증
├── config/
│   └── settings.example.toml     # 설정 예시 파일
├── data/                         # 다운로드된 데이터 저장
├── output/                       # 생성된 보고서 저장
├── docs/                         # 문서
│   └── To_do_list.md
├── .env                          # 환경 변수 (gitignore)
└── requirements.txt              # Python 의존성
```

## 워크플로우

### 전체 프로세스

```
1. Shiftee 로그인
   ↓
2. REALTIME-REPORT 다운로드
   ↓
3. PAYROLL 다운로드
   ↓
4. 템플릿 Excel 로드
   ↓
5. 템플릿 인스턴스 생성
   ↓
6. shiftee데이타 시트에 REALTIME 데이터 매핑
   ↓
7. shiftee데이타2 시트에 PAYROLL 데이터 매핑
   ↓
8. Excel 수식 재계산 활성화
   ↓
9. 파일 저장
   ↓
10. 보고서 검증
   ↓
11. 완료
```

### 공지용 시트 생성

생성된 보고서에서 공지용 시트를 만드는 방법:

#### 자동 생성 (Excel에서 수식으로)

생성된 보고서를 Excel에서 열면:
1. **수식 자동 재계산**: `계산` 및 `정리` 시트의 모든 수식이 자동으로 계산됩니다
2. **공지용 시트 확인**: `정리` 시트의 결과를 기반으로 위험/법기준초과 대상자를 확인할 수 있습니다

#### 수동 작성 (필요 시)

필요에 따라 공지용 시트를 수동으로 작성할 수 있습니다:

1. **Excel에서 보고서 열기**
2. **정리 시트로 이동**
3. **필터 적용**:
   - "적정성" 컬럼에서 "위험" 또는 "법기준초과" 선택
4. **공지용 시트에 복사**:
   - 필터링된 행을 선택하여 복사
   - `공지용` 시트에 붙여넣기

#### VBA 매크로 활용 (고급)

반복 작업을 자동화하려면 Excel VBA 매크로를 작성할 수 있습니다:

```vba
Sub GenerateNotice()
    ' 정리 시트에서 위험/법기준초과 대상자를 공지용 시트로 복사
    Dim wsSource As Worksheet
    Dim wsTarget As Worksheet

    Set wsSource = ThisWorkbook.Sheets("정리")
    Set wsTarget = ThisWorkbook.Sheets("공지용")

    ' 필터링 및 복사 로직
    ' (상세 구현은 프로젝트 요구사항에 따라 작성)
End Sub
```

#### 주요 확인 항목

공지용 시트 생성 시 다음을 확인하세요:

- ✅ **소정근로시간**: 정상 범위 내인지 확인
- ✅ **초과근로시간**: 52시간 법규 위반 여부
- ✅ **적정성 판단**: "위험" 또는 "법기준초과" 대상자
- ✅ **월말까지 가능시간**: 음수인 경우 이미 초과 상태

### 수동 작업 필요 사항

생성된 보고서는 다음 작업이 필요합니다:

1. **Excel에서 파일 열기**: 수식 자동 재계산 (자동)
2. **공지용 시트 작성**: 위 "공지용 시트 생성" 섹션 참고 (선택)

## 검증 항목

보고서 검증 시 다음 항목을 확인합니다:

- ✅ 필수 시트 존재 확인
- ✅ 데이터 시트 최소 행 수 확인
- ✅ 계산 시트 수식 개수 확인
- ⚠️ 공지용 시트 (선택적 검증)

## 문제 해결

### 로그인 실패

- `.env` 파일에 올바른 이메일과 비밀번호가 설정되어 있는지 확인
- `--no-headless` 옵션으로 브라우저를 표시하여 로그인 과정 확인

### 파일 다운로드 실패

- 네트워크 연결 확인
- Shiftee.io 웹사이트 접속 가능 여부 확인
- `--no-headless` 옵션으로 다운로드 과정 확인

### 보고서 생성 실패

- 템플릿 파일 경로 확인
- REALTIME-REPORT 및 PAYROLL 파일 존재 확인
- `-v` 옵션으로 상세 로그 확인

### 검증 실패

- 데이터 시트에 최소 1행 이상의 데이터가 있는지 확인
- 계산 시트에 수식이 있는지 확인
- 템플릿 구조가 올바른지 확인

## 개발자 정보

### 모듈 직접 실행

```bash
python -m src.shiftee full --template template.xlsx
python -m src.shiftee download
python -m src.shiftee generate --template template.xlsx
python -m src.shiftee validate output/report.xlsx
```

### Python API 사용

```python
from src.shiftee.workflow import ShifteeWorkflow, WorkflowConfig
from src.shiftee.settings import ShifteeSettings

# 설정
settings = ShifteeSettings()
config = WorkflowConfig(
    template_path="template.xlsx",
    output_path="output/report.xlsx",
    skip_download=False,
    validate=True,
    overwrite=True,
)

# 워크플로우 실행
import asyncio
workflow = ShifteeWorkflow(settings=settings, config=config)
result = asyncio.run(workflow.run_full_workflow())

if result["success"]:
    print(f"보고서 생성 완료: {result['generate']['output_path']}")
else:
    print(f"실패: {result['errors']}")
```

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다.
