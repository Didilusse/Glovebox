import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import { setSession } from '../utils/auth'

describe('HomeView', () => {
  afterEach(() => {
    setSession()
    vi.unstubAllGlobals()
  })

  it('requires confirmation before deleting a vehicle', async () => {
    setSession('owner-token', { username: 'owner' })
    const car = { _id: 'car-1', year: 2020, make: 'Toyota', model: 'Camry', mileage: 50000, access: { is_owner: true } }
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([car]), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: HomeView }, { path: '/car/:carId', component: { template: '<div />' } }] })
    await router.push('/')
    await router.isReady()
    const wrapper = mount(HomeView, { global: { plugins: [router], stubs: { AccountControls: true, DueAlerts: true } } })
    await flushPromises()

    await wrapper.get('.delete').trigger('click')
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(wrapper.get('.delete-confirmation').text()).toContain('2020 Toyota Camry')

    await wrapper.get('.confirm-delete').trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls[1][1].method).toBe('DELETE')
    expect(wrapper.text()).not.toContain('Toyota Camry')
    wrapper.unmount()
  })
})
