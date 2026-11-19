import { useRef, useState } from 'react'
import ProgressMeter from './components/ProgressMeter'
import TodoInput from './components/TodoInput'
import TodoItem from './components/TodoItem'
import type { Todo } from './types'
import { getInitialTodos } from './demoTodos'

export default function App() {
  const [todos, setTodos] = useState<Todo[]>(getInitialTodos)
  const inputRef = useRef<HTMLInputElement>(null)

  const addTodo = (text: string) => {
    setTodos((prev) => [...prev, { id: crypto.randomUUID(), text, completed: false }])
  }

  const toggleTodo = (id: string) => {
    setTodos((prev) =>
      prev.map((todo) => (todo.id === id ? { ...todo, completed: !todo.completed } : todo)),
    )
  }

  const updateTodo = (id: string, text: string) => {
    setTodos((prev) => prev.map((todo) => (todo.id === id ? { ...todo, text } : todo)))
  }

  // 삭제된 버튼에 머물던 키보드 포커스를 입력창으로 옮깁니다.
  const deleteTodo = (id: string) => {
    setTodos((prev) => prev.filter((todo) => todo.id !== id))
    inputRef.current?.focus()
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1 className="app-title">My ToDo</h1>
        <ProgressMeter todos={todos} />
      </header>

      <TodoInput onAdd={addTodo} inputRef={inputRef} />

      {todos.length === 0 ? (
        <p className="empty">첫 할 일을 위에 입력해 보세요.</p>
      ) : (
        <ul className="list" aria-label="할 일 목록">
          {todos.map((todo) => (
            <TodoItem
              key={todo.id}
              todo={todo}
              onToggle={toggleTodo}
              onUpdate={updateTodo}
              onDelete={deleteTodo}
            />
          ))}
        </ul>
      )}
    </main>
  )
}
