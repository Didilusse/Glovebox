import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import CarfaxCarImport from '../components/CarfaxCarImport.vue'


describe('CarfaxCarImport', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('creates the parsed vehicle with every service record', async () => {
    const preview = {
      report: {
        vin: '1HGCP3F89BA028384', vehicle: '2011 HONDA ACCORD EX-L V6',
        year: 2011, make: 'Honda', model: 'ACCORD EX-L V6', fuel_type: 'gas'
      },
      summary: { found: 2, missing_mileage: 1, latest_mileage: 108707 },
      warnings: [],
      records: [
        {
          date_of_service: '2025-12-29', mileage: 108707, cost: null, done_by: 'shop',
          work_done: 'Oil and filter changed; Tires rotated', category: 'other',
          notes: 'Imported from CARFAX', service_provider: 'Valvoline', source_record_key: 'a'.repeat(64)
        },
        {
          date_of_service: '2023-04-11', mileage: null, cost: null, done_by: 'shop',
          work_done: 'A/C refrigerant recharged', category: 'other',
          notes: 'Imported from CARFAX', service_provider: "Ronnie's", source_record_key: 'b'.repeat(64)
        }
      ]
    }
    const result = { car: { _id: 'car-1', make: 'Honda' }, created: 2, skipped_duplicates: 0 }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => preview })
      .mockResolvedValueOnce({ ok: true, json: async () => result })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(CarfaxCarImport, { props: { apiBase: 'http://api.test' } })
    const input = wrapper.get('#new-car-carfax')
    const file = new File(['%PDF-test'], 'carfax.pdf', { type: 'application/pdf' })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })
    await input.trigger('change')
    await wrapper.get('.primary').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('2 service visits')
    expect(wrapper.get('input[type="number"]').element.value).toBe('2011')
    const addButton = wrapper.findAll('.primary').find(button => button.text().includes('Add car and 2 records'))
    await addButton.trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls[0][0]).toBe('http://api.test/cars/import/carfax/preview')
    expect(fetchMock.mock.calls[0][1].body).toBeInstanceOf(FormData)
    const payload = JSON.parse(fetchMock.mock.calls[1][1].body)
    expect(payload.vehicle).toMatchObject({
      year: 2011, make: 'Honda', model: 'ACCORD EX-L V6',
      vin: '1HGCP3F89BA028384', mileage: 108707
    })
    expect(payload.records).toHaveLength(2)
    expect(wrapper.emitted('created')[0][0]).toEqual(result)
  })
})
