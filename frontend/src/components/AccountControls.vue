<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { auth, logout } from '../utils/auth'

const busy = ref(false)
const notificationsOpen = ref(false)
const accountOpen = ref(false)
const controls = ref(null)
const userInitial = computed(() => auth.user?.username?.charAt(0).toUpperCase() || '?')

function toggleNotifications() {
  notificationsOpen.value = !notificationsOpen.value
  accountOpen.value = false
}

function toggleAccount() {
  accountOpen.value = !accountOpen.value
  notificationsOpen.value = false
}

function closeMenus() {
  notificationsOpen.value = false
  accountOpen.value = false
}

function handleDocumentClick(event) {
  if (!controls.value?.contains(event.target)) closeMenus()
}

async function signOut() {
  if (busy.value) return
  busy.value = true
  closeMenus()
  await logout()
  busy.value = false
}

onMounted(() => document.addEventListener('click', handleDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', handleDocumentClick))
</script>

<template>
  <div v-if="auth.user" ref="controls" class="account-controls" @keydown.esc="closeMenus">
    <div class="menu-anchor">
      <button
        type="button"
        class="icon-trigger"
        :class="{ active: notificationsOpen }"
        :aria-expanded="notificationsOpen"
        aria-haspopup="menu"
        aria-label="Notifications"
        @click="toggleNotifications"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
        </svg>
      </button>
      <transition name="menu-pop">
        <section v-if="notificationsOpen" class="dropdown notifications-menu" role="menu">
          <div class="dropdown-heading">
            <strong>Notifications</strong>
            <span>Updates from your garage</span>
          </div>
          <div class="empty-notifications">
            <span class="empty-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>
            </span>
            <strong>You're all caught up</strong>
            <span>No new notifications.</span>
          </div>
        </section>
      </transition>
    </div>

    <span class="controls-divider" aria-hidden="true"></span>

    <div class="menu-anchor account-anchor">
      <button
        type="button"
        class="account-trigger"
        :class="{ active: accountOpen }"
        :aria-expanded="accountOpen"
        aria-haspopup="menu"
        @click="toggleAccount"
      >
        <span class="account-avatar" aria-hidden="true">{{ userInitial }}</span>
        <span class="account-copy">
          <span class="account-label">Account</span>
          <strong>{{ auth.user.username }}</strong>
        </span>
        <svg class="chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5" /></svg>
      </button>
      <transition name="menu-pop">
        <section v-if="accountOpen" class="dropdown account-menu" role="menu">
          <div class="account-summary">
            <span class="account-avatar large" aria-hidden="true">{{ userInitial }}</span>
            <div>
              <strong>{{ auth.user.username }}</strong>
              <span>{{ auth.user.is_admin ? 'Administrator' : 'Glovebox user' }}</span>
            </div>
          </div>
          <div class="menu-links">
            <router-link to="/account" role="menuitem" @click="closeMenus">
              <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg>
              <span><strong>Settings</strong></span>
            </router-link>
            <router-link to="/welcome" role="menuitem" @click="closeMenus">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 1.8 5.6h5.9l-4.8 3.5 1.8 5.6-4.7-3.5-4.8 3.5 1.8-5.6-4.7-3.5h5.9L12 3Z" /></svg>
              <span><strong>Get started</strong></span>
            </router-link>
            <router-link v-if="auth.user.is_admin" to="/admin" role="menuitem" @click="closeMenus">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>
              <span><strong>Users</strong></span>
            </router-link>
          </div>
          <button class="logout-action" role="menuitem" :disabled="busy" @click="signOut">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" /></svg>
            {{ busy ? 'Signing out...' : 'Log out' }}
          </button>
        </section>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.account-controls { position: relative; display: flex; align-items: center; gap: 8px; min-width: 0; }
.menu-anchor { position: relative; }
.account-anchor { min-width: 0; }
.icon-trigger, .account-trigger { min-height: 42px; border: 1px solid transparent; border-radius: 11px; background: transparent; color: var(--gb-text-muted); cursor: pointer; transition: .18s ease; }
.icon-trigger:hover, .icon-trigger.active, .account-trigger:hover, .account-trigger.active { border-color: var(--gb-border); background: var(--gb-surface); color: var(--gb-heading); }
.icon-trigger { width: 42px; display: grid; place-items: center; padding: 0; }
.icon-trigger svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.7; }
.controls-divider { width: 1px; height: 24px; background: var(--gb-border); }
.account-trigger { max-width: 210px; display: flex; align-items: center; gap: 9px; padding: 4px 8px 4px 5px; text-align: left; }
.account-avatar { width: 31px; height: 31px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid rgba(179, 199, 255, .28); border-radius: 9px; background: rgba(179, 199, 255, .12); color: var(--gb-accent); font-size: .76rem; font-weight: 800; }
.account-avatar.large { width: 38px; height: 38px; border-radius: 11px; font-size: .86rem; }
.account-copy { min-width: 0; display: grid; line-height: 1.15; }
.account-label { color: var(--gb-text-muted); font-size: .61rem; font-weight: 650; letter-spacing: .07em; text-transform: uppercase; }
.account-copy strong { overflow: hidden; color: inherit; font-size: .82rem; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.chevron { width: 15px; height: 15px; flex: 0 0 auto; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.8; transition: transform .18s ease; }
.account-trigger.active .chevron { transform: rotate(180deg); }
.dropdown { position: absolute; z-index: 100; top: calc(100% + 10px); right: 0; overflow: hidden; border: 1px solid var(--gb-border); border-radius: 14px; background: #191d23; box-shadow: 0 18px 45px rgba(0, 0, 0, .38); }
.notifications-menu { width: min(330px, calc(100vw - 28px)); }
.account-menu { width: min(285px, calc(100vw - 28px)); }
.dropdown-heading { display: grid; padding: 17px 18px 14px; border-bottom: 1px solid var(--gb-border); }
.dropdown-heading strong, .account-summary strong { color: var(--gb-heading); font-weight: 700; }
.dropdown-heading span, .account-summary span, .empty-notifications span { color: var(--gb-text-muted); font-size: .76rem; }
.empty-notifications { display: grid; justify-items: center; padding: 30px 20px 32px; text-align: center; }
.empty-notifications strong { margin: 10px 0 2px; color: var(--gb-heading); font-weight: 650; }
.empty-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; background: var(--gb-surface); }
.empty-icon svg { width: 20px; fill: none; stroke: var(--gb-text-muted); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.6; }
.account-summary { display: flex; align-items: center; gap: 11px; padding: 16px; border-bottom: 1px solid var(--gb-border); }
.account-summary div { min-width: 0; display: grid; }
.account-summary strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.menu-links { padding: 7px; }
.account-controls .menu-links a, .logout-action { width: 100%; display: flex; align-items: center; gap: 11px; border: 0; border-radius: 9px; background: transparent; color: var(--gb-text); font: inherit; text-align: left; cursor: pointer; }
.account-controls .menu-links a { padding: 10px; }
.account-controls .menu-links a:hover, .account-controls .menu-links a.router-link-active, .logout-action:hover { background: var(--gb-surface-hover); color: var(--gb-heading); }
.menu-links svg, .logout-action svg { width: 18px; height: 18px; flex: 0 0 auto; fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.7; }
.menu-links span { display: grid; line-height: 1.25; }
.menu-links strong { color: inherit; font-size: .85rem; font-weight: 650; }
.logout-action { padding: 12px 17px; border-top: 1px solid var(--gb-border); border-radius: 0; color: var(--gb-danger); }
.logout-action:disabled { cursor: wait; opacity: .55; }
.menu-pop-enter-active, .menu-pop-leave-active { transition: opacity .14s ease, transform .14s ease; transform-origin: top right; }
.menu-pop-enter-from, .menu-pop-leave-to { opacity: 0; transform: translateY(-4px) scale(.98); }
@media (max-width: 700px) {
  .account-controls { width: 100%; justify-content: flex-end; padding-top: 10px; border-top: 1px solid var(--gb-border); }
  .account-anchor { min-width: 0; }
  .account-trigger { max-width: min(230px, calc(100vw - 95px)); }
  .dropdown { position: fixed; top: 76px; right: 14px; }
}
</style>
