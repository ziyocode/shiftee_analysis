"""GUI 로그인 창 모듈.

tkinter를 사용한 간단한 로그인 인터페이스.
Windows에서도 별도 설치 없이 동작합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple
from pathlib import Path
import json


class LoginDialog:
    """로그인 정보를 입력받는 GUI 대화상자."""

    # 팀 목록
    TEAMS = [
        "인프라 본부",
        "뱅킹IS팀",
        "뱅킹정보IS팀",
        "뱅킹통신보안팀",
        "인프라SRE팀",
        "카드IS팀",
        "증권IS팀",
        "라이프IS팀",
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Shiftee 로그인")
        self.root.geometry("500x680")
        self.root.resizable(False, False)

        # 결과 (아이디, 비밀번호, 팀필터, 브라우저표시여부)
        self.result: Optional[Tuple[str, str, list[str], bool]] = None

        # 설정 파일 경로
        self.config_file = Path("shiftee_config.json")

        # 팀 체크박스 변수
        self.team_vars = {}

        self._create_widgets()
        self._load_saved_credentials()
        self._center_window()

    def _center_window(self):
        """창을 화면 중앙에 배치."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """UI 구성 요소 생성."""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 제목
        title_label = ttk.Label(
            main_frame,
            text="Shiftee 로그인 정보",
            font=("맑은 고딕", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 아이디
        ttk.Label(main_frame, text="아이디:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.id_entry = ttk.Entry(main_frame, width=35)
        self.id_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=tk.W)

        # 비밀번호
        ttk.Label(main_frame, text="비밀번호:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, width=35, show="*")
        self.password_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=tk.W)

        # 구분선
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15
        )

        # 팀 필터 섹션
        team_label = ttk.Label(
            main_frame,
            text="분석 대상 팀 선택",
            font=("맑은 고딕", 11, "bold")
        )
        team_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 팀 선택 프레임 (스크롤 가능)
        team_frame_container = ttk.Frame(main_frame)
        team_frame_container.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Canvas와 Scrollbar
        canvas = tk.Canvas(team_frame_container, height=200, highlightthickness=1, highlightbackground="#ccc")
        scrollbar = ttk.Scrollbar(team_frame_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 전체 선택/해제 버튼
        select_all_frame = ttk.Frame(scrollable_frame)
        select_all_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(
            select_all_frame,
            text="전체 선택",
            command=self._select_all_teams,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            select_all_frame,
            text="전체 해제",
            command=self._deselect_all_teams,
            width=15
        ).pack(side=tk.LEFT)

        # 팀 체크박스 생성
        for team in self.TEAMS:
            var = tk.BooleanVar(value=False)
            self.team_vars[team] = var

            cb = ttk.Checkbutton(
                scrollable_frame,
                text=team,
                variable=var
            )
            cb.pack(anchor=tk.W, padx=20, pady=3)

        # 안내 문구
        ttk.Label(
            main_frame,
            text="※ 선택하지 않으면 전체 직원을 분석합니다",
            font=("맑은 고딕", 8),
            foreground="gray"
        ).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 저장 체크박스
        self.save_var = tk.BooleanVar(value=True)
        save_check = ttk.Checkbutton(
            main_frame,
            text="로그인 정보 저장 (비밀번호 제외)",
            variable=self.save_var
        )
        save_check.grid(row=7, column=0, columnspan=2, pady=(5, 5))

        # 브라우저 표시 체크박스 (문제 해결용: 헤드리스에서 로그인 후 화면이 안 뜰 때)
        self.show_browser_var = tk.BooleanVar(value=False)
        show_browser_check = ttk.Checkbutton(
            main_frame,
            text="브라우저 창 표시 (다운로드가 멈추거나 실패할 때 체크)",
            variable=self.show_browser_var
        )
        show_browser_check.grid(row=8, column=0, columnspan=2, pady=(0, 5))

        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(10, 0))

        login_btn = ttk.Button(button_frame, text="로그인", command=self._on_login, width=12)
        login_btn.grid(row=0, column=0, padx=5)

        cancel_btn = ttk.Button(button_frame, text="취소", command=self._on_cancel, width=12)
        cancel_btn.grid(row=0, column=1, padx=5)

        # Enter 키 바인딩
        self.root.bind('<Return>', lambda e: self._on_login())
        self.root.bind('<Escape>', lambda e: self._on_cancel())

        # 첫 번째 빈 필드에 포커스
        self.id_entry.focus()

    def _select_all_teams(self):
        """모든 팀 선택."""
        for var in self.team_vars.values():
            var.set(True)

    def _deselect_all_teams(self):
        """모든 팀 선택 해제."""
        for var in self.team_vars.values():
            var.set(False)

    def _load_saved_credentials(self):
        """저장된 로그인 정보 불러오기."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.id_entry.insert(0, config.get('id', ''))

            # 저장된 팀 선택 복원
            saved_teams = config.get('teams', [])
            for team in saved_teams:
                if team in self.team_vars:
                    self.team_vars[team].set(True)

            # 아이디가 저장되어 있으면 비밀번호 필드에 포커스
            if config.get('id'):
                self.password_entry.focus()

        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")

    def _save_credentials(self, user_id: str, teams: list[str]):
        """로그인 정보 저장 (비밀번호 제외)."""
        try:
            config = {
                'id': user_id,
                'teams': teams,
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    def _on_login(self):
        """로그인 버튼 클릭 시."""
        user_id = self.id_entry.get().strip()
        password = self.password_entry.get().strip()

        if not user_id:
            messagebox.showwarning("입력 오류", "아이디를 입력해주세요.")
            self.id_entry.focus()
            return

        if not password:
            messagebox.showwarning("입력 오류", "비밀번호를 입력해주세요.")
            self.password_entry.focus()
            return

        # 선택된 팀 목록 가져오기
        selected_teams = [team for team, var in self.team_vars.items() if var.get()]

        # 저장 옵션 처리
        if self.save_var.get():
            self._save_credentials(user_id, selected_teams)

        show_browser = self.show_browser_var.get()
        self.result = (user_id, password, selected_teams, show_browser)
        self.root.quit()
        self.root.destroy()

    def _on_cancel(self):
        """취소 버튼 클릭 시."""
        self.root.quit()
        self.root.destroy()

    def show(self) -> Optional[Tuple[str, str, list[str], bool]]:
        """대화상자를 표시하고 결과 반환.

        Returns:
            (아이디, 비밀번호, 팀필터리스트, 브라우저표시여부) 튜플 또는 None (취소 시)
        """
        self.root.mainloop()
        return self.result


def get_credentials() -> Optional[Tuple[str, str, list[str], bool]]:
    """GUI를 통해 로그인 정보를 입력받습니다.

    Returns:
        (user_id, password, team_filter_list, show_browser) 또는 None (취소 시)
    """
    dialog = LoginDialog()
    return dialog.show()


if __name__ == "__main__":
    # 테스트용
    result = get_credentials()
    if result:
        user_id, password, teams, show_browser = result
        print(f"ID: {user_id}")
        print(f"Show browser: {show_browser}")
        print(f"Password: {'*' * len(password)}")
        print(f"Teams: {teams}")
    else:
        print("로그인이 취소되었습니다.")
