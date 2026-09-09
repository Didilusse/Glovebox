import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import CarForm from '../components/CarForm.vue'


describe('CarForm', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('submits the backend snake_case contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ _id: 'car-1' })
    })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    expect(wrapper.text()).toContain('Import CARFAX')
    const mainInputs = wrapper.findAll('.form-left input')
    await mainInputs[0].setValue('2020')
    await mainInputs[1].setValue('Toyota')
    await mainInputs[2].setValue('Camry')
    await mainInputs[3].setValue('ABC-123')

    const advancedInputs = wrapper.findAll('.advanced-options input')
    await advancedInputs[3].setValue('50000')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const request = fetchMock.mock.calls[0][1]
    expect(JSON.parse(request.body)).toEqual({
      make: 'Toyota',
      model: 'Camry',
      year: 2020,
      mileage: 50000,
      fuel_type: 'gas',
      license_plate: 'ABC-123'
    })
  })

  it('selects a fuel type from the fuel selector', async () => {
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    const electricOption = wrapper.get('input[value="electric"]')

    expect(wrapper.get('input[value="gas"]').element.checked).toBe(true)
    await electricOption.setValue(true)

    expect(electricOption.element.checked).toBe(true)
    expect(wrapper.get('.fuel-option.active').text()).toBe('Electric')
  })

  it('normalizes and validates the VIN check digit', async () => {
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    await wrapper.get('.advanced-toggle').trigger('click')
    const vinInput = wrapper.get('input[aria-describedby="vin-validation"]')

    await vinInput.setValue('1hg cm82633a004352')
    await vinInput.trigger('blur')
    expect(vinInput.element.value).toBe('1HGCM82633A004352')
    expect(wrapper.get('.field-valid').text()).toBe('Valid VIN')

    await vinInput.setValue('1HGCM82643A004352')
    expect(wrapper.get('.field-error').text()).toBe('VIN check digit does not match')
  })

  it('warns when a valid VIN decodes to a different vehicle', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ make: 'HONDA', model: 'Accord', year: '2003', fields: { Make: 'HONDA', Model: 'Accord', 'Model Year': '2003' } })
    }))
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    const mainInputs = wrapper.findAll('.form-left input')
    await mainInputs[0].setValue('2020')
    await mainInputs[1].setValue('Toyota')
    await mainInputs[2].setValue('Camry')
    await wrapper.get('.advanced-toggle').trigger('click')
    const vinInput = wrapper.get('input[aria-describedby="vin-validation"]')

    await vinInput.setValue('1HGCM82633A004352')
    await vinInput.trigger('blur')
    await flushPromises()

    expect(wrapper.get('.vin-warning').text()).toContain('2003 HONDA Accord')
  })

  it('keeps purchase prices formatted to two decimal places', async () => {
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    await wrapper.get('.advanced-toggle').trigger('click')
    const priceInput = wrapper.get('input[inputmode="decimal"]')

    await priceInput.setValue('2000.1')
    await priceInput.trigger('blur')

    expect(priceInput.element.value).toBe('2000.10')
  })

  it('allows negative purchase prices and sends them as numbers', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ _id: 'car-1' }) })
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    const mainInputs = wrapper.findAll('.form-left input')
    await mainInputs[0].setValue('2020')
    await mainInputs[1].setValue('Toyota')
    await mainInputs[2].setValue('Camry')
    await wrapper.get('.advanced-toggle').trigger('click')
    const priceInput = wrapper.get('input[inputmode="decimal"]')

    await priceInput.setValue('-100.10')
    await priceInput.trigger('blur')
    expect(priceInput.element.value).toBe('-100.10')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(JSON.parse(fetchMock.mock.calls[0][1].body).purchased_price).toBe(-100.1)
  })

  it('removes non-digits from mileage as the user types', async () => {
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    await wrapper.get('.advanced-toggle').trigger('click')
    const mileageInput = wrapper.get('input[aria-describedby="mileage-error"]')

    await mileageInput.setValue('12abc.34')

    expect(mileageInput.element.value).toBe('1234')
  })

  it('reveals and highlights an invalid price on submit', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    await wrapper.get('.advanced-toggle').trigger('click')
    const priceInput = wrapper.get('input[inputmode="decimal"]')
    await priceInput.setValue('not-a-price')
    await priceInput.trigger('blur')
    await wrapper.get('.advanced-toggle').trigger('click')

    expect(wrapper.get('.advanced-error-summary').text()).toBe('Needs attention')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.get('.advanced-toggle').attributes('aria-expanded')).toBe('true')
    expect(priceInput.attributes('aria-invalid')).toBe('true')
    expect(wrapper.get('#purchased-price-error').text()).toBe('Enter a valid price')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows server field validation in the form', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ loc: ['body', 'purchased_price'], msg: 'Value error, Price was rejected' }] })
    }))
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    const mainInputs = wrapper.findAll('.form-left input')
    await mainInputs[0].setValue('2020')
    await mainInputs[1].setValue('Toyota')
    await mainInputs[2].setValue('Camry')

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.get('.advanced-toggle').attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('#purchased-price-error').text()).toBe('Price was rejected')
  })

  it('forwards an imported CARFAX car to the garage', async () => {
    const wrapper = mount(CarForm, { props: { apiBase: 'http://api.test' } })
    await wrapper.findAll('.method-picker button')[1].trigger('click')
    const importedCar = { _id: 'car-imported', make: 'Honda' }

    wrapper.getComponent({ name: 'CarfaxCarImport' }).vm.$emit('created', {
      car: importedCar,
      created: 29
    })
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('created')[0][0]).toEqual(importedCar)
  })
})
