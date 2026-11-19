import type { Todo } from './types'

// 개발 서버에서 `?demo` 로 접속하면 샘플 할 일을 채워 UI를 확인할 수 있습니다.
// 프로덕션 빌드에서는 항상 빈 목록으로 시작합니다.
const samples: Array<[string, boolean]> = [
  ['주간 회의 안건 정리', true],
  ['디자인 리뷰 피드백 반영', true],
  ['API 명세 초안 작성', false],
  ['Supabase 테이블 설계', false],
  ['배포 체크리스트 확인', false],
]

export function getInitialTodos(): Todo[] {
  if (!import.meta.env.DEV) return []
  if (!new URLSearchParams(window.location.search).has('demo')) return []
  return samples.map(([text, completed]) => ({ id: crypto.randomUUID(), text, completed }))
}
