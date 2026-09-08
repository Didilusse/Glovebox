import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import SettingsView from '../views/SettingsView.vue'
import CarDetailView from '../views/CarDetailView.vue'
import ReminderCard from '../components/ReminderCard.vue'
import DueAlerts from '../components/DueAlerts.vue'
import AccountControls from '../components/AccountControls.vue'
import MaintenanceForm from '../components/MaintenanceForm.vue'
import { setSession } from '../utils/auth'

const settings = { oil_interval_miles: 5000, oil_interval_months: 6, webhook_url: null, discord_webhook_url: null, email: null, email_available: false }
const reminder = { log_id: 'log-1', car_id: 'car-1', car_name: 'Shared Toyota', work_done: 'Oil change', interval_miles: 5000, interval_months: 6, progress_miles: 100, progress_time: 45, is_due: true, is_overdue: true }
const notification = { _id: 'n-1', car_id: 'car-1', log_id: 'log-1', title: 'Oil change due', message: 'Service your Toyota', created_at: '2026-09-01T12:00:00Z', read: false }
const json = (data, status = 200) => new Response(JSON.stringify(data), { status })
let wrapper
beforeEach(() => { setSession('token', { username: 'owner' }); vi.stubGlobal('fetch', vi.fn()) })
afterEach(() => { wrapper?.unmount(); vi.useRealTimers(); vi.unstubAllGlobals() })
async function render(component, props = {}, path = '/') {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/', component: { template: '<p>Home</p>' } },
    { path: '/car/:carId', component: { template: '<p>Dashboard</p>' } },
    { path: '/settings', component: SettingsView }, { path: '/account', component: { template: '<p>Password</p>' } },
    { path: '/:pathMatch(.*)*', component: { template: '<p>Page</p>' } }
  ] })
  await router.push(path)
  wrapper = mount(component, { props, attachTo: document.body, global: { plugins: [router], stubs: component === AccountControls ? {} : { AccountControls: true } } })
  await flushPromises()
  return router
}

describe('reminder settings', () => {
  it('loads defaults, exposes email availability and saves only editable fields including cleared destinations', async () => {
    fetch.mockImplementation(async () => json({ ...settings, webhook_url: 'https://example.com/private' }))
    await render(SettingsView)
    expect(wrapper.find('#oil-miles').element.value).toBe('5000')
    expect(wrapper.find('#email').element.disabled).toBe(true)
    await wrapper.find('#webhook').setValue('')
    await wrapper.find('#oil-months').setValue('9')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ oil_interval_miles: 5000, oil_interval_months: 9, webhook_url: null, discord_webhook_url: null, email: null })
    expect(wrapper.text()).toContain('Settings saved')
    expect(wrapper.find('a[href="/account"]').exists()).toBe(true)
  })
  it('rejects insecure webhooks and reports load and save errors with retry', async () => {
    fetch.mockRejectedValueOnce(new Error('offline')).mockResolvedValue(json(settings))
    await render(SettingsView)
    expect(wrapper.find('form').exists()).toBe(false)
    await wrapper.find('[role=alert] button').trigger('click'); await flushPromises()
    await wrapper.find('#discord').setValue('http://example.com/hook')
    await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(wrapper.find('[role=alert]').text()).toContain('HTTPS')
    expect(fetch).toHaveBeenCalledTimes(2)
    await wrapper.find('#discord').setValue('https://example.com/hook')
    fetch.mockResolvedValue(json({}, 500))
    await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(wrapper.find('[role=alert]').text()).toContain('Unable to save')
  })
})

describe('reminder cards and dashboard', () => {
  it('renders separate progress and overdue state and clears intervals explicitly', async () => {
    fetch.mockResolvedValue(new Response(null, { status: 204 }))
    await render(ReminderCard, { reminder, carId: 'car-1', editable: true })
    expect(wrapper.classes()).toContain('overdue')
    expect(wrapper.findAll('progress').map(p => p.attributes('value'))).toEqual(['100', '45'])
    await wrapper.find('button').trigger('click')
    for (const input of wrapper.findAll('input')) await input.setValue('')
    await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ interval_miles: null, interval_months: null })
    expect(wrapper.emitted('updated')).toHaveLength(1)
  })
  it('keeps failed edits open and exposes unavailable progress for read-only users', async () => {
    fetch.mockRejectedValue(new Error('offline'))
    await render(ReminderCard, { reminder, carId: 'car-1', editable: true })
    await wrapper.find('button').trigger('click'); await wrapper.find('form').trigger('submit'); await flushPromises()
    expect(wrapper.find('[role=alert]').text()).toContain('Unable to save')
    expect(wrapper.emitted('updated')).toBeUndefined()
    await wrapper.setProps({ editable: false, reminder: { ...reminder, progress_miles: null, progress_time: null } })
    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.find('progress').exists()).toBe(false)
    expect(wrapper.text()).toContain('Mileage progress unavailable')
  })
  it('shows only configured reminders, a due badge and keyboard-operable tabs', async () => {
    fetch.mockImplementation(async url => {
      if (url.includes('/reminders/')) return json([reminder, { log_id: 'unconfigured', work_done: 'Not scheduled' }])
      if (url.includes('/stats/')) return json({ log_count: 2 })
      return json({ _id: 'car-1', make: 'Toyota', access: { is_owner: true } })
    })
    await render(CarDetailView, {}, '/car/car-1')
    expect(wrapper.find('#reminders-tab').text()).toContain('1 due')
    expect(wrapper.find('#reminders-panel').isVisible()).toBe(false)
    await wrapper.find('#overview-tab').trigger('keydown', { key: 'ArrowRight' })
    await flushPromises()
    expect(wrapper.find('#reminders-tab').attributes('aria-selected')).toBe('true')
    expect(wrapper.find('#reminders-panel').isVisible()).toBe(true)
    expect(wrapper.findAllComponents(ReminderCard)).toHaveLength(1)
  })
  it('does not report no reminders on dashboard load failure and supports retry', async () => {
    fetch.mockImplementation(async url => {
      if (url.includes('/reminders/')) return json({}, 500)
      if (url.includes('/stats/')) return json({})
      return json({ _id: 'car-1', access: { is_owner: true } })
    })
    await render(CarDetailView, {}, '/car/car-1?tab=reminders')
    expect(wrapper.find('#reminders-panel [role=alert]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('No reminders configured')
    fetch.mockResolvedValue(json([]))
    await wrapper.find('#reminders-panel button').trigger('click'); await flushPromises()
    expect(wrapper.text()).toContain('No reminders configured')
  })
  it('links shared due alerts to the dashboard and distinguishes errors from an empty list', async () => {
    fetch.mockRejectedValueOnce(new Error('offline')).mockResolvedValue(json([reminder]))
    await render(DueAlerts)
    expect(wrapper.text()).not.toContain('No services currently due')
    await wrapper.find('button').trigger('click'); await flushPromises()
    expect(wrapper.find('a').attributes('href')).toBe('/car/car-1?tab=reminders')
    expect(wrapper.text()).toContain('Shared Toyota')
    expect(wrapper.text()).toContain('Overdue')
  })
})

describe('notifications', () => {
  it('polls every 60 seconds, marks read before navigation, and links settings separately', async () => {
    vi.useFakeTimers()
    fetch.mockImplementation(async (url, init) => init.method === 'PATCH' ? new Response(null, { status: 204 }) : json([{ ...notification }]))
    const router = await render(AccountControls)
    expect(wrapper.find('.unread-badge').text()).toBe('1')
    await vi.advanceTimersByTimeAsync(60000)
    expect(fetch).toHaveBeenCalledTimes(2)
    await wrapper.find('.icon-trigger').trigger('click')
    await wrapper.find('.notification-list button').trigger('click'); await flushPromises()
    expect(fetch.mock.calls[2][0]).toContain('/notifications/n-1/read')
    expect(router.currentRoute.value.fullPath).toBe('/car/car-1?tab=reminders')
    expect(wrapper.find('.unread-badge').exists()).toBe(false)
    await wrapper.find('.account-trigger').trigger('click')
    expect(wrapper.find('a[href="/settings"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/account"]').text()).toContain('password')
    wrapper.unmount(); wrapper = null
    await vi.advanceTimersByTimeAsync(60000)
    expect(fetch).toHaveBeenCalledTimes(3)
  })
  it('retains updates on refresh failure and does not navigate when marking read fails', async () => {
    vi.useFakeTimers()
    fetch.mockResolvedValueOnce(json([notification])).mockRejectedValue(new Error('offline'))
    const router = await render(AccountControls)
    await vi.advanceTimersByTimeAsync(60000)
    await wrapper.find('.icon-trigger').trigger('click')
    expect(wrapper.find('[role=alert]').text()).toContain('Updates may be missing')
    expect(wrapper.text()).not.toContain("You're all caught up")
    await wrapper.find('.notification-list button').trigger('click'); await flushPromises()
    expect(router.currentRoute.value.path).toBe('/')
    expect(wrapper.find('.unread-badge').text()).toBe('1')
    expect(wrapper.find('[role=alert]').text()).toContain('Unable to open')
  })
  it('discards old-session responses and stops polling on sign-out', async () => {
    vi.useFakeTimers()
    let resolve
    fetch.mockReturnValueOnce(new Promise(done => { resolve = done })).mockResolvedValue(json([]))
    await render(AccountControls)
    setSession('second', { username: 'second' }); await flushPromises()
    resolve(json([notification])); await flushPromises()
    await wrapper.find('.icon-trigger').trigger('click')
    expect(wrapper.text()).not.toContain(notification.title)
    expect(wrapper.find('.unread-badge').exists()).toBe(false)
    setSession(); await flushPromises()
    const calls = fetch.mock.calls.length
    await vi.advanceTimersByTimeAsync(120000)
    expect(fetch).toHaveBeenCalledTimes(calls)
  })
  it('shows initial and malformed-response errors instead of claiming no updates', async () => {
    fetch.mockResolvedValue(json({ invalid: true }))
    await render(AccountControls)
    await wrapper.find('.icon-trigger').trigger('click')
    expect(wrapper.find('[role=alert]').exists()).toBe(true)
    expect(wrapper.text()).not.toContain("You're all caught up")
  })
})

describe('oil defaults', () => {
  it('fetches settings only for new oil changes and allows clearing both intervals', async () => {
    fetch.mockResolvedValue(json(settings))
    await render(MaintenanceForm)
    expect(fetch).not.toHaveBeenCalled()
    await wrapper.find('#work_done').setValue('Engine oil and filter changed'); await flushPromises()
    expect(wrapper.find('#interval_miles').element.value).toBe('5000')
    expect(wrapper.find('#interval_months').element.value).toBe('6')
    await wrapper.find('#interval_miles').setValue('')
    await wrapper.find('#interval_months').setValue('')
    await wrapper.find('#mileage').setValue('10000'); await wrapper.find('#cost').setValue('50')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('created')[0][0]).toMatchObject({ interval_miles: null, interval_months: null })
  })
  it('does not overwrite edits or user choices with a late settings response', async () => {
    let resolve
    fetch.mockReturnValue(new Promise(done => { resolve = done }))
    await render(MaintenanceForm)
    await wrapper.find('#work_done').setValue('Oil change')
    await wrapper.find('input[type=checkbox]').setValue(true)
    await wrapper.find('#interval_miles').setValue('7500')
    resolve(json(settings)); await flushPromises()
    expect(wrapper.find('#interval_miles').element.value).toBe('7500')
    await wrapper.find('input[type=checkbox]').setValue(false)
    await wrapper.find('#work_done').setValue('Brakes'); await wrapper.find('#work_done').setValue('Oil changed')
    expect(wrapper.find('#interval_miles').exists()).toBe(false)
  })
  it('never fetches defaults while editing an existing oil log', async () => {
    await render(MaintenanceForm, { mode: 'edit', maintenance: { work_done: 'Oil change', interval_miles: 8000 } })
    await wrapper.find('#work_done').setValue('Brakes'); await wrapper.find('#work_done').setValue('Oil change')
    expect(fetch).not.toHaveBeenCalled()
    expect(wrapper.find('#interval_miles').element.value).toBe('8000')
  })
  it('keeps service entry usable if optional settings fetch fails', async () => {
    fetch.mockRejectedValue(new Error('offline'))
    await render(MaintenanceForm)
    await wrapper.find('#work_done').setValue('Oil change'); await flushPromises()
    expect(wrapper.text()).toContain('Could not load oil defaults')
    await wrapper.find('#mileage').setValue('10000'); await wrapper.find('#cost').setValue('50')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.emitted('created')[0][0]).toMatchObject({ interval_miles: null, interval_months: null })
  })
})
