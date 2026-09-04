import { flushPromises, mount } from '@vue/test-utils'
import MaintenanceHeader from '../components/MaintenanceHeader.vue'
import MaintenanceImport from '../components/MaintenanceImport.vue'


describe('CARFAX maintenance import', () => {
  it('emits the import action from the maintenance header', async () => {
    const wrapper = mount(MaintenanceHeader)
    await wrapper.get('.import-button').trigger('click')
    expect(wrapper.emitted('import')).toHaveLength(1)
  })

  it('summarizes service status and history in the maintenance header', () => {
    const wrapper = mount(MaintenanceHeader, {
      props: {
        car: { make: 'Honda', model: 'Accord', mileage: 108707 },
        maintenances: [
          { date_of_service: '2026-02-01', cost: 120 },
          { date_of_service: '2025-06-01', cost: 80 }
        ],
        reminders: [{ work_done: 'Oil change', is_due: true }]
      }
    })

    expect(wrapper.text()).toContain('Honda Accord service history')
    expect(wrapper.text()).toContain('Oil change is due')
    expect(wrapper.text()).toContain('108,707 mi')
    expect(wrapper.text()).toContain('$200')
    expect(wrapper.text()).toContain('Feb 1, 2026')
  })

  it('previews a PDF and confirms selected records', async () => {
    const preview = {
      report: { vin: '1HGCP3F89BA028384', vehicle: '2011 Honda Accord EX-L V6' },
      summary: { found: 2, new: 1, duplicates: 1, missing_mileage: 1 },
      warnings: [],
      records: [
        {
          date_of_service: '2025-12-29', mileage: 108707, cost: null, done_by: 'shop',
          work_done: 'Oil and filter changed; Tires rotated', category: 'other',
          notes: 'Imported from CARFAX', service_provider: 'Valvoline', source_record_key: 'a'.repeat(64),
          source_page: 8, warnings: [], duplicate: false
        },
        {
          date_of_service: '2025-02-01', mileage: null, cost: null, done_by: 'shop',
          work_done: 'Oil and filter changed', category: 'fluids', notes: 'Imported from CARFAX',
          service_provider: 'Valvoline', source_record_key: 'b'.repeat(64), source_page: 8,
          warnings: ['Mileage was not reported by CARFAX'], duplicate: true
        }
      ]
    }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => preview })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ created: 1, skipped_duplicates: 0 }) })
    vi.stubGlobal('fetch', fetchMock)

    const wrapper = mount(MaintenanceImport, { props: { carId: 'car-1', apiBase: 'http://api' } })
    const file = new File(['%PDF-test'], 'carfax.pdf', { type: 'application/pdf' })
    const input = wrapper.get('#carfax-file')
    Object.defineProperty(input.element, 'files', { configurable: true, value: [file] })
    await input.trigger('change')
    await wrapper.get('.primary').trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls[0][0]).toBe('http://api/cars/car-1/logs/import/preview')
    expect(fetchMock.mock.calls[0][1].body).toBeInstanceOf(FormData)
    expect(wrapper.text()).toContain('2 found')
    expect(wrapper.text()).toContain('Already imported')

    const importButton = wrapper.findAll('.primary').find(button => button.text().includes('Import 1 records'))
    await importButton.trigger('click')
    await flushPromises()

    const confirmBody = JSON.parse(fetchMock.mock.calls[1][1].body)
    expect(confirmBody.report_vin).toBe('1HGCP3F89BA028384')
    expect(confirmBody.records).toHaveLength(1)
    expect(confirmBody.records[0].work_done).toContain('Oil and filter changed')
    expect(wrapper.emitted('imported')[0][0]).toEqual({ created: 1, skipped_duplicates: 0 })
    vi.unstubAllGlobals()
  })
})
