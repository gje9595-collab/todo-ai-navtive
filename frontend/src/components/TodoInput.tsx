import { useState, type FormEvent, type RefObject } from 'react'
import { CATEGORIES, isCategory, type Category } from '../categories'
import { DUE_DATE_MAX, DUE_DATE_MIN } from '../dueDate'

interface TodoInputProps {
  /** 추가에 성공하면 true. 실패하면 입력값을 그대로 남긴다 (AC-FR-001-4). */
  onAdd: (text: string, dueDate: string | null, category: Category) => Promise<boolean>
  inputRef: RefObject<HTMLInputElement | null>
  /** 카테고리 기본값. 필터가 특정 카테고리면 그 값이다 (AC-FR-014-6). */
  defaultCategory: Category
  /** 목록을 불러오기 전에는 추가할 수 없다 (FR-011). */
  disabled?: boolean
}

/** 새 할 일 입력창, 카테고리, 마감일(선택), 추가 버튼 */
export default function TodoInput({ onAdd, inputRef, defaultCategory, disabled = false }: TodoInputProps) {
  const [value, setValue] = useState('')
  // `<input type="date">`의 값. 비어 있으면 마감일 없음 (FR-012)
  const [dueDate, setDueDate] = useState('')
  const [category, setCategory] = useState<Category>(defaultCategory)
  // 필터가 바뀌어 기본값이 바뀌면 선택도 맞춘다. 렌더링 중 이전 값과 비교하는 방식이라 Effect가 필요 없다.
  const [prevDefault, setPrevDefault] = useState(defaultCategory)
  if (prevDefault !== defaultCategory) {
    setPrevDefault(defaultCategory)
    setCategory(defaultCategory)
  }
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const text = value.trim()
    // 공백만 입력했거나, 목록을 불러오는 중이거나, 이미 요청 중이면 추가하지 않는다.
    if (!text || disabled || isSubmitting) return

    // 버튼으로 제출하면 버튼이 곧 비활성화되며 포커스를 잃으므로, 먼저 입력창으로 옮긴다 (AC-NFR-003-3).
    inputRef.current?.focus()
    setIsSubmitting(true)
    const added = await onAdd(text, dueDate || null, category)
    setIsSubmitting(false)
    if (added) {
      setValue('')
      // 추가 후 날짜 입력도 비운다 (AC-FR-012-5). 카테고리는 연속 입력을 위해 그대로 둔다.
      setDueDate('')
    }
  }

  return (
    <form className="todo-form" onSubmit={handleSubmit}>
      <label htmlFor="new-todo" className="sr-only">
        새 할 일
      </label>
      <input
        id="new-todo"
        ref={inputRef}
        className="text-input"
        type="text"
        placeholder="할 일을 입력하세요"
        value={value}
        maxLength={500}
        // 요청 중에 입력이 바뀌면 성공 후 지울 때 새 입력까지 사라지므로 잠시 읽기 전용으로 둔다.
        readOnly={isSubmitting}
        onChange={(e) => setValue(e.target.value)}
      />
      <div className="todo-form-row">
        <div className="form-fields">
          <div className="field">
            <label htmlFor="new-todo-category" className="field-label">
              카테고리
            </label>
            <select
              id="new-todo-category"
              className="select-input"
              value={category}
              disabled={isSubmitting}
              onChange={(e) => {
                if (isCategory(e.target.value)) setCategory(e.target.value)
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
            <label htmlFor="new-todo-due" className="field-label">
              마감일 (선택)
            </label>
            <input
              id="new-todo-due"
              className="date-input"
              type="date"
              value={dueDate}
              min={DUE_DATE_MIN}
              max={DUE_DATE_MAX}
              readOnly={isSubmitting}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>
        </div>
        <button type="submit" className="btn btn-primary" disabled={disabled || isSubmitting || !value.trim()}>
          {isSubmitting ? '추가 중' : '추가'}
        </button>
      </div>
    </form>
  )
}
