<script setup lang="ts">
// import ErrorPopup from '@/components/ErrorPopup.vue';
// import { onErrorCaptured, ref } from 'vue';
import { RouterLink, RouterView } from 'vue-router';

// const errorMessage = ref('');
// onErrorCaptured((err) => {
//     errorMessage.value = 'An error occurred: ' + err.message;
//     return false;
// });

</script>

<template>
    <div class="container">
        <header>
            <!-- <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="125" height="125" /> -->
            <nav class="nav nav-tabs flex-column">
                <div class="container-fluid">
                    <RouterLink class="navbar-brand" to="/">
                        <!-- <a class="nav-link active" href="#" aria-current="page">Active link</a> -->
                        <!-- TODO: Logo -->
                        Home
                    </RouterLink>
                    <RouterLink class="nav-link" to="/about">About</RouterLink>
                </div>
            </nav>
        </header>
        <!-- <ErrorPopup :msg="errorMessage" /> -->
        <RouterView />
    </div>
</template>

<!-- <style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
</style> -->
