import type { Category } from './categories'

/** 할 일 한 건 */
export interface Todo {
  id: string
  text: string
  completed: boolean
  /** 마감일 `YYYY-MM-DD`(시각 없음). 없으면 null (FR-012, PRD D-8) */
  dueDate: string | null
  /** 업무·개인·학습 중 하나 (FR-013) */
  category: Category
}
