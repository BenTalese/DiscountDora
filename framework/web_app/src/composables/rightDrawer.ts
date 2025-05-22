import type { Component } from 'vue';
import { ref } from 'vue';

const isRightDrawerOpen = ref(false);
const rightDrawerContent = ref<Component | null>(null);

export function useRightDrawer() {
    return {
        isRightDrawerOpen,
        rightDrawerContent
    };
}
