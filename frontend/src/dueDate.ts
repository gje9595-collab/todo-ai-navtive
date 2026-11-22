// 마감일 표시 규칙 (FR-012, PRD D-8). 날짜는 시각 없는 `YYYY-MM-DD` 문자열로 다룬다.
// "오늘"·"지남"은 브라우저 현지 날짜로 판단한다.

/** 서버가 허용하는 범위 (api-spec 2-4). `<input type="date">`의 min/max로도 쓴다. */
export const DUE_DATE_MIN = '2000-01-01'
export const DUE_DATE_MAX = '2100-12-31'

export type DueTone = 'normal' | 'today' | 'overdue'

export interface DueInfo {
  label: string
  tone: DueTone
}

const DAY_MS = 24 * 60 * 60 * 1000

/** Date를 현지 날짜 기준 `YYYY-MM-DD`로 바꾼다. `toISOString()`은 UTC라 날짜가 하루 밀릴 수 있다. */
export function toDateKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

/** 두 날짜 키의 일 수 차이(a - b). UTC 자정으로 계산해 서머타임 영향을 받지 않는다. */
function daysBetween(a: string, b: string): number {
  return Math.round((Date.parse(`${a}T00:00:00Z`) - Date.parse(`${b}T00:00:00Z`)) / DAY_MS)
}

/**
 * 카드에 보여 줄 마감 문구를 만든다 (AC-FR-012-7).
 * - 오늘이면 "오늘 마감"
 * - 지났고 미완료면 "N일 지남" (강조)
 * - 그 밖(미래, 또는 완료된 지난 할 일)은 "M월 D일 마감"
 */
export function describeDue(dueDate: string, completed: boolean, todayKey: string): DueInfo {
  const diff = daysBetween(dueDate, todayKey)
  if (diff === 0) return { label: '오늘 마감', tone: 'today' }
  if (diff < 0 && !completed) return { label: `${-diff}일 지남`, tone: 'overdue' }
  const [, month, day] = dueDate.split('-')
  return { label: `${Number(month)}월 ${Number(day)}일 마감`, tone: 'normal' }
}
