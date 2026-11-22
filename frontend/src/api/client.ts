// FastAPI 호출 공통 처리: Base URL, 인증 헤더, 공통 에러 응답(api-spec 2-1) 해석.

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '')

// Supabase Auth 연동(3단계) 전까지 쓰는 개발용 토큰. 백엔드 dev 인증 모드에서 user_id가 된다.
const DEV_AUTH_TOKEN = import.meta.env.VITE_DEV_AUTH_TOKEN ?? 'dev-user'

/** API 실패를 나타낸다. `code`는 서버 에러 코드 또는 `NETWORK_ERROR`. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

interface ErrorBody {
  error?: { code?: string; message?: string }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  json?: unknown
}

export async function apiRequest<T>(path: string, { method = 'GET', json }: RequestOptions = {}): Promise<T> {
  const headers = new Headers({ Authorization: `Bearer ${DEV_AUTH_TOKEN}` })
  if (json !== undefined) headers.set('Content-Type', 'application/json')

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api${path}`, {
      method,
      headers,
      body: json === undefined ? undefined : JSON.stringify(json),
    })
  } catch {
    // 서버가 꺼져 있거나 CORS로 막힌 경우 (api-spec 5절)
    throw new ApiError(0, 'NETWORK_ERROR', '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해 주세요.')
  }

  if (response.status === 204) return undefined as T

  const data: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const error = (data as ErrorBody | null)?.error
    const message = error?.message ?? `요청을 처리하지 못했습니다. (HTTP ${response.status})`
    throw new ApiError(response.status, error?.code ?? 'UNKNOWN_ERROR', message)
  }

  return data as T
}

export function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : '알 수 없는 오류가 발생했습니다.'
}
