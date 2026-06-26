<template>
    <q-card flat bordered class="first-run-card q-mx-auto">
        <q-card-section class="text-center q-py-xl">
            <q-icon :name="ICONS.menu_book" size="48px" class="dora-text-muted q-mb-md" />
            <div class="text-h5 q-mb-sm">Add recipes to start planning</div>
            <div class="text-body2 dora-text-muted q-mb-lg" style="max-width: 32rem; margin-inline: auto;">
                Meal plans build a week from recipes in your cookbook. Add a few
                recipes first — then come back here to plan them.
            </div>
            <BaseButton
                :icon="ICONS.add"
                label="Go to Cookbook"
                @click="goToCookbook"
            />
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    function goToCookbook() {
        void router.push('/cookbook');
    }
</script>

<style scoped>
    .first-run-card {
        max-width: 36rem;
        margin-top: 4rem;
    }
</style>
