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
})
