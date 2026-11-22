import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import type { TodoPatch } from '../api/todos'
import { CATEGORIES, CATEGORY_LABEL, isCategory, type Category } from '../categories'
import { describeDue, DUE_DATE_MAX, DUE_DATE_MIN } from '../dueDate'
import type { Todo } from '../types'

interface TodoItemProps {
  todo: Todo
  /** 현지 날짜 기준 오늘 `YYYY-MM-DD`. 마감 표시(오늘·지남) 판단에 쓴다 (FR-012) */
  todayKey: string
  onToggle: (id: string) => void
  /** 바뀐 필드만 담아 보낸다 (텍스트, 마감일, 카테고리) */
  onUpdate: (id: string, patch: TodoPatch) => void
  onDelete: (id: string) => void
}

/** 할 일 한 줄. 편집에 필요한 로컬 상태(isEditing, draft, draftDue, draftCategory)만 관리한다. */
export default function TodoItem({ todo, todayKey, onToggle, onUpdate, onDelete }: TodoItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(todo.text)
  // 편집 중인 마감일. 빈 문자열이면 마감일 없음 (FR-012)
  const [draftDue, setDraftDue] = useState(todo.dueDate ?? '')
  // 편집 중인 카테고리 (FR-013)
  const [draftCategory, setDraftCategory] = useState<Category>(todo.category)
  const editButtonRef = useRef<HTMLButtonElement>(null)
  const dueInputRef = useRef<HTMLInputElement>(null)

  const checkboxId = `todo-${todo.id}`
  const dueInputId = `edit-due-${todo.id}`
  const categoryInputId = `edit-category-${todo.id}`
  const due = todo.dueDate ? describeDue(todo.dueDate, todo.completed, todayKey) : null

  // 편집 종료 후 렌더링이 끝난 다음 "수정" 버튼으로 포커스를 돌려준다.
  const returnFocus = () => {
    requestAnimationFrame(() => editButtonRef.current?.focus())
  }

  const startEdit = () => {
    setDraft(todo.text)
    setDraftDue(todo.dueDate ?? '')
    setDraftCategory(todo.category)
    setIsEditing(true)
  }

  const cancelEdit = () => {
    setIsEditing(false)
    returnFocus()
  }

  // "마감일 지우기"는 누르면 비활성화되므로, 포커스를 날짜 입력으로 옮겨 잃지 않게 한다.
  const clearDue = () => {
    setDraftDue('')
    dueInputRef.current?.focus()
  }

  const handleSave = (e: FormEvent) => {
    e.preventDefault()
    const text = draft.trim()
    if (!text) return
    // 바뀐 필드만 보낸다. 모두 그대로면 요청하지 않는다 (AC-FR-012-6, AC-FR-013-5).
    const patch: TodoPatch = {}
    if (text !== todo.text) patch.text = text
    const nextDue = draftDue || null
    if (nextDue !== todo.dueDate) patch.dueDate = nextDue
    if (draftCategory !== todo.category) patch.category = draftCategory
    if (Object.keys(patch).length > 0) onUpdate(todo.id, patch)
    setIsEditing(false)
    returnFocus()
  }

  // 텍스트·날짜 입력 어디서든 Esc를 누르면 편집을 취소한다 (NFR-003).
  const handleKeyDown = (e: KeyboardEvent<HTMLFormElement>) => {
    if (e.key === 'Escape') cancelEdit()
  }

  if (isEditing) {
    return (
      <li className="todo-item is-editing">
        <form className="edit-form" onSubmit={handleSave} onKeyDown={handleKeyDown}>
          <label htmlFor={`edit-${todo.id}`} className="sr-only">
            할 일 수정
          </label>
          <input
            id={`edit-${todo.id}`}
            className="text-input"
            type="text"
            value={draft}
            maxLength={500}
            autoFocus
            onChange={(e) => setDraft(e.target.value)}
          />
          <div className="edit-form-row">
            <div className="field">
              <label htmlFor={categoryInputId} className="field-label">
                카테고리
              </label>
              <select
                id={categoryInputId}
                className="select-input"
                value={draftCategory}
                onChange={(e) => {
                  if (isCategory(e.target.value)) setDraftCategory(e.target.value)
                }}
              >
                {CATEGORIES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor={dueInputId} className="field-label">
                마감일
              </label>
              <input
                id={dueInputId}
                ref={dueInputRef}
                className="date-input"
                type="date"
                value={draftDue}
                min={DUE_DATE_MIN}
                max={DUE_DATE_MAX}
                onChange={(e) => setDraftDue(e.target.value)}
              />
              <button type="button" className="btn btn-ghost" onClick={clearDue} disabled={!draftDue}>
                마감일 지우기
              </button>
            </div>
            <div className="actions">
              <button type="submit" className="btn btn-primary" disabled={!draft.trim()}>
                저장
              </button>
              <button type="button" className="btn btn-ghost" onClick={cancelEdit}>
                취소
              </button>
            </div>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className={`todo-item${todo.completed ? ' is-done' : ''}`}>
      <input
        id={checkboxId}
        className="checkbox"
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id)}
      />
      <div className="todo-body">
        <label htmlFor={checkboxId} className="todo-text">
          {todo.text}
        </label>
        <div className="todo-meta">
          {/* 카테고리는 색 없이 라벨로만 구분한다 (spec-review R-31) */}
          <span className="todo-category">{CATEGORY_LABEL[todo.category]}</span>
          {due && (
            <time className={`todo-due is-${due.tone}`} dateTime={todo.dueDate ?? undefined}>
              {due.label}
            </time>
          )}
        </div>
      </div>
      <div className="actions">
        <button
          ref={editButtonRef}
          type="button"
          className="btn btn-ghost"
          onClick={startEdit}
          aria-label={`"${todo.text}" 수정`}
        >
          수정
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-danger"
          onClick={() => onDelete(todo.id)}
          aria-label={`"${todo.text}" 삭제`}
        >
          삭제
        </button>
      </div>
    </li>
  )
}
