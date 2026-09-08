import { reactive } from 'vue'

export const API_BASE = (import.meta.env.VITE_API_BASE_URL?.trim() || `${window.location.protocol}//${window.location.hostname}:8000`).replace(/\/$/, '')
const storageKey = 'glovebox.session'
function storedToken() {
  try { return sessionStorage.getItem(storageKey) || '' } catch { return '' }
}
export const auth = reactive({ token: storedToken(), user: null, ready: false, loading: false, error: '', setupRequired: false, setupTokenRequired: false, version: 0, notice: '' })

export function setSession(token = '', user = null) {
  auth.token = token
  auth.user = user
  auth.version++
  try {
    if (token) sessionStorage.setItem(storageKey, token)
    else sessionStorage.removeItem(storageKey)
  } catch { /* A blocked storage policy still permits an in-memory session. */ }
}

function checkVersion(version) {
  if (version !== auth.version) throw new DOMException('Session changed', 'AbortError')
}

// Keep Response semantics (including FormData and 204s), but never expose a previous session's body.
export async function apiFetch(input, init = {}) {
  const version = auth.version
  const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined))
  if (auth.token) headers.set('Authorization', `Bearer ${auth.token}`)
  const response = await globalThis.fetch(input, { cache: 'no-store', ...init, headers })
  checkVersion(version)
  if (response.status === 401 && auth.token) {
    setSession()
    auth.notice = 'Your session has expired. Please sign in again.'
    throw new DOMException('Session expired', 'AbortError')
  }
  return guardedResponse(response, version)
}

function guardedResponse(response, version) {
  return new Proxy(response, {
    get(target, key) {
      const value = Reflect.get(target, key, target)
      if (['json', 'text', 'blob', 'arrayBuffer', 'formData'].includes(key) && typeof value === 'function') {
        return async (...args) => {
          checkVersion(version)
          const body = await value.apply(target, args)
          checkVersion(version)
          return body
        }
      }
      if (key === 'clone') return () => { checkVersion(version); return guardedResponse(target.clone(), version) }
      return typeof value === 'function' ? value.bind(target) : value
    }
  })
}

export function useApiClient() {
  const version = auth.version
  return (input, init) => {
    checkVersion(version)
    return apiFetch(input, init)
  }
}

export async function request(path, body, method = 'POST', headers = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, {
    method, headers: { ...(body === undefined ? {} : { 'Content-Type': 'application/json' }), ...headers },
    ...(body === undefined ? {} : { body: JSON.stringify(body) })
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}). Please try again.`)
  }
  return response.status === 204 ? undefined : response.json()
}

export function useApiRequest() {
  const version = auth.version
  return (path, body, method, headers) => {
    checkVersion(version)
    return request(path, body, method, headers)
  }
}

let initialization
export function initializeAuth() {
  if (initialization) return initialization
  if (auth.ready) return Promise.resolve()
  auth.loading = true
  auth.error = ''
  const version = auth.version
  initialization = (async () => {
    try {
      const status = await request('/auth/status', undefined, 'GET')
      checkVersion(version)
      if (typeof status.setup_required !== 'boolean') throw new Error('Invalid authentication status from server.')
      auth.setupRequired = status.setup_required
      auth.setupTokenRequired = Boolean(status.setup_token_required)
      if (auth.setupRequired) setSession()
      else if (auth.token) {
        try { auth.user = await request('/auth/me', undefined, 'GET') }
        catch (error) { if (auth.token || error.name !== 'AbortError') throw error }
      }
      auth.ready = true
    } catch (error) {
      auth.error = error.message || 'Unable to connect to the server.'
    } finally {
      auth.loading = false
      initialization = undefined
    }
  })()
  return initialization
}

export const normalizeUsername = value => value.trim().toLowerCase()
export function validateCredentials(username, password, minimumPasswordLength = 12) {
  if (username !== null && !/^[a-z0-9][a-z0-9_.-]{2,29}$/.test(normalizeUsername(username))) return 'Username must be 3-30 characters: letters, numbers, dots, underscores or hyphens; start with a letter or number.'
  if ([...password].length < minimumPasswordLength || [...password].length > 128) return `Password must be ${minimumPasswordLength}-128 characters. Spaces are preserved.`
  return ''
}

export async function logout() {
  const token = auth.token
  setSession()
  auth.notice = 'Signed out.'
  const version = auth.version
  if (!token) return
  const controller = new AbortController()
  let timeout
  try {
    const deadline = new Promise((_, reject) => {
      timeout = setTimeout(() => {
        reject(new Error('Logout timed out'))
        controller.abort()
      }, 5000)
    })
    // Revocation belongs to the captured token, not the current session's guarded client.
    const response = await Promise.race([globalThis.fetch(`${API_BASE}/auth/logout`, {
      method: 'POST', cache: 'no-store',
      headers: { Authorization: `Bearer ${token}` }, signal: controller.signal
    }), deadline])
    if (!response.ok) throw new Error('Logout failed')
  } catch {
    if (version === auth.version) auth.notice = 'Signed out locally. The server could not confirm logout.'
  } finally {
    clearTimeout(timeout)
  }
}
