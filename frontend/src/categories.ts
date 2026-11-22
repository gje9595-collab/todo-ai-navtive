// 카테고리 정의 (FR-013, FR-014, PRD D-9). 서버 허용값과 화면 라벨을 한곳에서 관리한다.

export type Category = 'work' | 'personal' | 'study'

/** 필터 값. 'all'은 전체 보기 */
export type CategoryFilter = Category | 'all'

/** 화면 표시 순서와 라벨 */
export const CATEGORIES: ReadonlyArray<{ value: Category; label: string }> = [
  { value: 'work', label: '업무' },
  { value: 'personal', label: '개인' },
  { value: 'study', label: '학습' },
]

export const DEFAULT_CATEGORY: Category = 'personal'

export const CATEGORY_LABEL: Record<Category, string> = {
  work: '업무',
  personal: '개인',
  study: '학습',
}

export function isCategory(value: string): value is Category {
  return Object.hasOwn(CATEGORY_LABEL, value)
}

/** 필터별 할 일 개수. 상태로 저장하지 않고 todos에서 계산한다 (CLAUDE.md 6-1). */
export function countByCategory(categories: Category[]): Record<CategoryFilter, number> {
  const counts: Record<CategoryFilter, number> = { all: categories.length, work: 0, personal: 0, study: 0 }
  for (const category of categories) counts[category] += 1
  return counts
}
