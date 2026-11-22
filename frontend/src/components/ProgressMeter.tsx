import type { Todo } from '../types'

interface ProgressMeterProps {
  todos: Todo[]
}

/** 작업 하나를 칸 하나로 표시할 최대 개수. 넘으면 연속형 막대로 바꾼다. */
const MAX_SEGMENTS = 24

/**
 * 완료율 표시. 별도 상태 없이 todos에서 계산한다.
 * 막대는 시각 정보이므로 aria-hidden, 같은 내용은 aria-live 문장으로 전달한다.
 */
export default function ProgressMeter({ todos }: ProgressMeterProps) {
  const total = todos.length
  const done = todos.filter((t) => t.completed).length
  const percent = total === 0 ? 0 : Math.round((done / total) * 100)

  let message: string
  if (total === 0) message = '아직 할 일이 없습니다'
  else if (done === total) message = `${total}개 모두 완료했습니다`
  else message = `${total}개 중 ${done}개 완료`

  return (
    <section className="progress" aria-label="진행률">
      <div className="progress-head">
        <p className="progress-text" aria-live="polite">
          {message}
        </p>
        {total > 0 && <span className="progress-percent">{percent}%</span>}
      </div>

      {total > 0 &&
        (total <= MAX_SEGMENTS ? (
          <ol className="meter meter-segmented" aria-hidden="true">
            {todos.map((t) => (
              <li key={t.id} className={t.completed ? 'segment is-done' : 'segment'} />
            ))}
          </ol>
        ) : (
          <div className="meter meter-continuous" aria-hidden="true">
            <div className="meter-fill" style={{ width: `${percent}%` }} />
          </div>
        ))}
    </section>
  )
}
