import { mount } from '@vue/test-utils'
import MaintenanceLogCard from '../components/MaintenanceLogCard.vue'

const log = {
  _id: 'log-1',
  date_of_service: '2026-05-14',
  mileage: 85420,
  cost: 189.5,
  work_done: 'Brake fluid flush',
  category: 'brakes',
  done_by: 'shop',
  service_provider: 'Apex Motorworks',
  reminder_date: '2028-05-14',
  reminder_mileage: 105420,
  notes: 'Used DOT 4 fluid',
  source: 'carfax'
}

describe('MaintenanceLogCard', () => {
  it('prioritizes service identity, scan values, and next-service details', async () => {
    const wrapper = mount(MaintenanceLogCard, { props: { log } })

    expect(wrapper.text()).toContain('May')
    expect(wrapper.text()).toContain('14')
    expect(wrapper.text()).toContain('Brake fluid flush')
    expect(wrapper.text()).toContain('Apex Motorworks')
    expect(wrapper.text()).toContain('85,420 mi')
    expect(wrapper.text()).toContain('$189.50')
    expect(wrapper.text()).toContain('105,420 mi')

    await wrapper.get('.edit').trigger('click')
    await wrapper.get('.delete').trigger('click')
    expect(wrapper.emitted('edit')[0][0]).toEqual(log)
    expect(wrapper.emitted('delete')[0][0]).toBe('log-1')
  })
})
