import { mount } from '@vue/test-utils'
import CarList from '../components/CarList.vue'

describe('CarList', () => {
  it('renders cars and emits card actions', async () => {
    const wrapper = mount(CarList, {
      props: {
        inventory: [
          {
            _id: 'car-1',
            make: 'Toyota',
            model: 'Camry',
            year: 2020,
            mileage: 50000
          }
        ]
      }
    })

    expect(wrapper.text()).toContain('Toyota Camry')
    expect(wrapper.text()).toContain('50,000 miles')

    await wrapper.find('.view').trigger('click')
    await wrapper.find('.delete').trigger('click')
    await wrapper.find('.add-car-card').trigger('click')

    expect(wrapper.emitted('view')).toEqual([['car-1']])
    expect(wrapper.emitted('delete')).toEqual([['car-1']])
    expect(wrapper.emitted('add')).toEqual([[]])
  })
})
