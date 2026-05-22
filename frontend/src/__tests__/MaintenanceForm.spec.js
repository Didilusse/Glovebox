import { mount } from '@vue/test-utils'
import MaintenanceForm from '../components/MaintenanceForm.vue'

describe('MaintenanceForm', () => {
  it('prefills edit values and emits reminder fields with the update payload', async () => {
    const wrapper = mount(MaintenanceForm, {
      props: {
        mode: 'edit',
        maintenance: {
          date_of_service: '2026-05-01',
          mileage: 12000,
          cost: 89.5,
          done_by: 'shop',
          category: 'fluids',
          work_done: 'Oil change',
          notes: 'Changed filter too',
          interval_months: 6,
          interval_miles: 5000
        }
      }
    })

    expect(wrapper.find('#work_done').element.value).toBe('Oil change')
    expect(wrapper.find('#interval_months').element.value).toBe('6')

    await wrapper.find('#work_done').setValue('Oil change and inspection')
    await wrapper.find('#interval_months').setValue('12')
    await wrapper.find('#interval_miles').setValue('7500')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('updated')).toBeTruthy()
    expect(wrapper.emitted('updated')[0][0]).toMatchObject({
      date_of_service: '2026-05-01',
      mileage: 12000,
      cost: 89.5,
      done_by: 'shop',
      category: 'fluids',
      work_done: 'Oil change and inspection',
      notes: 'Changed filter too',
      interval_months: 12,
      interval_miles: 7500
    })
  })
})