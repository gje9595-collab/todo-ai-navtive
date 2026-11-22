// `/api/todos` 호출과 서버 응답(snake_case) → 프론트 `Todo` 변환 (api-spec 3절).

import { DEFAULT_CATEGORY, type Category } from '../categories'
import type { Todo } from '../types'
import { apiRequest } from './client'

interface TodoDto {
  id: string
  text: string
  completed: boolean
  due_date: string | null
  category: Category
  created_at: string
  updated_at: string
}

interface TodoListDto {
  items: TodoDto[]
}

/** 부분 수정. `dueDate: null`은 마감일 지우기, 생략은 유지 (api-spec 3-4, FR-012, FR-013). */
export type TodoPatch = Partial<Pick<Todo, 'text' | 'completed' | 'dueDate' | 'category'>>

const toTodo = (dto: TodoDto): Todo => ({
  id: dto.id,
  text: dto.text,
  completed: dto.completed,
  // 이전 서버(v2.0)는 due_date를 보내지 않으므로 없으면 null로 본다.
  dueDate: dto.due_date ?? null,
  // 이전 서버(v2.1)는 category를 보내지 않으므로 기본값으로 본다 (D-9).
  category: dto.category ?? DEFAULT_CATEGORY,
})

/** 정의된 필드만 snake_case 본문으로 옮긴다. 서버는 정의되지 않은 필드를 422로 거부한다. */
function toPatchBody(patch: TodoPatch): Record<string, unknown> {
  const body: Record<string, unknown> = {}
  if (patch.text !== undefined) body.text = patch.text
  if (patch.completed !== undefined) body.completed = patch.completed
  if (patch.dueDate !== undefined) body.due_date = patch.dueDate
  if (patch.category !== undefined) body.category = patch.category
  return body
}

/** 전체 목록을 받는다. 화면은 이 목록을 브라우저에서 거른다 (PRD D-10). */
export async function fetchTodos(): Promise<Todo[]> {
  const data = await apiRequest<TodoListDto>('/todos')
  return data.items.map(toTodo)
}

export async function createTodo(
  text: string,
  dueDate: string | null = null,
  category: Category = DEFAULT_CATEGORY,
): Promise<Todo> {
  const json = dueDate === null ? { text, category } : { text, due_date: dueDate, category }
  return toTodo(await apiRequest<TodoDto>('/todos', { method: 'POST', json }))
}

export async function updateTodo(id: string, patch: TodoPatch): Promise<Todo> {
  return toTodo(await apiRequest<TodoDto>(`/todos/${id}`, { method: 'PATCH', json: toPatchBody(patch) }))
}

export async function deleteTodo(id: string): Promise<void> {
  await apiRequest<void>(`/todos/${id}`, { method: 'DELETE' })
}
