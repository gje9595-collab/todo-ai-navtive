import type { Todo } from '../types'

interface ProgressMeterProps {
  todos: Todo[]
}

// 할 일이 이보다 많으면 칸을 나누지 않고 하나의 막대로 표시합니다.
const MAX_SEGMENTS = 24

export default function ProgressMeter({ todos }: ProgressMeterProps) {
  const total = todos.length
  const done = todos.filter((todo) => todo.completed).length
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)
  const segmented = total > 0 && total <= MAX_SEGMENTS

  return (
    <section className="progress" aria-label="완료율">
      <p className="progress-text" aria-live="polite">
        {total === 0 ? (
          <span className="progress-detail">할 일을 추가하면 완료율이 표시됩니다</span>
        ) : (
          <>
            <span className="progress-percent">{percent}%</span>
            <span className="progress-detail">
              {total}개 중 {done}개 완료
            </span>
          </>
        )}
      </p>

      <div
        className="meter"
        role="progressbar"
        aria-label="완료율"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={`${total}개 중 ${done}개 완료`}
      >
        {segmented ? (
          todos.map((todo) => (
            <span key={todo.id} className={`meter-segment${todo.completed ? ' is-done' : ''}`} />
          ))
        ) : (
          <span className="meter-track">
            <span className="meter-fill" style={{ width: `${percent}%` }} />
          </span>
        )}
      </div>
    </section>
  )
}
