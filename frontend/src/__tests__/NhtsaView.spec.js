import { flushPromises, mount } from '@vue/test-utils'
import NhtsaView from '../views/NhtsaView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { carId: 'car-1' } })
}))

describe('NhtsaView', () => {
  it('renders recall campaign details and the VIN status link', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ _id: 'car-1', access: { is_owner: true } })
    }).mockResolvedValue({
      ok: true,
      json: async () => ({
        vin: '3VW547AUXHM054108',
        decode: {
          fields: {
            Make: 'VOLKSWAGEN',
            Model: 'Golf GTI',
            'Model Year': '2017'
          }
        },
        ratings: { selected: { OverallRating: '5' } },
        recalls: [{
          recall_number: '24V110',
          manufacturer_recall_number: '20UF',
          manufacturer: 'Volkswagen Group of America, Inc.',
          component: 'FUEL SYSTEM, GASOLINE',
          report_date: '14/02/2024',
          summary: 'Fuel may leak.',
          consequence: 'A fuel leak increases the risk of fire.',
          remedy: 'Dealers will replace the suction pump.',
          notes: 'Contact NHTSA.'
        }],
        recall_lookup_url: 'https://www.nhtsa.gov/recalls#vehicle',
        errors: {}
      })
    })

    const wrapper = mount(NhtsaView, {
      global: {
        stubs: {
          AccountControls: true,
          'router-link': true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('Golf GTI')
    expect(wrapper.text()).toContain('24V110')
    expect(wrapper.text()).toContain('20UF')
    expect(wrapper.text()).toContain('FUEL SYSTEM, GASOLINE')
    expect(wrapper.find('.lookup-link').attributes('href')).toBe('https://www.nhtsa.gov/recalls#vehicle')
  })
})
