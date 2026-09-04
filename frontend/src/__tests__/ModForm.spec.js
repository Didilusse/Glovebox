import { mount } from '@vue/test-utils'
import ModForm from '../components/ModForm.vue'

describe('ModForm', () => {
  it('validates required values before creating a part', async () => {
    const wrapper = mount(ModForm)

    await wrapper.find('#mod-name').setValue('')
    await wrapper.find('#mod-cost').setValue('-1')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('created')).toBeFalsy()
    expect(wrapper.text()).toContain('Part name is required.')
    expect(wrapper.text()).toContain('Enter a cost of zero or more.')
  })

  it('prefills and emits all editable part fields', async () => {
    const wrapper = mount(ModForm, {
      props: {
        mode: 'edit',
        mod: {
          name: 'Coilovers',
          type: 'modification',
          category: 'suspension',
          status: 'purchased',
          cost: 950,
          priority: 'high',
          install_method: 'shop',
          part_number: '35220001',
          target_date: '2026-06-15',
          brand: 'KW',
          url: 'https://example.com/coilovers',
          notes: 'Install next weekend'
        }
      }
    })

    expect(wrapper.find('#mod-name').element.value).toBe('Coilovers')
    expect(wrapper.find('#mod-status').element.value).toBe('purchased')
    expect(wrapper.find('#mod-priority').element.value).toBe('high')
    expect(wrapper.find('#mod-part-number').element.value).toBe('35220001')
    await wrapper.find('#mod-status').setValue('installed')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('updated')[0][0]).toEqual({
      name: 'Coilovers',
      type: 'modification',
      category: 'suspension',
      status: 'installed',
      cost: 950,
      priority: 'high',
      install_method: 'shop',
      part_number: '35220001',
      target_date: '2026-06-15',
      brand: 'KW',
      url: 'https://example.com/coilovers',
      notes: 'Install next weekend'
    })
  })
})
