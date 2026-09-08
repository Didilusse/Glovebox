<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CarForm from '../components/CarForm.vue'
import NavBar from '../components/NavBar.vue'
import { API_BASE } from '../utils/auth'
const adding = ref(false)
const router = useRouter()
</script>
<template>
  <NavBar />
  <main class="welcome-page" :class="{ 'showing-form': adding }">
    <section v-if="!adding" class="welcome-content" aria-labelledby="welcome-title">
      <div class="garage-mark" aria-hidden="true">
        <svg viewBox="0 0 80 80" fill="none">
          <path d="M12 64V28L40 14l28 14v36M22 64V34h36v30M23 42h34M23 50h34" />
          <path d="M26 65v-7l4-8h20l4 8v7M26 58h28M30 64h3M47 64h3" />
        </svg>
        <span class="ready-mark"><svg viewBox="0 0 24 24"><path d="m6 12 4 4 8-8" /></svg></span>
      </div>
      <span class="welcome-eyebrow">Welcome to Glovebox</span>
      <h1 id="welcome-title">Your garage is ready.</h1>
      <p class="welcome-description">A home for your cars and everything that keeps them running. Add a vehicle to start keeping track.</p>
      <div class="welcome-actions">
        <button class="auth-button" @click="adding = true">Add a car</button>
        <router-link to="/">Skip for now</router-link>
      </div>
      <p class="welcome-note">No rush. You can always add a car from your garage later.</p>
    </section>
    <section v-else class="welcome-form" aria-label="Add a car">
      <CarForm :api-base="API_BASE" @created="router.replace('/')" @close="adding = false" />
    </section>
  </main>
</template>

<style scoped>
.welcome-page {
  min-height: calc(100svh - 70px);
  display: grid;
  place-items: center;
  padding: 64px 24px 88px;
}

.welcome-content {
  width: min(100%, 600px);
  text-align: center;
}

.garage-mark {
  position: relative;
  width: 108px;
  height: 108px;
  display: grid;
  place-items: center;
  margin: 0 auto 36px;
  border: 1px solid var(--gb-border-strong);
  border-radius: 28px;
  background: var(--gb-surface);
  color: var(--gb-accent);
}

.garage-mark > svg { width: 76px; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.ready-mark { position: absolute; right: -8px; bottom: -6px; width: 32px; height: 32px; display: grid; place-items: center; border: 4px solid var(--gb-background); border-radius: 50%; background: var(--gb-accent); }
.ready-mark svg { width: 20px; fill: none; stroke: var(--gb-background-deep); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.welcome-eyebrow { color: var(--gb-accent); font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.welcome-content h1 { margin: 14px 0 20px; color: var(--gb-heading); font-size: clamp(2.1rem, 5vw, 3.4rem); font-weight: 700; line-height: 1.12; letter-spacing: -.035em; }
.welcome-description { max-width: 440px; margin: 0 auto; color: var(--gb-text-muted); font-size: 1.05rem; line-height: 1.75; }
.welcome-actions { display: flex; justify-content: center; align-items: center; gap: 14px; margin-top: 34px; }
.welcome-actions .auth-button, .welcome-actions a { min-height: 48px; padding: 12px 26px; border-radius: 999px; font-size: .92rem; font-weight: 650; }
.welcome-actions a { border: 1px solid var(--gb-border); color: var(--gb-text); }
.welcome-actions .auth-button:hover { background: var(--gb-accent-hover); }
.welcome-actions a:hover { background: var(--gb-surface); color: var(--gb-heading); }
.welcome-actions :focus-visible { outline: 2px solid var(--gb-accent); outline-offset: 4px; }
.welcome-note { max-width: 350px; margin: 24px auto 0; color: var(--gb-text-muted); font-size: .8rem; line-height: 1.6; }
.welcome-form { width: min(100%, 900px); }
.showing-form { align-items: start; }

@media (max-width: 480px) {
  .welcome-page { padding: 48px 20px; }
  .garage-mark { margin-bottom: 28px; }
  .welcome-actions { flex-direction: column; align-items: stretch; gap: 12px; }
  .welcome-description { font-size: .96rem; }
  .welcome-note { margin-top: 22px; }
  .showing-form { padding: 24px 12px; }
}
</style>
