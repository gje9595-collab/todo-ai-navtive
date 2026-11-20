import { useEffect, useRef, useState } from 'react'
import { ApiError, getErrorMessage } from './api/client'
import * as todoApi from './api/todos'
import ProgressMeter from './components/ProgressMeter'
import TodoInput from './components/TodoInput'
import TodoItem from './components/TodoItem'
import type { Todo } from './types'

type LoadState = 'loading' | 'ready' | 'error'

export default function App() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [reloadKey, setReloadKey] = useState(0)
  const [notice, setNotice] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // 목록 조회 (FR-002). StrictMode의 이중 실행이나 재시도 시 늦게 도착한 응답은 무시합니다.
  useEffect(() => {
    let ignore = false
    todoApi
      .fetchTodos()
      .then((items) => {
        if (ignore) return
        setTodos(items)
        setLoadState('ready')
      })
      .catch((error: unknown) => {
        if (ignore) return
        setNotice(getErrorMessage(error))
        setLoadState('error')
      })
    return () => {
      ignore = true
    }
  }, [reloadKey])

  const retryLoad = () => {
    setNotice(null)
    setLoadState('loading')
    setReloadKey((key) => key + 1)
  }

  const replaceTodo = (id: string, update: (todo: Todo) => Todo) => {
    setTodos((prev) => prev.map((todo) => (todo.id === id ? update(todo) : todo)))
  }

  // 생성은 서버가 발급한 id가 필요하므로 응답을 받은 뒤 목록에 추가합니다 (FR-001).
  const addTodo = async (text: string): Promise<boolean> => {
    try {
      const created = await todoApi.createTodo(text)
      setTodos((prev) => [...prev, created])
      setNotice(null)
      inputRef.current?.focus()
      return true
    } catch (error) {
      setNotice(`할 일을 추가하지 못했습니다. ${getErrorMessage(error)}`)
      return false
    }
  }

  // 완료 토글/텍스트 수정: 화면을 먼저 바꾸고, 실패하면 이전 값으로 되돌립니다 (NFR-006).
  const patchTodo = (id: string, patch: todoApi.TodoPatch, failMessage: string) => {
    const previous = todos.find((todo) => todo.id === id)
    if (!previous) return

    replaceTodo(id, (todo) => ({ ...todo, ...patch }))
    todoApi
      .updateTodo(id, patch)
      .then((saved) => replaceTodo(id, () => saved))
      .catch((error: unknown) => {
        replaceTodo(id, (todo) => ({
          ...todo,
          ...(patch.text !== undefined && { text: previous.text }),
          ...(patch.completed !== undefined && { completed: previous.completed }),
        }))
        setNotice(`${failMessage} ${getErrorMessage(error)}`)
      })
  }

  const toggleTodo = (id: string) => {
    const target = todos.find((todo) => todo.id === id)
    if (target) patchTodo(id, { completed: !target.completed }, '완료 상태를 바꾸지 못했습니다.')
  }

  const updateTodoText = (id: string, text: string) => {
    patchTodo(id, { text }, '할 일을 수정하지 못했습니다.')
  }

  // 삭제: 먼저 목록에서 빼고 포커스를 입력창으로 옮깁니다 (NFR-003).
  // 이미 삭제된 항목(404)은 성공으로 간주하고, 그 외 실패는 원래 자리로 복구합니다 (AC-FR-005-2).
  const deleteTodo = (id: string) => {
    const index = todos.findIndex((todo) => todo.id === id)
    if (index === -1) return
    const removed = todos[index]

    setTodos((prev) => prev.filter((todo) => todo.id !== id))
    inputRef.current?.focus()

    todoApi.deleteTodo(id).catch((error: unknown) => {
      if (error instanceof ApiError && error.code === 'NOT_FOUND') return
      setTodos((prev) => {
        const next = [...prev]
        next.splice(Math.min(index, next.length), 0, removed)
        return next
      })
      setNotice(`할 일을 삭제하지 못했습니다. ${getErrorMessage(error)}`)
    })
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1 className="app-title">My ToDo</h1>
        <ProgressMeter todos={todos} />
      </header>

      {notice && (
        <div className="notice" role="alert">
          <p className="notice-text">{notice}</p>
          {loadState === 'error' ? (
            <button type="button" className="btn btn-quiet" onClick={retryLoad}>
              다시 시도
            </button>
          ) : (
            <button type="button" className="btn btn-quiet" onClick={() => setNotice(null)}>
              닫기
            </button>
          )}
        </div>
      )}

      <TodoInput onAdd={addTodo} inputRef={inputRef} disabled={loadState !== 'ready'} />

      {loadState === 'loading' && (
        <p className="empty" aria-live="polite">
          할 일을 불러오는 중입니다…
        </p>
      )}

      {loadState === 'ready' &&
        (todos.length === 0 ? (
          <p className="empty">첫 할 일을 위에 입력해 보세요.</p>
        ) : (
          <ul className="list" aria-label="할 일 목록">
            {todos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                onToggle={toggleTodo}
                onUpdate={updateTodoText}
                onDelete={deleteTodo}
              />
            ))}
          </ul>
        ))}
    </main>
  )
}
