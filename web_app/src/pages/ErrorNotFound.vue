<template>
    <div class="fullscreen not-found-page text-center q-pa-md flex flex-center">
        <div>
            <div style="font-size: 30vh">404</div>

            <div
                class="text-h2"
                style="opacity: 0.4"
            >
                Oops. Nothing here...
            </div>

            <q-btn
                class="q-mt-xl not-found-btn"
                unelevated
                to="/"
                label="Go Home"
                no-caps
            />
        </div>
    </div>
</template>

<script setup lang="ts"></script>

<style scoped>
    .not-found-page {
        background: var(--surface-toolbar);
        color: var(--text-on-toolbar);
    }
    .not-found-btn {
        background: var(--text-on-toolbar);
        color: var(--surface-toolbar);
    }
</style>
