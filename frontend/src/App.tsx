import { useEffect, useRef, useState } from 'react'
import { ApiError, getErrorMessage } from './api/client'
import * as todoApi from './api/todos'
import {
  CATEGORY_LABEL,
  countByCategory,
  DEFAULT_CATEGORY,
  type Category,
  type CategoryFilter as Filter,
} from './categories'
import CategoryFilter from './components/CategoryFilter'
import ProgressMeter from './components/ProgressMeter'
import TodoInput from './components/TodoInput'
import TodoItem from './components/TodoItem'
import { toDateKey } from './dueDate'
import type { Todo } from './types'

type LoadState = 'loading' | 'ready' | 'error'

const dateFormatter = new Intl.DateTimeFormat('ko-KR', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
})

/** 할 일 목록 상태와 API 연동을 관리한다 (api-spec 5절의 화면 갱신 전략). */
export default function App() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [loadError, setLoadError] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  // 개별 동작(추가·토글·수정·삭제) 실패 알림 (FR-011)
  const [notice, setNotice] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  // 서버가 마지막으로 확인해 준 값. 낙관적 업데이트가 실패하면 이 값으로 되돌린다 (NFR-006).
  // 화면 상태(todos)는 아직 저장되지 않은 낙관적 값을 담고 있을 수 있어 롤백 기준으로 쓸 수 없다.
  const confirmedRef = useRef(new Map<string, Todo>())
  // 렌더링마다 새로 만들지 않도록 처음 한 번만 계산한다.
  const [today] = useState(() => new Date())
  // 마감 표시(오늘·지남) 기준이 되는 현지 날짜 (FR-012, PRD D-8)
  const todayKey = toDateKey(today)
  // 카테고리 필터 (FR-014). 저장하지 않으므로 새로고침하면 "전체"다 (PRD D-10).
  const [filter, setFilter] = useState<Filter>('all')

  // 파생 값: 상태로 저장하지 않고 todos와 filter에서 계산한다 (CLAUDE.md 6-1).
  const visibleTodos = filter === 'all' ? todos : todos.filter((todo) => todo.category === filter)
  const counts = countByCategory(todos.map((todo) => todo.category))
  // 필터가 특정 카테고리면 새 할 일도 그 카테고리로 만든다. 추가하자마자 화면에서 사라지지 않게 하기 위해서다 (AC-FR-014-6).
  const defaultCategory: Category = filter === 'all' ? DEFAULT_CATEGORY : filter

  // 목록 조회 (FR-002). StrictMode의 이중 실행이나 재시도 중 늦게 도착한 응답은 무시한다.
  useEffect(() => {
    let ignore = false
    todoApi
      .fetchTodos()
      .then((items) => {
        if (ignore) return
        confirmedRef.current = new Map(items.map((todo) => [todo.id, todo]))
        setTodos(items)
        setLoadState('ready')
      })
      .catch((error: unknown) => {
        if (ignore) return
        setLoadError(getErrorMessage(error))
        setLoadState('error')
      })
    return () => {
      ignore = true
    }
  }, [reloadKey])

  const retryLoad = () => {
    setLoadState('loading')
    setReloadKey((key) => key + 1)
  }

  // 추가: id를 서버가 발급하므로 응답을 받은 뒤 목록 끝에 붙인다 (FR-001).
  const addTodo = async (text: string, dueDate: string | null, category: Category): Promise<boolean> => {
    try {
      const created = await todoApi.createTodo(text, dueDate, category)
      confirmedRef.current.set(created.id, created)
      setTodos((prev) => [...prev, created])
      setNotice(null)
      return true
    } catch (error) {
      setNotice(`할 일을 추가하지 못했습니다. ${getErrorMessage(error)}`)
      return false
    }
  }

  /**
   * 토글·수정: 화면을 먼저 바꾸고(낙관적 업데이트) 요청한다 (NFR-006).
   * - 성공 응답으로 화면을 다시 덮어쓰지 않는다. 늦게 온 응답이 사용자의 최신 선택을 되돌리지 않게 하기 위해서다.
   *   대신 서버 확인 값(confirmedRef)만 갱신한다.
   * - 실패하면 바꾼 필드만, 그 필드가 아직 이번에 보낸 값일 때만(그사이 사용자가 다시 바꾸지 않았을 때만)
   *   서버 확인 값으로 되돌린다 (AC-NFR-006-2).
   */
  const patchTodo = (id: string, patch: todoApi.TodoPatch, failMessage: string) => {
    const previous = todos.find((todo) => todo.id === id)
    if (!previous) return

    setTodos((prev) => prev.map((todo) => (todo.id === id ? { ...todo, ...patch } : todo)))

    todoApi
      .updateTodo(id, patch)
      .then((saved) => {
        confirmedRef.current.set(id, saved)
      })
      .catch((error: unknown) => {
        const confirmed = confirmedRef.current.get(id) ?? previous
        setTodos((prev) =>
          prev.map((todo) => {
            if (todo.id !== id) return todo
            const rolledBack = { ...todo }
            if (patch.text !== undefined && todo.text === patch.text) rolledBack.text = confirmed.text
            if (patch.completed !== undefined && todo.completed === patch.completed) {
              rolledBack.completed = confirmed.completed
            }
            // 마감일도 같은 규칙으로 되돌린다. null(지우기)도 보낸 값이므로 undefined만 "안 바꿈"이다 (AC-FR-012-8).
            if (patch.dueDate !== undefined && todo.dueDate === patch.dueDate) rolledBack.dueDate = confirmed.dueDate
            // 카테고리도 같은 규칙. 필터에서 빠졌던 카드는 롤백되면 다시 보인다 (AC-FR-013-5).
            if (patch.category !== undefined && todo.category === patch.category) {
              rolledBack.category = confirmed.category
            }
            return rolledBack
          }),
        )
        setNotice(`${failMessage} ${getErrorMessage(error)}`)
      })
  }

  const toggleTodo = (id: string) => {
    const target = todos.find((todo) => todo.id === id)
    if (target) patchTodo(id, { completed: !target.completed }, '완료 상태를 바꾸지 못했습니다.')
  }

  // 편집 저장: 텍스트·마감일·카테고리 중 바뀐 필드만 한 번에 보낸다 (FR-004, FR-012, FR-013).
  const updateTodo = (id: string, patch: todoApi.TodoPatch) => {
    patchTodo(id, patch, '할 일을 수정하지 못했습니다.')
    // 카테고리를 바꿔 현재 필터에서 빠지면 카드와 "수정" 버튼이 사라진다.
    // 포커스를 잃지 않도록 삭제와 같이 새 할 일 입력창으로 옮긴다 (AC-FR-014-6, NFR-003).
    if (patch.category !== undefined && filter !== 'all' && patch.category !== filter) {
      inputRef.current?.focus()
    }
  }

  // 삭제: 먼저 목록에서 빼고 입력창으로 포커스를 옮긴다 (NFR-003).
  // 이미 삭제된 항목(NOT_FOUND)은 성공으로 보고, 그 밖의 실패는 원래 위치에 복구한다 (FR-005).
  const deleteTodo = (id: string) => {
    const index = todos.findIndex((todo) => todo.id === id)
    if (index === -1) return
    const removed = todos[index]

    setTodos((prev) => prev.filter((todo) => todo.id !== id))
    inputRef.current?.focus()

    todoApi
      .deleteTodo(id)
      .then(() => {
        confirmedRef.current.delete(id)
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.code === 'NOT_FOUND') {
          confirmedRef.current.delete(id)
          return
        }
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
        <time className="app-date" dateTime={todayKey}>
          {dateFormatter.format(today)}
        </time>
      </header>

      {/* 완료율은 현재 필터에 보이는 목록 기준이다 (AC-FR-014-5) */}
      {loadState === 'ready' && <ProgressMeter todos={visibleTodos} />}

      <TodoInput
        onAdd={addTodo}
        inputRef={inputRef}
        defaultCategory={defaultCategory}
        disabled={loadState !== 'ready'}
      />

      {notice && (
        <div className="notice" role="alert">
          <p className="notice-text">{notice}</p>
          <button type="button" className="btn btn-ghost" onClick={() => setNotice(null)}>
            닫기
          </button>
        </div>
      )}

      {loadState === 'loading' && (
        <div className="loading" aria-busy="true">
          <p className="sr-only" aria-live="polite">
            할 일을 불러오는 중입니다.
          </p>
          <div className="skeleton-list" aria-hidden="true">
            <div className="skeleton-card" />
            <div className="skeleton-card" />
            <div className="skeleton-card" />
          </div>
        </div>
      )}

      {loadState === 'error' && (
        <div className="load-error" role="alert">
          <p className="load-error-title">할 일 목록을 불러오지 못했습니다.</p>
          <p className="load-error-text">{loadError}</p>
          <button type="button" className="btn btn-primary" onClick={retryLoad}>
            다시 시도
          </button>
        </div>
      )}

      {loadState === 'ready' && <CategoryFilter value={filter} counts={counts} onChange={setFilter} />}

      {loadState === 'ready' &&
        (visibleTodos.length === 0 ? (
          <p className="empty">
            {todos.length === 0 || filter === 'all'
              ? '위 입력창에 첫 할 일을 적고 Enter를 누르세요.'
              : `${CATEGORY_LABEL[filter]} 할 일이 없습니다. 위에서 추가하거나 "전체"를 눌러 보세요.`}
          </p>
        ) : (
          <ul className="todo-list" aria-label="할 일 목록">
            {visibleTodos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                todayKey={todayKey}
                onToggle={toggleTodo}
                onUpdate={updateTodo}
                onDelete={deleteTodo}
              />
            ))}
          </ul>
        ))}
    </main>
  )
}
