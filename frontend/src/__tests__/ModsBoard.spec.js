import { mount } from '@vue/test-utils'
import ModsBoard from '../components/ModsBoard.vue'

const mods = [
  { _id: 'planned-2', name: 'Second', status: 'planned', position: 1, type: 'modification', category: 'engine', cost: 20 },
  { _id: 'installed-1', name: 'Installed', status: 'installed', position: 0, type: 'maintenance', category: 'fluids', cost: 30 },
  { _id: 'planned-1', name: 'First', status: 'planned', position: 0, type: 'modification', category: 'brakes', cost: 10 }
]

describe('ModsBoard', () => {
  it('groups cards into ordered workflow columns', () => {
    const wrapper = mount(ModsBoard, { props: { mods } })
    const columns = wrapper.findAll('.column')

    expect(columns).toHaveLength(3)
    expect(columns[0].text()).toContain('Planned')
    expect(columns[0].findAll('.mod-card').map(card => card.text())).toEqual([
      expect.stringContaining('First'),
      expect.stringContaining('Second')
    ])
    expect(columns[1].text()).toContain('Drop a part here')
    expect(columns[2].text()).toContain('Installed')
  })

  it('emits the destination and index from a drag change', () => {
    const wrapper = mount(ModsBoard, { props: { mods } })

    wrapper.vm.handleChange({
      added: { element: mods[0], newIndex: 0 }
    }, 'purchased')

    expect(wrapper.emitted('move')[0][0]).toEqual({
      modId: 'planned-2',
      status: 'purchased',
      position: 0
    })
  })
})
