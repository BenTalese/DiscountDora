<template>
    <div class="password-setter">
        <q-input
            v-if="!generate"
            :model-value="modelValue"
            outlined
            :label="label"
            :type="reveal ? 'text' : 'password'"
            autocomplete="new-password"
            :autofocus="autofocus"
            :error="!!error || tooShort"
            :error-message="error || (tooShort ? PASSWORD_HINT : '')"
            :hint="error || tooShort ? '' : PASSWORD_HINT"
            @update:model-value="onInput"
        >
            <template #append>
                <!-- Revealing is the point here: the admin is typing a password
                     they're about to say out loud to the person standing next
                     to them, so a hidden field they can't proof-read is the
                     wrong default-only option. Starts masked all the same. -->
                <q-icon
                    :name="reveal ? ICONS.visibility_off : ICONS.visibility"
                    class="cursor-pointer"
                    role="button"
                    tabindex="0"
                    :aria-label="reveal ? 'Hide password' : 'Show password'"
                    @click="reveal = !reveal"
                    @keydown.enter.prevent="reveal = !reveal"
                    @keydown.space.prevent="reveal = !reveal"
                />
            </template>
        </q-input>

        <q-toggle
            :model-value="generate"
            dense
            :label="generateLabel"
            @update:model-value="$emit('update:generate', $event)"
        />
        <div v-if="generate" class="text-caption dora-text-muted">
            Dora will invent one and show it to you once — copy it and pass it
            on out-of-band.
        </div>
    </div>
</template>

<script setup lang="ts">
    /**
     * One password field + a "let Dora generate one instead" escape hatch.
     *
     * Shared by Admin → Users' Add-user and Change-password dialogs (R-001 —
     * the two had identical needs and would otherwise have drifted). The
     * parent owns both halves of the state: `modelValue` (the typed password)
     * and `generate` (whether to ignore it and ask the server for one), so it
     * can decide what to send without reaching back in here.
     */
    import { ICONS } from 'src/style/icons';
    import { PASSWORD_HINT, MIN_PASSWORD_LENGTH } from 'src/models/password';
    import { computed, ref } from 'vue';

    const props = withDefaults(
        defineProps<{
            modelValue: string;
            generate: boolean;
            label?: string;
            generateLabel?: string;
            /** Server-side message for this field, if the save was rejected. */
            error?: string | undefined;
            autofocus?: boolean;
        }>(),
        {
            label: 'Password',
            generateLabel: 'Generate one instead',
            error: '',
            autofocus: false,
        },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: string): void;
        (e: 'update:generate', value: boolean): void;
        (e: 'input'): void;
    }>();

    const reveal = ref(false);

    // Only nag once they've started typing — an empty field on a freshly
    // opened dialog isn't an error, it's the starting state.
    const tooShort = computed(
        () => props.modelValue.length > 0
            && props.modelValue.length < MIN_PASSWORD_LENGTH,
    );

    function onInput(value: string | number | null) {
        emit('update:modelValue', String(value ?? ''));
        emit('input');
    }
</script>

<style scoped lang="scss">
    .password-setter {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
</style>
