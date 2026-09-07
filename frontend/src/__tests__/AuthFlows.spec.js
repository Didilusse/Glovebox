import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import AccountView from '../views/AccountView.vue'
import AdminView from '../views/AdminView.vue'
import WelcomeView from '../views/WelcomeView.vue'
import App from '../App.vue'
import HomeView from '../views/HomeView.vue'
import { auth, setSession } from '../utils/auth'
import { authGuard } from '../router/authGuard'
const admin = { _id: 'admin', username: 'admin', is_admin: true }
const member = { _id: 'member', username: 'member', is_admin: false }
const json = data => new Response(JSON.stringify(data), { status: 200 })
let wrapper
beforeEach(() => {
  setSession()
  Object.assign(auth, { ready: true, setupRequired: false, setupTokenRequired: false, error: '', notice: '' })
  vi.stubGlobal('fetch', vi.fn())
})
afterEach(() => { wrapper?.unmount(); vi.unstubAllGlobals() })
async function render(component, path = '/', garage = { template: '<p>Private garage</p>' }) {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: garage },
    { path: '/login', component: AuthView }, { path: '/setup', component: AuthView },
    { path: '/welcome', component: WelcomeView }, { path: '/account', component: AccountView },
    { path: '/admin', component: AdminView, meta: { admin: true } }
  ] })
  await router.push(path)
  await router.isReady()
  wrapper = mount(component, { global: { plugins: [router] } })
  await flushPromises()
  return router
}
describe('auth flows', () => {
  it('shows initialization failure with a working retry, not a setup form', async () => {
    Object.assign(auth, { ready: false, error: 'Offline' })
    fetch.mockResolvedValue(json({ setup_required: false }))
    const router = await render(App)
    expect(wrapper.text()).toContain('Unable to initialize authentication')
    expect(wrapper.find('form').exists()).toBe(false)
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(wrapper.text()).toContain('Welcome back')
  })
  it('clears the previous garage while the next account is loading', async () => {
    setSession('first-token', member)
    let resolve
    fetch.mockResolvedValueOnce(json([{ _id: 'car-a', make: 'PrivateMake', model: 'FirstCar', year: 2020 }]))
      .mockReturnValueOnce(new Promise(done => { resolve = done }))
    await render(App, '/', HomeView)
    expect(wrapper.text()).toContain('PrivateMake')
    setSession('second-token', admin)
    await flushPromises()
    expect(wrapper.text()).not.toContain('PrivateMake')
    expect(fetch.mock.calls[1][1].headers.get('Authorization')).toBe('Bearer second-token')
    resolve(json([]))
    await flushPromises()
  })
  it('shows invalid login errors without establishing a session', async () => {
    fetch.mockResolvedValue(new Response(JSON.stringify({ detail: 'Invalid username or password' }), { status: 401 }))
    await render(AuthView, '/login')
    await wrapper.findAll('input')[0].setValue('member')
    await wrapper.findAll('input')[1].setValue('incorrect')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Invalid username or password')
    expect(auth.user).toBeNull()
  })
  it('normalizes login usernames, preserves passwords, and stores only the token', async () => {
    fetch.mockResolvedValue(json({ token: 'session-token', user: member }))
    const router = await render(AuthView, '/login')
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue(' Member ')
    await inputs[1].setValue(' password ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ username: 'member', password: ' password ' })
    expect(sessionStorage.getItem('glovebox.session')).toBe('session-token')
    expect(router.currentRoute.value.path).toBe('/')
    expect(inputs[1].element.value).toBe('')
  })
  it('sends required setup token, then signs in and offers onboarding', async () => {
    Object.assign(auth, { setupRequired: true, setupTokenRequired: true })
    fetch.mockResolvedValueOnce(json(admin)).mockResolvedValueOnce(json({ token: 'admin-token', user: admin }))
    const router = await render(AuthView, '/setup')
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue(' Admin ')
    await inputs[1].setValue(' password ')
    await inputs[2].setValue(' password ')
    await inputs[3].setValue('setup-secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(fetch.mock.calls[0][1].headers.get('X-Setup-Token')).toBe('setup-secret')
    expect(fetch.mock.calls[1][1].headers.has('X-Setup-Token')).toBe(false)
    expect(auth.setupRequired).toBe(false)
    expect(router.currentRoute.value.path).toBe('/welcome')
  })
  it('offers add and skip after setup and reuses CarForm', async () => {
    setSession('admin-token', admin)
    await render(WelcomeView, '/welcome')
    expect(wrapper.find('a[href="/"]').text()).toBe('Skip for now')
    await wrapper.findAll('button').find(button => button.text() === 'Add a car').trigger('click')
    expect(wrapper.findComponent({ name: 'CarForm' }).exists()).toBe(true)
  })
  it('keeps the account signed in after changing its password', async () => {
    setSession('session-token', member)
    fetch.mockResolvedValue(new Response(null, { status: 204 }))
    await render(AccountView, '/account')
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue(' old pass ')
    await inputs[1].setValue(' new pass ')
    await inputs[2].setValue(' new pass ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ current_password: ' old pass ', new_password: ' new pass ' })
    expect(auth.token).toBe('session-token')
    expect(wrapper.text()).toContain('Password changed')
    expect(inputs.every(input => input.element.value === '')).toBe(true)
  })
  it('removes a protected view immediately on session loss', async () => {
    setSession('session-token', member)
    const router = await render(App)
    router.beforeEach(authGuard)
    expect(wrapper.text()).toContain('Private garage')
    setSession()
    await flushPromises()
    expect(wrapper.text()).not.toContain('Private garage')
    expect(router.currentRoute.value.path).toBe('/login')
  })
  it('creates users, confirms password reset, and requires confirmation before deletion', async () => {
    setSession('admin-token', admin)
    fetch.mockImplementation((url, init) => Promise.resolve(init.method === 'GET' ? json([admin, member]) : new Response(null, { status: 204 })))
    await render(AdminView, '/admin')
    const inputs = wrapper.findAll('input')
    await inputs[0].setValue(' New.User ')
    await inputs[1].setValue(' initial password ')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ username: 'new.user', password: ' initial password ' })
    await wrapper.findAll('button').find(button => button.text() === 'Reset password').trigger('click')
    const dialog = wrapper.find('[role="dialog"]')
    await dialog.findAll('input')[0].setValue(' replacement ')
    await dialog.findAll('input')[1].setValue(' replacement ')
    await dialog.find('form').trigger('submit')
    await flushPromises()
    const reset = fetch.mock.calls.find(([, init]) => init.method === 'PATCH')
    expect(reset[0]).toContain('/users/member/password')
    expect(JSON.parse(reset[1].body)).toEqual({ new_password: ' replacement ' })
    await wrapper.findAll('button').find(button => button.text() === 'Delete user').trigger('click')
    expect(fetch.mock.calls.some(([, init]) => init.method === 'DELETE')).toBe(false)
    await wrapper.find('[role="dialog"] form').trigger('submit')
    await flushPromises()
    expect(fetch.mock.calls.find(([, init]) => init.method === 'DELETE')[0]).toContain('/users/member')
  })
  it('can cancel deletion and reports admin API errors without removing users', async () => {
    setSession('admin-token', admin)
    fetch.mockResolvedValueOnce(json([admin, member]))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Deletion failed' }), { status: 500 }))
    await render(AdminView, '/admin')
    await wrapper.findAll('button').find(button => button.text() === 'Delete user').trigger('click')
    await wrapper.find('[role="dialog"]').findAll('button').find(button => button.text() === 'Cancel').trigger('click')
    expect(fetch).toHaveBeenCalledTimes(1)
    await wrapper.findAll('button').find(button => button.text() === 'Delete user').trigger('click')
    await wrapper.find('[role="dialog"] form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Deletion failed')
    expect(wrapper.findAll('.user-list li')).toHaveLength(2)
  })
})
