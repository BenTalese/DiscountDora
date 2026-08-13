<template>
    <!-- Switcher (owner 2026-08-13): the reconcile surface depends on the
         install-wide posture. AUTO ⇒ a read-only log of what Dora did; MANUAL
         ⇒ the confirm-each runner. The dashboard chip / settings button both
         deep-link here, so they land on the right view automatically. We wait
         for the health-derived policy so we never flash the wrong surface. -->
    <q-page v-if="!reconcilePolicyLoaded" class="reconcile-switch-loading">
        <q-spinner color="primary" size="42px" />
    </q-page>
    <MealReconcileLog v-else-if="autoDrain" />
    <MealReconcileRunner v-else />
</template>

<script lang="ts" setup>
    import { useReconcilePolicy } from 'src/composables/useReconcilePolicy';
    import MealReconcileLog from 'src/pages/MealReconcileLog.vue';
    import MealReconcileRunner from 'src/pages/MealReconcileRunner.vue';

    const { autoDrain, reconcilePolicyLoaded } = useReconcilePolicy();
</script>

<style scoped lang="scss">
    .reconcile-switch-loading {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
