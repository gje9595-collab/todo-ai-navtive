import { CATEGORIES, type CategoryFilter as Filter } from '../categories'

interface CategoryFilterProps {
  value: Filter
  /** 카테고리별 할 일 개수. 'all'은 전체 개수 */
  counts: Record<Filter, number>
  onChange: (value: Filter) => void
}

const OPTIONS: ReadonlyArray<{ value: Filter; label: string }> = [{ value: 'all', label: '전체' }, ...CATEGORIES]

/**
 * 카테고리 필터 (FR-014). 토글 버튼 묶음이며 선택 상태는 `aria-pressed`로 전달한다.
 * 목록을 다시 요청하지 않고 App이 받아 둔 목록을 거른다 (PRD D-10).
 */
export default function CategoryFilter({ value, counts, onChange }: CategoryFilterProps) {
  return (
    <div className="category-filter" role="group" aria-label="카테고리 필터">
      {OPTIONS.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            className={`filter-btn${selected ? ' is-selected' : ''}`}
            aria-pressed={selected}
            onClick={() => onChange(option.value)}
          >
            {option.label}
            <span className="filter-count">
              {counts[option.value]}
              <span className="sr-only">개</span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
