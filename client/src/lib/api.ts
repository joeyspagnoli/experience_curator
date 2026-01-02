// Light wrapper around fetch that captures trace ids and normalizes errors.
type JsonInit = Omit<RequestInit, 'body' | 'headers'> & {
  body?: BodyInit | object | null
  headers?: HeadersInit
}

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
const TRACE_HEADER = 'x-trace-id'

export class ApiError extends Error {
  status: number
  data?: unknown
  traceId?: string

  constructor(message: string, status: number, data?: unknown, traceId?: string) {
    super(message)
    this.status = status
    this.data = data
    this.traceId = traceId
  }
}

const getTraceId = (response: Response) =>
  response.headers.get(TRACE_HEADER) || response.headers.get('X-Trace-Id') || undefined

const parseJson = async (response: Response) => {
  try {
    return await response.json()
  } catch {
    return null
  }
}

/** Perform JSON requests and return `{ data, traceId }` for observability. */
export async function fetchJson<T>(path: string, init: JsonInit = {}) {
  const { body, headers, ...rest } = init
  const finalHeaders = new Headers(headers ?? {})
  let finalBody: BodyInit | null | undefined = body as BodyInit | null | undefined

  const isJsonBody =
    body &&
    typeof body === 'object' &&
    !(body instanceof FormData) &&
    !(body instanceof Blob)

  if (isJsonBody) {
    finalHeaders.set('Content-Type', 'application/json')
    finalBody = JSON.stringify(body)
  }

  if (!finalHeaders.has('Accept')) {
    finalHeaders.set('Accept', 'application/json')
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: finalBody,
  })

  const traceId = getTraceId(response)
  const payload = await parseJson(response)

  if (!response.ok) {
    const message =
      (payload && typeof payload === 'object' && 'detail' in payload
        ? String((payload as { detail?: string }).detail)
        : response.statusText) || 'Request failed'
    throw new ApiError(message, response.status, payload, traceId)
  }

  return { data: payload as T, traceId }
}

/** Multipart helper for file uploads with trace id capture. */
export async function uploadMultipart<T>(path: string, formData: FormData, init: RequestInit = {}) {
  const headers = new Headers(init.headers ?? {})
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json')
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    method: init.method ?? 'POST',
    body: formData,
    headers,
  })
  const traceId = getTraceId(response)
  const payload = await parseJson(response)

  if (!response.ok) {
    const message =
      (payload && typeof payload === 'object' && 'detail' in payload
        ? String((payload as { detail?: string }).detail)
        : response.statusText) || 'Request failed'
    throw new ApiError(message, response.status, payload, traceId)
  }

  return { data: payload as T, traceId }
}

export const isApiError = (error: unknown): error is ApiError =>
  error instanceof ApiError
