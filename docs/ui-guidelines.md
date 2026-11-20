## UI Design Rules

- 모든 UI 개발 시 docs/ui-guidelines.md를 참조한다.
- 새로운 컴포넌트는 정의된 Color, Typography, Spacing 규칙을 따른다.
- TaskCard와 TaskForm은 공통 디자인 토큰을 사용한다.
- 반응형 UI와 키보드 접근성을 반드시 고려한다.
- UI 변경 시 docs/ui-guidelines.md를 함께 업데이트한다.
- 기존 CRUD 기능을 유지하고 변경 후 테스트한다.

## 알림 (Notice)

- API 오류는 입력창 위의 알림(`.notice`, `role="alert"`)으로 안내한다.
- 색상은 `--danger` / `--danger-soft` 토큰만 사용한다.
- 메시지는 "무엇이 실패했는지 + 서버 메시지" 순서로 쓴다. (예: "할 일을 추가하지 못했습니다. 할 일 내용을 입력해 주세요.")
- 목록을 불러오지 못한 경우에는 "다시 시도", 그 외에는 "닫기" 버튼을 둔다.
- 목록을 불러오는 중이거나 실패한 상태에서는 입력창과 추가 버튼을 비활성화한다.