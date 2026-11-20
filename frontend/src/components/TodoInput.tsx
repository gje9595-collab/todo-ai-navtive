import { useState, type FormEvent, type Ref } from 'react'

interface TodoInputProps {
  /** 추가에 성공하면 true를 돌려줍니다. 실패하면 입력값을 그대로 둡니다. */
  onAdd: (text: string) => Promise<boolean>
  inputRef?: Ref<HTMLInputElement>
  disabled?: boolean
}

export default function TodoInput({ onAdd, inputRef, disabled = false }: TodoInputProps) {
  const [text, setText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || isSubmitting || disabled) return

    setIsSubmitting(true)
    const added = await onAdd(trimmed)
    setIsSubmitting(false)
    if (added) setText('')
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <label htmlFor="new-todo" className="visually-hidden">
        새 할 일
      </label>
      <input
        id="new-todo"
        ref={inputRef}
        type="text"
        className="field"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="할 일을 입력하고 Enter"
        autoComplete="off"
        maxLength={500}
        disabled={disabled}
      />
      <button
        type="submit"
        className="btn btn-primary"
        disabled={disabled || isSubmitting || !text.trim()}
      >
        {isSubmitting ? '추가 중…' : '추가'}
      </button>
    </form>
  )
}
