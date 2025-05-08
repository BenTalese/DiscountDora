<template>
    <q-btn
        :class="{ isHovering }"
        :to="link"
        class="nav-btn q-mx-xs"
        flat
        no-caps
        stack
    >
        <q-icon
            :name="icon"
            class="nav-icon"
            size="45px"
        />
        <div class="nav-label">
            {{ label }}
        </div>
    </q-btn>
</template>

<script setup lang="ts">
    //#region Props and Events
    export interface MainMenuButtonProps {
        isHovering: boolean;
        icon: string;
        label: string;
        link: string;
    }

    defineProps({
        isHovering: { type: Boolean, required: true },
        icon: { type: String, required: true },
        label: { type: String, required: true },
        link: { type: String, required: true }
    });
    //#endregion Props and Events
</script>

<style scoped>
    .nav-btn {
        width: 130px;
        /* transition: background-color 0.3s ease; */
    }

    .nav-icon {
        transition:
            transform 0.5s ease,
            margin 0.5s ease;
    }

    .nav-btn.isHovering .nav-icon {
        margin-bottom: 4px;
        transform: scale(0.7);
    }

    .nav-label {
        font-size: 0.65rem;
        font-weight: bold;
        max-height: 0;
        line-height: 1;
        opacity: 0;
        overflow: hidden;
        transform: translateY(10px);
        transition:
            opacity 0.5s ease,
            max-height 0.5s ease,
            font-size 0.5s ease,
            transform 0.5s ease;
        white-space: nowrap;
    }

    .nav-btn.isHovering .nav-label {
        font-size: 0.9rem;
        max-height: 30px;
        opacity: 1;
        transform: translateY(-8px);
    }
</style>
