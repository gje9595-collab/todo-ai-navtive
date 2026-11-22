interface ImportMetaEnv {
  /** FastAPI 서버 주소 (예: http://localhost:8000). `/api`는 붙이지 않는다. */
  readonly VITE_API_BASE_URL?: string
  /** 개발용 인증 토큰. Supabase Auth 연동(3단계) 전까지 Authorization 헤더에 쓴다. */
  readonly VITE_DEV_AUTH_TOKEN?: string
}
