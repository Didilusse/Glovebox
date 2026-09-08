import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import CarDetailView from '../views/CarDetailView.vue'
import MaintenanceView from '../views/MaintenanceView.vue'
import ModsView from '../views/ModsView.vue'
import NhtsaView from '../views/NhtsaView.vue'
import CarList from '../components/CarList.vue'
import ModsBoard from '../components/ModsBoard.vue'
import MaintenanceHeader from '../components/MaintenanceHeader.vue'
import MaintenanceList from '../components/MaintenanceList.vue'
import ModsHeader from '../components/ModsHeader.vue'
import App from '../App.vue'
import { auth, setSession } from '../utils/auth'

const access = (maintenance = 'view', mods = 'view', vehicle = 'view') => ({ is_owner: false, owner_username: 'owner', permissions: { vehicle, maintenance, mods } })
const vehicle = (permissions = access()) => ({ _id: 'car-1', make: 'Toyota', model: 'Camry', year: 2020, access: permissions })
const log = { _id: 'log-1', work_done: 'Oil change', date_of_service: '2026-01-01', cost: 50 }
const mod = { _id: 'mod-1', name: 'Wheels', status: 'planned', position: 0 }
const reminder = { log_id: 'log-1', work_done: 'Oil change', interval_miles: 5000, interval_months: 6 }
const json = (data, status = 200) => new Response(JSON.stringify(data), { status })
let wrapper
beforeEach(() => {
  setSession('token', { username: 'member' })
  Object.assign(auth, { ready: true, setupRequired: false })
  vi.stubGlobal('fetch', vi.fn())
})
afterEach(() => { wrapper?.unmount(); vi.unstubAllGlobals() })
async function render(component, path) {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/car/:carId', component: CarDetailView },
    { path: '/maintenance/:carId', component: MaintenanceView },
    { path: '/mods/:carId', component: ModsView },
    { path: '/nhtsa/:carId', component: NhtsaView },
    { path: '/', component: { template: '<p>Garage</p>' } }
  ] })
  await router.push(path)
  wrapper = mount(component, { global: { plugins: [router], stubs: { AccountControls: true } } })
  await flushPromises()
  return router
}
function respond(car) {
  fetch.mockImplementation(async url => {
    if (/\/cars\/[^/]+$/.test(url)) return json(car)
    if (url.includes('/logs/')) return json([log])
    if (url.includes('/reminders/')) return json([reminder])
    if (url.includes('/stats/')) return json({ log_count: 1 })
    if (url.includes('/planned-mods/')) return json([mod])
    if (url.includes('/nhtsa/')) return json({ recalls: [] })
    throw new Error(`Unexpected request: ${url}`)
  })
}

describe('vehicle permission boundaries', () => {
  it.each([[MaintenanceView, '/maintenance/car-1', 'maintenance'], [ModsView, '/mods/car-1', 'mods']])('suppresses denied direct section requests', async (view, path, section) => {
    respond(vehicle(access('none', 'none')))
    await render(view, path)
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain(`You do not have access to ${section}`)
    expect(wrapper.find('a[href="/maintenance/car-1"]').exists()).toBe(false)
    expect(wrapper.find('a[href="/mods/car-1"]').exists()).toBe(false)
    expect(wrapper.find('a[href="/nhtsa/car-1"]').exists()).toBe(true)
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('waits for access before fetching any section data', async () => {
    let resolve
    fetch.mockReturnValueOnce(new Promise(done => { resolve = done })).mockResolvedValue(json([]))
    await render(MaintenanceView, '/maintenance/car-1')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.add-button').exists()).toBe(false)
    resolve(json(vehicle()))
    await flushPromises()
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it('hides dashboard statistics, reminders and owner actions when not permitted', async () => {
    respond(vehicle(access('none', 'edit')))
    await render(CarDetailView, '/car/car-1')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Shared by owner')
    expect(wrapper.find('.car-stats').exists()).toBe(false)
    expect(wrapper.find('.car-reminders').exists()).toBe(false)
    expect(wrapper.find('.vehicle-actions').findAll('button')).toHaveLength(0)
    expect(wrapper.find('a[href="/mods/car-1"]').exists()).toBe(true)
  })

  it('shows read-only maintenance without add, import, edit or delete controls and rejects emitted mutations', async () => {
    respond(vehicle())
    await render(MaintenanceView, '/maintenance/car-1')
    expect(wrapper.text()).toContain('Oil change')
    expect(wrapper.text()).toContain('Read-only maintenance')
    expect(wrapper.find('.record-actions').exists()).toBe(false)
    expect(wrapper.find('.import-button').exists()).toBe(false)
    expect(wrapper.find('.add-button').exists()).toBe(false)
    wrapper.findComponent(MaintenanceHeader).vm.$emit('add')
    wrapper.findComponent(MaintenanceHeader).vm.$emit('import')
    wrapper.findComponent(MaintenanceList).vm.$emit('edit', log)
    wrapper.findComponent(MaintenanceList).vm.$emit('delete', log._id)
    await flushPromises()
    expect(wrapper.find('form').exists()).toBe(false)
    expect(fetch.mock.calls.every(([, init]) => !init.method)).toBe(true)
  })

  it('shows read-only mods without mutation controls and disables drag/drop', async () => {
    respond(vehicle(access('none', 'view')))
    await render(ModsView, '/mods/car-1')
    expect(wrapper.text()).toContain('Wheels')
    expect(wrapper.find('.drag-handle').exists()).toBe(false)
    expect(wrapper.find('.edit').exists()).toBe(false)
    expect(wrapper.find('.delete').exists()).toBe(false)
    expect(wrapper.find('.add-button').exists()).toBe(false)
    const board = wrapper.findComponent(ModsBoard)
    const lists = board.findAllComponents({ name: 'draggable' })
    expect(lists).toHaveLength(3)
    expect(lists.every(item => item.vm._sortable.option('disabled'))).toBe(true)
    board.vm.$emit('move', { modId: mod._id, status: 'installed', position: 0 })
    board.vm.$emit('edit', mod)
    board.vm.$emit('delete', mod._id)
    wrapper.findComponent(ModsHeader).vm.$emit('add')
    await flushPromises()
    expect(wrapper.find('form').exists()).toBe(false)
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('allows section editors to delete records without granting vehicle ownership', async () => {
    respond(vehicle(access('edit', 'none')))
    await render(MaintenanceView, '/maintenance/car-1')
    expect(wrapper.find('.import-button').exists()).toBe(true)
    expect(wrapper.find('.add-button').exists()).toBe(true)
    expect(wrapper.find('.edit').exists()).toBe(true)
    await wrapper.find('.delete').trigger('click')
    await flushPromises()
    expect(fetch.mock.calls.some(([url, init]) => url.endsWith('/logs/log-1') && init.method === 'DELETE')).toBe(true)
  })

  it('allows mod editors to delete and move parts independently of maintenance', async () => {
    respond(vehicle(access('none', 'edit')))
    await render(ModsView, '/mods/car-1')
    expect(wrapper.find('.drag-handle').exists()).toBe(true)
    expect(wrapper.find('.add-button').exists()).toBe(true)
    const board = wrapper.findComponent(ModsBoard)
    board.vm.$emit('move', { modId: mod._id, status: 'installed', position: 0 })
    await flushPromises()
    expect(fetch.mock.calls.some(([url, init]) => url.endsWith('/mod-1/move') && init.method === 'PATCH')).toBe(true)
    await wrapper.find('.delete').trigger('click')
    await flushPromises()
    expect(fetch.mock.calls.some(([url, init]) => url.endsWith('/planned-mods/mod-1') && init.method === 'DELETE')).toBe(true)
  })

  it('shows vehicle editing to vehicle editors, but sharing only to owners', async () => {
    respond(vehicle(access('view', 'none', 'edit')))
    await render(CarDetailView, '/car/car-1')
    expect(wrapper.text()).toContain('Edit vehicle')
    expect(wrapper.text()).not.toContain('manage sharing')
    expect(wrapper.text()).not.toContain('Edit reminder')
    await wrapper.find('.vehicle-actions button').trigger('click')
    expect(wrapper.find('dialog').exists()).toBe(true)
  })

  it('gives owners every section and dashboard action regardless of permission values', async () => {
    respond(vehicle({ ...access('none', 'none'), is_owner: true }))
    await render(CarDetailView, '/car/car-1')
    expect(wrapper.text()).toContain('manage sharing')
    expect(wrapper.text()).toContain('Edit vehicle')
    await wrapper.find('#reminders-tab').trigger('click')
    expect(wrapper.text()).toContain('Edit reminder')
    expect(fetch).toHaveBeenCalledTimes(3)
    expect(wrapper.text()).not.toContain('Shared by')
  })

  it('never offers collaborators car deletion in the garage', () => {
    wrapper = mount(CarList, { props: { inventory: [vehicle()] } })
    expect(wrapper.text()).toContain('Shared by owner')
    expect(wrapper.find('.delete').exists()).toBe(false)
  })

  it.each([403, 404, 500])('fails closed when vehicle access returns %s', async status => {
    fetch.mockResolvedValue(json({ detail: 'Unavailable' }, status))
    await render(MaintenanceView, '/maintenance/car-1')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Unable to load vehicle access')
    expect(wrapper.find('.maintenance-list').exists()).toBe(false)
  })

  it('fails closed when a response omits access metadata', async () => {
    respond({ _id: 'car-1', make: 'Toyota' })
    await render(ModsView, '/mods/car-1')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.findComponent(ModsBoard).exists()).toBe(false)
    expect(wrapper.find('a[href="/maintenance/car-1"]').exists()).toBe(false)
  })

  it('rejects an old account section response after switching sessions', async () => {
    let resolve
    fetch.mockResolvedValueOnce(json(vehicle(access('none', 'view'))))
      .mockReturnValueOnce(new Promise(done => { resolve = done }))
      .mockResolvedValue(json({ detail: 'Forbidden' }, 403))
    await render(App, '/mods/car-1')
    setSession('second-token', { username: 'second' })
    await flushPromises()
    resolve(json([{ ...mod, name: 'Private old account part' }]))
    await flushPromises()
    expect(wrapper.text()).not.toContain('Private old account part')
    expect(wrapper.text()).not.toContain('Toyota')
    expect(wrapper.findComponent(ModsBoard).exists()).toBe(false)
  })

  it('does not reuse another vehicle or account access after navigation and failed requests', async () => {
    respond(vehicle({ ...access(), is_owner: true }))
    const router = await render(App, '/car/car-1')
    expect(wrapper.text()).toContain('manage sharing')
    fetch.mockResolvedValue(json({ detail: 'Forbidden' }, 403))
    await router.push('/car/car-2')
    await flushPromises()
    expect(wrapper.text()).not.toContain('Toyota')
    expect(wrapper.text()).not.toContain('manage sharing')
    expect(wrapper.find('a[href="/maintenance/car-2"]').exists()).toBe(false)
    setSession('second-token', { username: 'second' })
    await flushPromises()
    expect(wrapper.text()).not.toContain('Toyota')
    expect(wrapper.text()).not.toContain('manage sharing')
    expect(fetch.mock.calls.at(-1)[1].headers.get('Authorization')).toBe('Bearer second-token')
  })

  it('keeps safety available with maintenance and mods denied', async () => {
    respond(vehicle(access('none', 'none')))
    await render(NhtsaView, '/nhtsa/car-1')
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('No NHTSA campaigns found')
    expect(wrapper.find('a[href="/maintenance/car-1"]').exists()).toBe(false)
    expect(wrapper.find('a[href="/mods/car-1"]').exists()).toBe(false)
  })
})
