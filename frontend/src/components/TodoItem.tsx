import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import type { Todo } from '../types'

interface TodoItemProps {
  todo: Todo
  onToggle: (id: string) => void
  onUpdate: (id: string, text: string) => void
  onDelete: (id: string) => void
}

export default function TodoItem({ todo, onToggle, onUpdate, onDelete }: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(todo.text)
  const editButtonRef = useRef<HTMLButtonElement>(null)
  const returnFocus = useRef(false)

  // 저장/취소 후 키보드 포커스를 "수정" 버튼으로 되돌립니다.
  useEffect(() => {
    if (!isEditing && returnFocus.current) {
      returnFocus.current = false
      editButtonRef.current?.focus()
    }
  }, [isEditing])

  const startEdit = () => {
    setDraft(todo.text)
    setIsEditing(true)
  }

  const finishEdit = () => {
    returnFocus.current = true
    setIsEditing(false)
  }

  const cancelEdit = () => {
    setDraft(todo.text)
    finishEdit()
  }

  const handleSave = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const trimmed = draft.trim()
    if (!trimmed) return
    onUpdate(todo.id, trimmed)
    finishEdit()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') cancelEdit()
  }

  const checkboxId = `todo-${todo.id}`

  return (
    <li className={`card${todo.completed ? ' is-done' : ''}${isEditing ? ' is-editing' : ''}`}>
      <input
        id={checkboxId}
        type="checkbox"
        className="check"
        checked={todo.completed}
        onChange={() => onToggle(todo.id)}
        aria-label={`${todo.text} 완료 표시`}
      />

      {isEditing ? (
        <form className="card-edit" onSubmit={handleSave}>
          <input
            type="text"
            className="field"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="할 일 수정"
            autoFocus
          />
          <div className="card-actions">
            <button type="submit" className="btn btn-primary" disabled={!draft.trim()}>
              저장
            </button>
            <button type="button" className="btn btn-quiet" onClick={cancelEdit}>
              취소
            </button>
          </div>
        </form>
      ) : (
        <>
          <label htmlFor={checkboxId} className="card-text">
            {todo.text}
          </label>
          <div className="card-actions">
            <button
              ref={editButtonRef}
              type="button"
              className="btn btn-quiet"
              onClick={startEdit}
              aria-label={`${todo.text} 수정`}
            >
              수정
            </button>
            <button
              type="button"
              className="btn btn-quiet btn-danger"
              onClick={() => onDelete(todo.id)}
              aria-label={`${todo.text} 삭제`}
            >
              삭제
            </button>
          </div>
        </>
      )}
    </li>
  )
}
