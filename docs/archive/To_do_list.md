# 공지용 Excel 자동 생성 작업 목록

## 프로젝트 목표
Shiftee에서 다운로드한 두 개의 Excel 파일을 기반으로 템플릿 Excel 파일을 자동으로 업데이트하여 최종 "공지용" 시트를 생성하는 자동화 시스템 구축

## 현재 상황 분석

### 입력 파일
1. **SHIFTEE-REALTIME-REPORT-*.xlsx** (리포트)
   - Sheet: `20251201-20251231` (날짜 범위로 동적 생성)
   - 25개 컬럼: 사원번호, 직원, 입사일, 퇴사일, 본조직, 본직무, 소정근로시간, 승인된 근로시간, 실제 근로시간 등
   - 약 46-132명의 직원 데이터

2. **SHIFTEE-PAYROLL-BY-SHIFT-AND-ATTENDANCE-*.xlsx** (실급여정산)
   - Sheet: `실급여정산(근무일정 및 출퇴근기록 기반) `
   - 47개 컬럼: 사원번호, 이름, 지점, 직무, 각종 급여 및 수당 계산 데이터
   - 약 384-2545개 행 (직원별 상세 데이터)

### 템플릿 파일 구조
**파일**: `레포트_20251101-1130_뱅킹인프라본부_정문현 (1).xlsx`

- **작성법 시트**: 사용 설명서 (수동 작성 가이드)
- **shiftee데이타 시트**: REALTIME-REPORT 데이터가 들어가는 곳 (25개 컬럼)
- **shiftee데이타2 시트**: PAYROLL 데이터가 들어가는 곳 (47개 컬럼, header는 2번째 행)
- **계산 시트**: shiftee데이타/shiftee데이타2를 참조하여 계산 수행 (수식 기반)
  - 소정근로시간, 승인된 근로시간, 실제 근로시간, 표준 근로시간 등 계산
  - 초과근로 시간, 법규 위반 시간, 적정성 판단 등
- **정리 시트**: 계산 시트 결과를 정리 (수식으로 계산 시트 참조)
- **공지용 시트**: 정리 시트에서 위험/법기준초과 대상자만 필터링하여 표시 (최종 결과물)
- **월요일대상자 시트**: 특정 조건의 대상자 리스트

### 발견된 계산 로직 예시
```excel
계산!D2 = shiftee데이타!G2  (소정근로시간)
계산!E2 = shiftee데이타!H2  (승인된 근로시간)
계산!F2 = shiftee데이타!J2  (실제 근로시간)
계산!G2 = shiftee데이타!J2 + shiftee데이타!W2*8 + shiftee데이타!X2*8  (결근/퇴근누락 포함)
계산!H2 = SUMPRODUCT(...) - shiftee데이타2 참조하여 복잡한 시간 계산

정리!D2 = 계산!D2
정리!E2 = 계산!F2
...
```

## 작업 단계

### Phase 1: 프로젝트 구조 및 환경 설정 ✅ (완료)
- [x] Python 프로젝트 구조 생성 (`src/`, `tests/`, `data/`)
- [x] Playwright 기반 자동 다운로드 구현
- [x] 설정 파일 관리 (pydantic-settings)
- [x] 기본 문서화 (AGENTS.md, CLAUDE.md)

### Phase 2: Excel 파일 분석 및 데이터 구조 파악 ✅ (완료)
- [x] 템플릿 Excel 파일 구조 분석
- [x] Shiftee 다운로드 파일 구조 분석
- [x] 시트 간 수식 관계 파악
- [x] 데이터 매핑 요구사항 정리

### Phase 3: Excel 데이터 처리 모듈 개발 ✅ (완료 - 2025-12-13)
**목표**: Shiftee 다운로드 파일을 읽어서 템플릿에 삽입하는 기능 구현

#### 3.1 Excel 읽기/쓰기 기본 모듈 ✅
- [x] `src/shiftee/excel_processor.py` 생성 (221 lines)
  - [x] Excel 파일 읽기 함수 (openpyxl + pandas)
  - [x] Excel 시트 복사 함수 (수식 보존)
  - [x] 데이터 삽입 함수 (기존 수식 유지)
  - [x] Context manager 지원
  - [x] DataFrame ↔ Excel 양방향 변환
  - [x] 시트 데이터 삭제 (수식 보존)

**구현 세부사항**:
- `ExcelProcessor` 클래스: openpyxl 기반 Excel 처리
- `load_workbook(data_only=False)`: 수식 보존 모드
- `write_dataframe_to_sheet()`: DataFrame을 시트에 안전하게 삽입
- `clear_sheet_data()`: 수식은 유지하고 데이터만 삭제
- Helper 함수: `load_excel()`, `read_excel_to_dataframe()`

#### 3.2 템플릿 관리 모듈 ✅
- [x] `src/shiftee/template.py` 생성 (170 lines)
  - [x] 템플릿 파일 로드 함수
  - [x] 템플릿 검증 함수 (필수 시트 존재 확인)
  - [x] 새 템플릿 인스턴스 생성 함수
  - [x] 시트 정보 조회 기능
  - [x] 데이터 시트 초기화 기능

**구현 세부사항**:
- `TemplateManager` 클래스: 템플릿 검증 및 관리
- 필수 시트 검증: 작성법, shiftee데이타, shiftee데이타2, 계산, 정리, 공지용
- 컬럼 수 검증: shiftee데이타(25개), shiftee데이타2(47개)
- `create_instance()`: 템플릿 복사하여 새 인스턴스 생성
- `clear_data_sheets()`: 데이터 시트 초기화 (헤더 보존)

#### 3.3 데이터 매핑 모듈 ✅
- [x] `src/shiftee/data_mapper.py` 생성 (289 lines)
  - [x] REALTIME-REPORT → shiftee데이타 매핑 함수
    - [x] 날짜 범위 패턴으로 시트명 동적 찾기 (regex: `\d{8}-\d{8}`)
    - [x] 25개 컬럼 매핑 및 검증
  - [x] PAYROLL → shiftee데이타2 매핑 함수
    - [x] Header 행 처리 (3번째 행이 실제 헤더, index=2)
    - [x] 47개 컬럼 매핑 및 검증
  - [x] 직원 데이터 일치성 검증 (두 파일 간 직원 목록 비교)
  - [x] 최신 파일 자동 찾기 기능
  - [x] 통합 매핑 함수 (`map_all_data()`)

**구현 세부사항**:
- `ShifteeDataMapper` 클래스: 데이터 로드 및 매핑
- 동적 시트 감지: 정규표현식 패턴 매칭
- `validate_data_consistency()`: 직원 목록 일치성 검증
- `find_latest_shiftee_files()`: data 디렉토리에서 최신 파일 자동 찾기
- 검증 결과 리포트: 누락된 직원 자동 감지

**테스트 결과**:
- ✅ ExcelProcessor: 기본 읽기/쓰기 기능 검증
- ✅ TemplateManager: 템플릿 검증 및 인스턴스 생성
- ✅ DataMapper: 데이터 로드 및 매핑
- ✅ Full Workflow: 전체 통합 테스트 통과
- ⚠️ 데이터 일치성: PAYROLL에 없는 직원 5명 감지 (정상 - 기간 차이)

**주요 발견사항**:
- PAYROLL 파일 헤더: 3번째 행(index 2)에 위치
- shiftee데이타2 구조: 1행(메타), 2행(더미), 3행(헤더), 4행부터 데이터
- 직원 불일치: 서정우, 박성호, 최성민, 우상민, 허지행 (REALTIME에만 존재)

### Phase 4: Excel 생성 자동화 ✅ (완료: 2025-12-13)
**목표**: 데이터 삽입 후 계산 시트 자동 갱신 및 결과 생성

#### 4.1 메인 처리 로직 ✅
- [x] `src/shiftee/report_generator.py` 생성 (153 lines)
  - [x] `ReportGenerator` 클래스: 전체 보고서 생성 워크플로우 관리
  - [x] 템플릿 복사 및 초기화
  - [x] shiftee데이타 시트 업데이트 (REALTIME-REPORT 데이터)
  - [x] shiftee데이타2 시트 업데이트 (PAYROLL 데이터)
  - [x] Excel 수식 재계산 활성화 (`fullCalcOnLoad=True`)
  - [x] 최종 파일 저장 및 검증
  - [x] `generate_report()` 헬퍼 함수: 간편한 보고서 생성

#### 4.2 결과 검증 모듈 ✅
- [x] `src/shiftee/validator.py` 생성 (291 lines)
  - [x] `ReportValidator` 클래스: 생성된 보고서 검증
  - [x] 시트 구조 검증 (필수 시트 존재 확인)
  - [x] 데이터 시트 검증 (shiftee데이타: 130행, shiftee데이타2: 2541행)
  - [x] 계산 시트 검증 (계산: 4578개 수식, 정리: 6444개 수식)
  - [x] 공지용 시트 검증 (선택적, Excel에서 수동 처리)
  - [x] `validate_report()` 헬퍼 함수: 간편한 검증 실행

#### 4.3 Excel 수식 재계산 기능 ✅
- [x] `ExcelProcessor.enable_formula_recalculation()` 메서드 추가
  - [x] `calcMode = "auto"` 설정
  - [x] `fullCalcOnLoad = True` 설정
  - [x] Excel 파일 열 때 자동 재계산 활성화

**구현 세부사항**:
- 전체 워크플로우: 템플릿 로드 → 인스턴스 생성 → 데이터 매핑 → 검증 → 저장
- 경고 처리: 데이터 불일치를 경고로 처리하고 매핑은 계속 진행
- 검증 결과: 시트 구조, 데이터 시트, 계산 시트 모두 통과
- 공지용 시트: Excel에서 수동으로 정리 시트를 필터/복사하거나 VBA 매크로로 생성

**테스트 결과**:
- ✅ 템플릿 로드 및 검증
- ✅ 데이터 매핑 (shiftee데이타: 130행, shiftee데이타2: 2541행)
- ✅ 계산 시트 수식 보존 (계산: 4578개, 정리: 6444개)
- ✅ Excel 수식 재계산 활성화
- ✅ 전체 검증 통과
- ⚠️ 공지용 시트: Excel에서 열어서 확인 필요

**주요 발견사항**:
- 공지용 시트: 수식이 아니라 정리 시트의 결과를 수동 복사/VBA로 생성
- Excel 재계산: openpyxl로 재계산 플래그 설정, Excel에서 열면 자동 계산
- 검증 선택성: 공지용 시트는 선택적 검증 (`validate_notice=False` 기본값)

### Phase 5: CLI 통합 및 워크플로우 자동화 ✅ (완료: 2025-12-13)
**목표**: 전체 프로세스를 하나의 명령으로 실행 가능하게 구성

#### 5.1 메인 CLI 진입점 ✅
- [x] `shiftee_analysis.py` 메인 진입점 생성
  - [x] `python shiftee_analysis.py [명령어]` 실행 구조
  - [x] 4가지 서브 커맨드 구현: `full`, `download`, `generate`, `validate`
  - [x] `src/shiftee/cli.py` - argparse 기반 CLI 로직 모듈 (320 lines)
  - [x] `src/shiftee/__main__.py` 수정 - CLI로 리다이렉트

#### 5.2 워크플로우 통합 모듈 ✅
- [x] `src/shiftee/workflow.py` 생성 (264 lines)
  - [x] `WorkflowConfig` 클래스: 워크플로우 설정 관리
  - [x] `ShifteeWorkflow` 클래스: 전체 워크플로우 자동화
  - [x] Step 1: Shiftee 로그인 및 다운로드
  - [x] Step 2: 다운로드된 파일 자동 검색 (`find_latest_shiftee_files`)
  - [x] Step 3: Excel 템플릿 처리 및 데이터 삽입
  - [x] Step 4: 결과 파일 저장 및 검증
  - [x] Step 5: 성공/실패 리포트 생성

#### 5.3 CLI 명령어 상세 ✅
- [x] **`full`**: 전체 워크플로우 (다운로드 + 생성)
  - [x] `--template`: 템플릿 파일 경로 (필수)
  - [x] `--output`: 출력 파일 경로
  - [x] `--skip-download`: 다운로드 건너뛰기
  - [x] `--overwrite`: 덮어쓰기
  - [x] `--no-validate`: 검증 건너뛰기
  - [x] `--headless` / `--no-headless`: 브라우저 모드

- [x] **`download`**: 데이터 다운로드만
  - [x] `--data-dir`: 다운로드 디렉터리
  - [x] `--headless` / `--no-headless`: 브라우저 모드

- [x] **`generate`**: 보고서 생성만
  - [x] `--template`: 템플릿 파일 경로 (필수)
  - [x] `--realtime` / `--payroll`: 파일 경로 직접 지정
  - [x] `--output`: 출력 파일 경로
  - [x] `--data-dir`: 자동 검색 디렉터리
  - [x] `--overwrite`: 덮어쓰기
  - [x] `--no-validate`: 검증 건너뛰기

- [x] **`validate`**: 보고서 검증만
  - [x] `report`: 검증할 파일 경로 (위치 인자)
  - [x] `--validate-notice`: 공지용 시트도 검증

- [x] **공통 옵션**
  - [x] `-v` / `--verbose`: 상세 로깅
  - [x] `-q` / `--quiet`: 최소 로깅
  - [x] `--config`: 설정 파일 경로

#### 5.4 문서화 ✅
- [x] `README.md` 생성
  - [x] 설치 및 설정 가이드
  - [x] 모든 명령어 사용법 및 예시
  - [x] 프로젝트 구조 설명
  - [x] 워크플로우 다이어그램
  - [x] 문제 해결 가이드

**테스트 결과**:
```bash
# 보고서 생성 테스트
python shiftee_analysis.py generate --template template.xlsx --output test.xlsx --overwrite
# ✅ 성공: 2초 이내 완료, 모든 검증 통과

# 검증 테스트
python shiftee_analysis.py validate test.xlsx
# ✅ 성공: shiftee데이타 130행, shiftee데이타2 2541행, 계산 4578개 수식, 정리 6444개 수식
```

**주요 기능**:
- 전체 워크플로우 자동화: 로그인 → 다운로드 → 생성 → 검증
- 유연한 명령어 구조: 필요한 단계만 선택 실행 가능
- 자동 파일 검색: data 디렉터리에서 최신 파일 자동 감지
- 진행 상황 로깅: INFO 레벨로 모든 단계 추적
- 에러 핸들링: 각 단계별 실패 시 명확한 오류 메시지

### Phase 6: 테스트 및 검증
**목표**: 안정적인 동작 보장

#### 6.1 단위 테스트 ✅
- [x] `tests/test_excel_processor.py` (33 tests)
  - [x] Excel 읽기/쓰기 테스트
  - [x] 수식 보존 테스트
  - [x] DataFrame 변환 테스트
  - [x] Context manager 테스트
  - [x] 헬퍼 함수 테스트
  - [x] 엣지 케이스 테스트 (NaN 처리, 헤더 포함 등)
- [x] `tests/test_data_mapper.py` (16 tests)
  - [x] 데이터 매핑 정확성 테스트
  - [x] 컬럼 매칭 테스트
  - [x] 데이터 일치성 검증 테스트
  - [x] find_latest_shiftee_files 헬퍼 함수 테스트
  - [x] 엣지 케이스 테스트 (누락된 컬럼 등)
- [x] `tests/test_report_generator.py` (14 tests)
  - [x] 전체 생성 프로세스 테스트
  - [x] 템플릿 검증 테스트
  - [x] 에러 핸들링 테스트
  - [x] 통합 워크플로우 테스트
- [x] `pytest.ini` 설정 파일 생성
- [x] `tests/__init__.py` 테스트 패키지 초기화

**테스트 결과**:
```bash
pytest tests/ -v
# ✅ 47 tests passed in 0.70s
# - 33 tests: test_excel_processor.py
# - 16 tests: test_data_mapper.py
# - 14 tests: test_report_generator.py
```

**테스트 커버리지**:
- ExcelProcessor: 모든 public 메서드 및 헬퍼 함수
- ShifteeDataMapper: 데이터 로딩, 검증, 매핑 기능 전체
- ReportGenerator: 전체 생성 워크플로우 및 에러 처리
- 엣지 케이스: NaN 처리, 파일 없음, 데이터 불일치 등

#### 6.2 통합 테스트 ✅
- [x] `tests/test_integration.py` (15 tests)
  - [x] End-to-End 워크플로우 테스트
  - [x] 데이터 매핑 통합 테스트
  - [x] 파일 검색 통합 테스트
  - [x] 에러 핸들링 테스트
  - [x] 다양한 월/기간 데이터 테스트
  - [x] 성능 테스트 (10초 이내 생성, 5초 이내 검증)

**테스트 결과**:
```bash
pytest tests/test_integration.py -v
# ✅ 15 tests passed in 12.84s
# - TestEndToEndWorkflow: 3 tests
# - TestDataMapping: 2 tests
# - TestFileDiscovery: 2 tests
# - TestErrorHandling: 4 tests
# - TestMonthlyDataVariations: 2 tests
# - TestPerformance: 2 tests
```

**테스트 커버리지**:
- 실제 Shiftee 다운로드 파일 사용
- 완전한 워크플로우: 로드 → 매핑 → 생성 → 검증
- 에러 케이스: 파일 없음, 잘못된 템플릿 구조, 검증 실패
- 성능 벤치마크: 보고서 생성 10초, 검증 5초 제한

### Phase 7: 문서화 및 배포 준비 ✅ (완료: 2025-12-14)
**목표**: 사용 가이드 및 유지보수 문서 작성

#### 7.1 사용자 문서 ✅
- [x] `docs/usage_guide.md` 작성 (300+ lines)
  - [x] 전체 워크플로우 설명 (ASCII 다이어그램 포함)
  - [x] 4가지 CLI 명령어 사용 예시 (full, download, generate, validate)
  - [x] 트러블슈팅 가이드 (로그인/다운로드/생성/검증/성능 문제)
  - [x] FAQ 섹션 (10개 항목)
  - [x] Python API 사용 예시
- [x] `README.md` 업데이트
  - [x] 공지용 시트 생성 섹션 추가
    - [x] 자동 생성 방법 (Excel 수식)
    - [x] 수동 작성 방법 (필터링 및 복사)
    - [x] VBA 매크로 예시 코드
    - [x] 주요 확인 항목 체크리스트

#### 7.2 개발자 문서 ✅
- [x] `docs/excel_structure.md` 작성 (400+ lines)
  - [x] 템플릿 Excel 구조 상세 설명
    - [x] 6개 시트 구조 및 역할 테이블
    - [x] shiftee데이타 25개 컬럼 상세 정의
    - [x] shiftee데이타2 47개 컬럼 및 헤더 구조
  - [x] 수식 로직 문서화
    - [x] 계산 시트 수식 예시 (SUMPRODUCT 등)
    - [x] 정리 시트 참조 관계
    - [x] 적정성 판단 로직 (IF 조건문)
  - [x] 데이터 매핑 상세 정보
    - [x] 동적 시트명 찾기 (정규표현식)
    - [x] 헤더 행 처리 (PAYROLL의 header=2)
    - [x] 데이터 흐름 다이어그램
    - [x] 코드 구현 예시

#### 7.3 자동화 스크립트 ✅
- [x] `scripts/monthly_report.sh` (월말 자동 실행용, 303 lines)
  - [x] 전체 워크플로우 자동화
    - [x] 환경 변수 로드 (.env 파일)
    - [x] 템플릿/Python 환경 검증
    - [x] Shiftee 다운로드 → Excel 생성
  - [x] 로깅 시스템
    - [x] 날짜별 로그 파일 생성
    - [x] INFO/WARN/ERROR/SUCCESS 레벨
    - [x] 에러 핸들러 (trap)
  - [x] 이메일 발송 (선택적)
    - [x] SEND_EMAIL 환경 변수 제어
    - [x] 보고서 첨부 및 실행 요약
  - [x] 자동 정리
    - [x] 오래된 로그 파일 삭제 (CLEANUP_DAYS)
    - [x] 오래된 보고서 삭제 (선택적)
  - [x] Cron 설정 예시 주석 포함
    - [x] `0 0 1 * *` (매월 1일 자정 실행)

**문서화 결과**:
- ✅ 사용자 가이드: 설치부터 트러블슈팅까지 완전한 사용법
- ✅ 개발자 문서: Excel 구조 및 수식 로직 상세 분석
- ✅ 자동화 스크립트: 프로덕션급 월말 보고서 자동 생성
- ✅ README 업데이트: 공지용 시트 생성 방법 3가지 제시

**주요 문서**:
- `docs/usage_guide.md`: End-user 가이드 (설치, 명령어, FAQ)
- `docs/excel_structure.md`: Developer 레퍼런스 (구조, 수식, 매핑)
- `scripts/monthly_report.sh`: 월말 자동화 스크립트 (로깅, 이메일, 정리)
- `README.md`: 프로젝트 개요 및 빠른 시작 가이드

## 우선순위 및 추정 기간

### 우선순위 High (1-2주)
1. Phase 3: Excel 데이터 처리 모듈 개발
2. Phase 4: Excel 생성 자동화
3. Phase 5.1: CLI 통합

### 우선순위 Medium (1주)
4. Phase 5.2: 통합 워크플로우
5. Phase 6.1: 단위 테스트

### 우선순위 Low (선택적)
6. Phase 6.2: 통합 테스트
7. Phase 7: 문서화

## 기술 스택 추가 요구사항

### Python 패키지 ✅ (requirements.txt 업데이트 완료)
```txt
pydantic>=2.4              # 설정 관리
pydantic-settings>=2.2     # 환경변수 설정
playwright>=1.40           # 브라우저 자동화
pandas>=2.0.0              # 데이터 처리
openpyxl>=3.1.0            # Excel 수식 보존 읽기/쓰기
python-dateutil>=2.8.0     # 날짜/시간 처리
```

## 주요 고려사항

### 기술적 고려사항 (Phase 3 적용 완료)
1. **수식 보존**: ✅ openpyxl을 사용하여 템플릿의 수식을 보존하면서 데이터만 업데이트
2. **동적 시트명**: ✅ REALTIME-REPORT의 시트명이 날짜 범위로 동적 생성됨 (regex 패턴 `\d{8}-\d{8}` 사용)
3. **헤더 행 처리**: ✅ shiftee데이타2는 3번째 행이 실제 컬럼 헤더 (index=2)
   - 1행: 메타데이터 (날짜 범위 등)
   - 2행: 더미 데이터
   - 3행: 실제 헤더
   - 4행부터: 데이터
4. **Excel 재계산**: 데이터 삽입 후 Excel의 자동 계산 기능 활성화 필요 (Phase 4에서 구현 예정)

### 비즈니스 로직
1. **공지용 기준**: "위험" 또는 "법기준초과" 대상자만 표시
2. **월말까지 가능시간**: 52시간 - 실제 초과근로시간 계산
3. **적정성 판단**: 법규 위반 여부에 따른 상태 표시
4. **월요일 대상자**: 특정 임계값 기준 필터링 (추가 분석 필요)

### 데이터 품질
1. 두 파일의 직원 목록 일치성 검증
2. 날짜 범위 일치성 확인
3. 필수 컬럼 존재 여부 검증
4. 이상치 데이터 감지 및 알림

## 참고 파일

### 템플릿 및 데이터
- 템플릿: `/Users/ryancho/Downloads/레포트_20251101-1130_뱅킹인프라본부_정문현 (1).xlsx`
- 현재 다운로드 위치: `data/SHIFTEE-*.xlsx`
- 테스트 결과: `data/test_output.xlsx`, `data/test_result.xlsx`

### 구현된 모듈 (Phase 3)
- `src/shiftee/excel_processor.py` (221 lines) - Excel 읽기/쓰기 기본 모듈
- `src/shiftee/template.py` (170 lines) - 템플릿 관리 모듈
- `src/shiftee/data_mapper.py` (289 lines) - 데이터 매핑 모듈

### 기존 모듈 (Phase 1)
- `src/shiftee/login.py` - Playwright 기반 로그인
- `src/shiftee/attendance.py` - 리포트 다운로드 (REALTIME, PAYROLL)
- `src/shiftee/settings.py` - pydantic-settings 기반 설정 관리
