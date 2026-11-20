// FastAPI 호출 공통 처리: Base URL, 인증 헤더, 에러 응답(API 명세 2-1) 해석.

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '')

// Supabase Auth 연동 전까지 사용하는 개발용 토큰. 백엔드 dev 인증 모드에서 user_id로 쓰입니다.
const DEV_AUTH_TOKEN = import.meta.env.VITE_DEV_AUTH_TOKEN ?? 'dev-user'

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
    throw new ApiError(0, 'NETWORK_ERROR', '서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해 주세요.')
  }

  if (response.status === 204) return undefined as T

  const data: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const error = (data as ErrorBody | null)?.error
    const message =
      response.status === 401
        ? '인증이 필요합니다. 다시 로그인해 주세요.'
        : (error?.message ?? `요청을 처리하지 못했습니다. (HTTP ${response.status})`)
    throw new ApiError(response.status, error?.code ?? 'UNKNOWN_ERROR', message)
  }

  return data as T
}

export function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : '알 수 없는 오류가 발생했습니다.'
}
