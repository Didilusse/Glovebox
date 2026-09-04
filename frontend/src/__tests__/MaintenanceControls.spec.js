import { mount } from '@vue/test-utils'

import MaintenanceControls from '../components/MaintenanceControls.vue'


describe('MaintenanceControls', () => {
  it('emits search, category, sort, and clear updates', async () => {
    const wrapper = mount(MaintenanceControls, { props: { search: 'oil', sort: 'recent' } })
    await wrapper.get('input[type="search"]').setValue('brakes')
    await wrapper.get('.select-field:not(.sort-field) select').setValue('brakes')
    await wrapper.get('.sort-field select').setValue('cost-low')
    await wrapper.get('.clear').trigger('click')

    expect(wrapper.emitted('update:search').map(event => event[0])).toEqual(['brakes', ''])
    expect(wrapper.emitted('update:category')[0][0]).toBe('brakes')
    expect(wrapper.emitted('update:sort')[0][0]).toBe('cost-low')
  })
})
