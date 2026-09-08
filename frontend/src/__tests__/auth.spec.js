import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { API_BASE, apiFetch, auth, initializeAuth, logout, request, setSession, useApiClient, validateCredentials } from '../utils/auth'
import { authGuard } from '../router/authGuard'

const user = { _id: 'a', username: 'alice', is_admin: false }
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
beforeEach(() => {
  setSession()
  Object.assign(auth, { ready: false, loading: false, error: '', setupRequired: false, setupTokenRequired: false, notice: '' })
  vi.stubGlobal('fetch', vi.fn())
})
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })

describe('authenticated client', () => {
  it('preserves FormData, caller headers and signals while adding the token', async () => {
    setSession('secret', user)
    fetch.mockResolvedValue(new Response(null, { status: 204 }))
    const body = new FormData()
    body.append('file', 'example')
    const signal = new AbortController().signal
    const response = await apiFetch(`${API_BASE}/cars/`, { method: 'POST', body, signal, headers: { 'X-Test': 'yes' } })
    const init = fetch.mock.calls[0][1]
    expect(init.body).toBe(body)
    expect(init.signal).toBe(signal)
    expect(init.headers.get('Authorization')).toBe('Bearer secret')
    expect(init.headers.get('X-Test')).toBe('yes')
    expect(init.headers.has('Content-Type')).toBe(false)
    expect(response.status).toBe(204)
    expect(sessionStorage.getItem('glovebox.session')).toBe('secret')
  })
  it('retains response cloning and body consumption', async () => {
    fetch.mockResolvedValue(json({ ok: true }))
    const response = await apiFetch('/api/test')
    expect(await response.clone().json()).toEqual({ ok: true })
    expect(await response.json()).toEqual({ ok: true })
  })
  it('expires the current session on 401 but not on 403', async () => {
    setSession('secret', user)
    fetch.mockResolvedValueOnce(json({}, 403)).mockResolvedValueOnce(json({}, 401))
    expect((await apiFetch('/api/private')).status).toBe(403)
    expect(auth.user).toEqual(user)
    await expect(apiFetch('/api/private')).rejects.toMatchObject({ name: 'AbortError' })
    expect(auth.user).toBeNull()
    expect(sessionStorage.getItem('glovebox.session')).toBeNull()
  })
  it('rejects old responses and prevents old component clients using a new account', async () => {
    setSession('alice-token', user)
    const client = useApiClient()
    let resolve
    fetch.mockReturnValue(new Promise(done => { resolve = done }))
    const pending = client('/api/private')
    setSession('bob-token', { ...user, _id: 'b' })
    resolve(json({}, 401))
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' })
    expect(auth.token).toBe('bob-token')
    expect(() => client('/api/private')).toThrow('Session changed')
    expect(fetch).toHaveBeenCalledTimes(1)
  })
  it('rejects a body which finishes after switching accounts', async () => {
    let resolve
    fetch.mockResolvedValue({ ok: true, json: () => new Promise(done => { resolve = done }) })
    const response = await apiFetch('/api/private')
    const pending = response.json()
    setSession('new', user)
    resolve({ private: 'old account' })
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' })
  })
  it('handles 204 password changes without losing the current session and logs out', async () => {
    setSession('secret', user)
    fetch.mockImplementation(() => Promise.resolve(new Response(null, { status: 204 })))
    await expect(request('/auth/password', { current_password: ' old pass ', new_password: ' new pass ' })).resolves.toBeUndefined()
    expect(auth.token).toBe('secret')
    expect(JSON.parse(fetch.mock.calls[0][1].body).new_password).toBe(' new pass ')
    await logout()
    expect(auth.token).toBe('')
  })
  it('signs out locally when the server is unavailable', async () => {
    setSession('secret', user)
    fetch.mockRejectedValue(new TypeError('Offline'))
    await logout()
    expect(auth.user).toBeNull()
    expect(auth.notice).toContain('locally')
  })
  it('clears the session immediately and bounds a stalled logout even if fetch ignores abort', async () => {
    vi.useFakeTimers()
    setSession('secret', user)
    const version = auth.version
    const client = useApiClient()
    fetch.mockReturnValue(new Promise(() => {}))
    const pending = logout()
    expect(auth.token).toBe('')
    expect(auth.user).toBeNull()
    expect(auth.version).toBe(version + 1)
    expect(sessionStorage.getItem('glovebox.session')).toBeNull()
    expect(() => client('/api/private')).toThrow('Session changed')
    const [url, init] = fetch.mock.calls[0]
    expect(url).toBe(`${API_BASE}/auth/logout`)
    expect(init.method).toBe('POST')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer secret')
    expect(init.signal.aborted).toBe(false)
    await vi.advanceTimersByTimeAsync(5000)
    await expect(pending).resolves.toBeUndefined()
    expect(init.signal.aborted).toBe(true)
    expect(auth.notice).toContain('locally')
    expect(vi.getTimerCount()).toBe(0)
  })
  it.each(['success', 'unauthorized', 'offline', 'timeout'])('preserves a login during logout after %s', async outcome => {
    vi.useFakeTimers()
    // Other mounted UI tests may have polling timers; only assert logout cleanup here.
    vi.clearAllTimers()
    setSession('old-token', user)
    let resolve, reject
    fetch.mockReturnValueOnce(new Promise((done, fail) => { resolve = done; reject = fail }))
    const pending = logout()
    const nextUser = { ...user, _id: 'b', username: 'bob' }
    fetch.mockResolvedValueOnce(json({ token: 'new-token', user: nextUser }))
    const session = await request('/auth/login', { username: 'bob', password: 'password' })
    setSession(session.token, session.user)
    auth.notice = 'New session notice'
    const version = auth.version
    expect(new Headers(fetch.mock.calls[0][1].headers).get('Authorization')).toBe('Bearer old-token')
    expect(fetch.mock.calls[1][1].headers.has('Authorization')).toBe(false)
    if (outcome === 'timeout') await vi.advanceTimersByTimeAsync(5000)
    else if (outcome === 'offline') reject(new TypeError('Offline'))
    else resolve(new Response(null, { status: outcome === 'success' ? 204 : 401 }))
    await pending
    expect(auth.token).toBe('new-token')
    expect(auth.user).toEqual(nextUser)
    expect(auth.version).toBe(version)
    expect(sessionStorage.getItem('glovebox.session')).toBe('new-token')
    expect(auth.notice).toBe('New session notice')
    expect(vi.getTimerCount()).toBe(0)
  })
})

describe('initialization and guards', () => {
  it('does not mistake an API failure for setup and permits retry', async () => {
    fetch.mockRejectedValueOnce(new TypeError('Offline')).mockResolvedValueOnce(json({ setup_required: true, setup_token_required: true }))
    expect(await authGuard({ path: '/', meta: {} })).toBe('/auth')
    expect(auth.setupRequired).toBe(false)
    expect(auth.ready).toBe(false)
    expect(auth.error).toBe('Offline')
    await initializeAuth()
    expect(auth.ready).toBe(true)
    expect(auth.setupTokenRequired).toBe(true)
    expect(await authGuard({ path: '/login', meta: {} })).toBe('/setup')
  })
  it('validates stored tokens with me and enforces admin guards', async () => {
    setSession('stored')
    fetch.mockResolvedValueOnce(json({ setup_required: false })).mockResolvedValueOnce(json(user))
    await initializeAuth()
    expect(fetch.mock.calls[1][0]).toBe(`${API_BASE}/auth/me`)
    expect(await authGuard({ path: '/admin', meta: { admin: true } })).toBe('/')
    auth.user.is_admin = true
    expect(await authGuard({ path: '/admin', meta: { admin: true } })).toBe(true)
  })
  it('routes expired stored sessions to login', async () => {
    setSession('expired')
    fetch.mockResolvedValueOnce(json({ setup_required: false })).mockResolvedValueOnce(json({}, 401))
    expect(await authGuard({ path: '/car/1', meta: {} })).toBe('/login')
    expect(auth.ready).toBe(true)
  })
  it('accepts normalized usernames and preserves password whitespace at boundaries', () => {
    expect(validateCredentials(' Alice ', '    ')).toBe('')
    expect(validateCredentials('abc', 'xxx')).toContain('4-128')
    expect(validateCredentials('abc', 'x'.repeat(128))).toBe('')
    expect(validateCredentials('abc', 'x'.repeat(129))).toContain('4-128')
    expect(validateCredentials('_abc', 'password')).toContain('Username')
    expect(validateCredentials('ab', 'password')).toContain('Username')
  })
})
