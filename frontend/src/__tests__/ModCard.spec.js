import { mount } from '@vue/test-utils'
import ModCard from '../components/ModCard.vue'

const mod = {
  _id: 'mod-1',
  name: 'Cat-back exhaust',
  type: 'modification',
  category: 'exhaust',
  cost: 725,
  priority: 'high',
  install_method: 'diy',
  part_number: '140496',
  target_date: '2026-10-12',
  brand: 'Borla',
  url: 'https://example.com/exhaust',
  notes: 'Check tip clearance'
}

describe('ModCard', () => {
  it('renders part details and emits card actions', async () => {
    const wrapper = mount(ModCard, { props: { mod } })

    expect(wrapper.text()).toContain('Borla')
    expect(wrapper.text()).toContain('Cat-back exhaust')
    expect(wrapper.text()).toContain('Exhaust')
    expect(wrapper.text()).toContain('High priority')
    expect(wrapper.text()).toContain('DIY install')
    expect(wrapper.text()).toContain('140496')
    expect(wrapper.find('a').attributes('href')).toBe(mod.url)

    await wrapper.get('button:not(.delete)').trigger('click')
    await wrapper.get('button.delete').trigger('click')

    expect(wrapper.emitted('edit')[0][0]).toEqual(mod)
    expect(wrapper.emitted('delete')[0][0]).toBe('mod-1')
  })
})
