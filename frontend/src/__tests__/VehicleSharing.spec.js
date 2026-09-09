import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import VehicleSharing from '../components/VehicleSharing.vue'
import VehicleEdit from '../components/VehicleEdit.vue'
import { setSession } from '../utils/auth'

const permissions = { vehicle: 'view', maintenance: 'view', mods: 'view' }
const car = { _id: 'car-1', make: 'Toyota', model: 'Camry', year: 2020, mileage: 50000, access: { is_owner: true } }
const grant = { _id: 'share-1', user_id: 'user-2', username: 'friend', permissions }
const json = (body, status = 200) => new Response(JSON.stringify(body), { status })
let wrapper
beforeEach(() => {
  setSession('owner-token', { username: 'owner' })
  vi.stubGlobal('fetch', vi.fn())
})
afterEach(() => { wrapper?.unmount(); vi.unstubAllGlobals() })

describe('vehicle sharing', () => {
  it('lists recipients, adds a normalized exact username with view defaults, edits and revokes', async () => {
    fetch.mockResolvedValueOnce(json([]))
    wrapper = mount(VehicleSharing, { props: { car } })
    await flushPromises()
    expect(fetch.mock.calls[0][0]).toMatch(/\/cars\/car-1\/shares\/$/)
    expect(wrapper.text()).toContain('No recipients yet')
    expect(wrapper.findAll('select').map(select => select.element.value)).toEqual(['view', 'view', 'view'])
    expect(wrapper.findAll('select')[0].find('option[value="none"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Service logs, reminders and statistics')
    await wrapper.find('input').setValue(' Friend ')
    fetch.mockResolvedValueOnce(json(grant, 201))
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ username: 'friend', permissions })
    expect(wrapper.find('.recipients').text()).toContain('friend')
    await wrapper.findAll('button').find(button => button.text() === 'Edit friend').trigger('click')
    await wrapper.findAll('select')[1].setValue('none')
    await wrapper.findAll('select')[2].setValue('edit')
    const edited = { ...permissions, maintenance: 'none', mods: 'edit' }
    fetch.mockResolvedValueOnce(json({ ...grant, permissions: edited }))
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(fetch.mock.calls[2][0]).toMatch(/\/shares\/user-2$/)
    expect(fetch.mock.calls[2][1].method).toBe('PUT')
    expect(JSON.parse(fetch.mock.calls[2][1].body)).toEqual({ permissions: edited })
    expect(wrapper.find('.recipients').text()).toContain('Maintenance: none / Mods: edit')
    fetch.mockResolvedValueOnce(new Response(null, { status: 204 }))
    await wrapper.findAll('button').find(button => button.text() === 'Revoke friend').trigger('click')
    await flushPromises()
    expect(fetch.mock.calls[3][1].method).toBe('DELETE')
    expect(wrapper.text()).toContain('No recipients yet')
  })

  it('shows server errors without claiming that a grant was added', async () => {
    fetch.mockResolvedValueOnce(json([])).mockResolvedValueOnce(json({ detail: 'User not found' }, 404))
    wrapper = mount(VehicleSharing, { props: { car } })
    await flushPromises()
    await wrapper.find('input').setValue('missing')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('User not found')
    expect(wrapper.find('.recipients').text()).toContain('No recipients yet')
  })

  it('retains the saved grant when edits or revocation are rejected', async () => {
    fetch.mockResolvedValueOnce(json([grant]))
      .mockResolvedValueOnce(json({ detail: 'Forbidden' }, 403))
      .mockResolvedValueOnce(json({ detail: 'Unable to revoke' }, 500))
    wrapper = mount(VehicleSharing, { props: { car } })
    await flushPromises()
    await wrapper.findAll('button').find(button => button.text() === 'Edit friend').trigger('click')
    await wrapper.findAll('select')[1].setValue('edit')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Forbidden')
    expect(wrapper.find('.recipients').text()).toContain('Maintenance: view')
    await wrapper.findAll('button').find(button => button.text() === 'Revoke friend').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Unable to revoke')
    expect(wrapper.find('.recipients').text()).toContain('friend')
  })

  it('rejects invalid usernames without a request', async () => {
    fetch.mockResolvedValueOnce(json([]))
    wrapper = mount(VehicleSharing, { props: { car } })
    await flushPromises()
    await wrapper.find('input').setValue('not a username')
    await wrapper.find('form').trigger('submit')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.find('[role="alert"]').text()).toContain('valid existing username')
  })

  it('does not fetch shares or render grant controls for a collaborator', async () => {
    wrapper = mount(VehicleSharing, { props: { car: { ...car, access: { is_owner: false, permissions } } } })
    await flushPromises()
    expect(fetch).not.toHaveBeenCalled()
    expect(wrapper.find('dialog').exists()).toBe(false)
  })

  it('hides the dialog and rejects in-flight recipients after a session change', async () => {
    let resolve
    fetch.mockReturnValueOnce(new Promise(done => { resolve = done }))
    wrapper = mount(VehicleSharing, { props: { car } })
    setSession('other-token', { username: 'other' })
    resolve(json([grant]))
    await flushPromises()
    expect(wrapper.find('dialog').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('friend')
  })

  it('keeps failed recipient loading closed until retry succeeds', async () => {
    fetch.mockResolvedValueOnce(json({ detail: 'Forbidden' }, 403)).mockResolvedValueOnce(json([grant]))
    wrapper = mount(VehicleSharing, { props: { car } })
    await flushPromises()
    expect(wrapper.find('form').exists()).toBe(false)
    await wrapper.findAll('button').find(button => button.text().includes('Retry')).trigger('click')
    await flushPromises()
    expect(wrapper.find('.recipients').text()).toContain('friend')
  })
})

describe('vehicle editing', () => {
  it('shows purchase prices with two decimal places', async () => {
    wrapper = mount(VehicleEdit, { props: { car: { ...car, purchased_price: 2000.1 } } })
    const priceInput = wrapper.get('input[data-currency]')

    expect(priceInput.element.value).toBe('2000.10')
    await priceInput.setValue('1500.5')
    await priceInput.trigger('blur')
    expect(priceInput.element.value).toBe('1500.50')
  })

  it('preserves negative currency formatting and filters mileage while typing', async () => {
    wrapper = mount(VehicleEdit, { props: { car: { ...car, purchased_price: -100.1 } } })
    const priceInput = wrapper.get('input[data-currency]')
    const mileageInput = wrapper.get('#edit-mileage')

    expect(priceInput.element.value).toBe('-100.10')
    await mileageInput.setValue('50k.25')
    expect(mileageInput.element.value).toBe('5025')
  })

  it('allows vehicle editors to save schema fields without sending access metadata', async () => {
    const editable = { ...car, access: { is_owner: false, permissions: { ...permissions, vehicle: 'edit' } } }
    wrapper = mount(VehicleEdit, { props: { car: editable } })
    await wrapper.findAll('input')[0].setValue('Honda')
    fetch.mockResolvedValueOnce(json({ ...editable, make: 'Honda' }))
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(fetch.mock.calls[0][1].method).toBe('PATCH')
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ make: 'Honda', model: 'Camry', year: 2020, mileage: 50000 })
    expect(wrapper.emitted('updated')[0][0].make).toBe('Honda')
  })

  it.each([['year', '1800'], ['mileage', '-1'], ['mileage', '1.5'], ['purchased_price', 'invalid'], ['purchased_date', '2999-01-01']])('rejects invalid %s %s', async (field, value) => {
    wrapper = mount(VehicleEdit, { props: { car: { ...car, [field]: value } } })
    await wrapper.find('form').trigger('submit')
    expect(fetch).not.toHaveBeenCalled()
    expect(wrapper.find('[role="alert"]').exists()).toBe(true)
  })

  it('does not show a vehicle form to read-only collaborators', () => {
    wrapper = mount(VehicleEdit, { props: { car: { ...car, access: { is_owner: false, permissions } } } })
    expect(wrapper.find('form').exists()).toBe(false)
  })
})
