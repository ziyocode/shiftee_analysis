# 변경 이력 (Changelog)

이 프로젝트의 주요 변경 사항을 기록합니다.

## [1.0.1] - 2026-06-30

### 수정 (Fixed)
- **헤드리스 봇 감지 우회**: 신규 Shiftee `/app` SPA가 헤드리스(WSL 포함) 환경에서
  자동화를 감지하면 로딩 스피너에서 멈추던 문제 해결. 실제 데스크톱 Chrome처럼
  위장(User-Agent, `locale=ko-KR`, `timezone=Asia/Seoul`, 뷰포트, `navigator.webdriver`
  마스킹)하여 정상 부팅하도록 수정 (`login.py`).
- **실급여정산 다운로드 멈춤**: 모달의 "모두 선택"이 토글이고 직원이 진입 시 이미
  전체 선택돼 있어, 기존 코드가 한 번 클릭해 전체를 해제 → 직원 0명으로 다운로드
  버튼이 비활성인 채 720초 타임아웃으로 실패하던 문제 해결. 클릭 후 선택이 해제되면
  다시 눌러 전체 선택을 보장하도록 수정 (`attendance.py`).

## [1.0.0] - 2026-06

### 추가 (Added)
- Windows `.exe` 배포 지원 (PyInstaller + GitHub Actions 자동 빌드/릴리스)
- GUI 로그인 화면 및 HTML 리포트 생성
