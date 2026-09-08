import { safeExternalUrl } from '../utils/url'

describe('safeExternalUrl', () => {
  it('allows HTTPS links and rejects insecure or active schemes', () => {
    expect(safeExternalUrl('https://example.com/path')).toBe('https://example.com/path')
    expect(safeExternalUrl('http://example.com/')).toBe('')
    expect(safeExternalUrl('javascript:alert(1)')).toBe('')
    expect(safeExternalUrl('data:text/html,test')).toBe('')
    expect(safeExternalUrl('not a URL')).toBe('')
  })
})
