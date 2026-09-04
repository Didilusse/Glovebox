import { mount } from '@vue/test-utils'
import ModsHeader from '../components/ModsHeader.vue'

describe('ModsHeader', () => {
  it('summarizes build progress and actionable spend', () => {
    const wrapper = mount(ModsHeader, {
      props: {
        carName: 'BMW M3',
        mods: [
          { status: 'planned', cost: 800 },
          { status: 'purchased', cost: 1200 },
          { status: 'installed', cost: 500 }
        ]
      }
    })

    expect(wrapper.text()).toContain('BMW M3 build')
    expect(wrapper.text()).toContain('1 of 3 installed')
    expect(wrapper.text()).toContain('33%')
    expect(wrapper.text()).toContain('$2,500')
    expect(wrapper.text()).toContain('$800')
    expect(wrapper.get('[role="progressbar"]').attributes('aria-valuenow')).toBe('33')
  })
})
