import { mount } from '@vue/test-utils'
import CarList from '../components/CarList.vue'

describe('CarList', () => {
  it('renders cars and emits add when the add card is clicked', async () => {
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

    await wrapper.find('.add-car-card').trigger('click')

    expect(wrapper.emitted('add')).toBeTruthy()
  })
})