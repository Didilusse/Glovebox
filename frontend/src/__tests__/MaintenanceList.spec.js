import { mount } from '@vue/test-utils'

import MaintenanceList from '../components/MaintenanceList.vue'


describe('MaintenanceList', () => {
  it('distinguishes an empty history from an empty search result', () => {
    expect(mount(MaintenanceList).text()).toContain('No service history yet')
    expect(mount(MaintenanceList, { props: { hasRecords: true } }).text()).toContain('No matching service records')
  })
})
