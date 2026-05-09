import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import HelloWorld from '@/components/HelloWorld.vue'

describe('HelloWorld', () => {
  it('renders provided message', () => {
    const wrapper = mount(HelloWorld, { props: { msg: 'Hi Test' } })
    expect(wrapper.text()).toContain('Hi Test')
  })
})
