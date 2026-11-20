// `/api/todos` 엔드포인트 호출과 서버 응답(snake_case) → 프론트 `Todo` 변환.

import type { Todo } from '../types'
import { apiRequest } from './client'

interface TodoDto {
  id: string
  text: string
  completed: boolean
  created_at: string
  updated_at: string
}

interface TodoListDto {
  items: TodoDto[]
}

export type TodoPatch = Partial<Pick<Todo, 'text' | 'completed'>>

const toTodo = (dto: TodoDto): Todo => ({ id: dto.id, text: dto.text, completed: dto.completed })

export async function fetchTodos(): Promise<Todo[]> {
  const data = await apiRequest<TodoListDto>('/todos')
  return data.items.map(toTodo)
}

export async function createTodo(text: string): Promise<Todo> {
  return toTodo(await apiRequest<TodoDto>('/todos', { method: 'POST', json: { text } }))
}

export async function updateTodo(id: string, patch: TodoPatch): Promise<Todo> {
  return toTodo(await apiRequest<TodoDto>(`/todos/${id}`, { method: 'PATCH', json: patch }))
}

export async function deleteTodo(id: string): Promise<void> {
  await apiRequest<void>(`/todos/${id}`, { method: 'DELETE' })
}
