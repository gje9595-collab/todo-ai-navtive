import { useState, type FormEvent, type Ref } from 'react'

interface TodoInputProps {
  onAdd: (text: string) => void
  inputRef?: Ref<HTMLInputElement>
}

export default function TodoInput({ onAdd, inputRef }: TodoInputProps) {
  const [text, setText] = useState('')

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    onAdd(trimmed)
    setText('')
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
      />
      <button type="submit" className="btn btn-primary" disabled={!text.trim()}>
        추가
      </button>
    </form>
  )
}
