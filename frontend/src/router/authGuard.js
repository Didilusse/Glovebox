import { auth, initializeAuth } from '../utils/auth'

export async function authGuard(to) {
  await initializeAuth()
  if (!auth.ready) return to.path === '/auth' ? true : '/auth'
  if (auth.setupRequired) return to.path === '/setup' ? true : '/setup'
  if (!auth.user) return to.path === '/login' ? true : '/login'
  if (['/login', '/setup', '/auth'].includes(to.path)) return '/'
  if (to.meta.admin && !auth.user.is_admin) return '/'
  return true
}
