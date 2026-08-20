<template>
    <q-select
        v-bind="forwardedAttrs"
        :model-value="modelValue"
        :options="options"
        :behavior="resolvedBehavior"
        :use-input="resolvedUseInput"
        outlined
        dense
        @update:model-value="(v: TValue) => emit('update:modelValue', v)"
    >
        <!-- Close affordance, dialog case only. Quasar's select dialog has no
             X and no Done — the only way out is the backdrop, which on a phone
             is a ~19px strip down each side and a ~54px band top and bottom
             (from its own `width: 90vw` / `max-height: calc(100vh - 108px)`).
             Those are real targets but awkward ones, and the bottom band is
             exactly where the browser toolbar and home indicator sit. With
             `use-input` the software keyboard takes most of what's left.
             That is the "difficult to tap out of" the owner reported. -->
        <template v-if="showsDialog" #before-options>
            <div class="base-select__dialog-bar row items-center justify-between">
                <span class="base-select__dialog-title">{{ dialogTitle }}</span>
                <BaseButton
                    variant="icon"
                    :icon="ICONS.close"
                    aria-label="Close"
                    v-close-popup
                />
            </div>
        </template>

        <!-- Everything else the call site passed through untouched. -->
        <template v-for="(_, name) in passthroughSlots" #[name]="slotProps">
            <slot :name="name" v-bind="slotProps ?? {}" />
        </template>
    </q-select>
</template>

<script setup lang="ts" generic="TValue">
    /*
     * The app's single-select control.
     *
     * Exists to make ONE decision in one place: menu or dialog on mobile.
     * Before this, all 72 `q-select`s left `behavior` unset, so every one took
     * Quasar's default — and that default is **user-agent based, not viewport
     * based** (`$q.platform.is.mobile`, QSelect.js `updatePreState`). So a
     * desktop browser dragged to phone width still gets an anchored menu while
     * a real phone gets a full-screen dialog; you cannot see the mobile
     * behaviour by resizing. Meanwhile the tri-state filters render their own
     * `q-menu` and are never dialogs. Hence the owner's report: "most dropdowns
     * open a modal, but our custom ones behave normally."
     *
     * The rule, rather than a blanket flip either way:
     *
     *   short, closed vocabulary  → `menu`   (Difficulty, Theme mode, cadence…)
     *   long list, or `use-input` → `default` (dialog on mobile, menu on desktop)
     *
     * Because the two cases genuinely differ. A five-option menu anchored to a
     * field is faster and less disruptive than a modal takeover — that's the
     * style the owner prefers, and there's no reason a phone should get a
     * full-screen surface to pick "Easy / Medium / Hard". But a long or
     * typeahead list needs the room and needs to survive the software keyboard,
     * which is exactly the problem the dialog exists to solve; forcing those
     * into an anchored menu on a phone would trade a mild annoyance for a
     * genuinely cramped one.
     */
    import { computed, useAttrs, useSlots } from 'vue';
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    defineOptions({ inheritAttrs: false });

    const props = withDefaults(
        defineProps<{
            modelValue: TValue;
            /** Option rows. Deliberately `unknown` rather than `any`: the shape
             *  is the call site's business (string, {label,value}, a domain
             *  entity with `option-label`/`option-value` fns), and this
             *  component only ever reads `.length` off it. */
            options: readonly unknown[];
            /** Typeahead. Mirrors `q-select`'s own prop name because the
             *  behaviour rule has to read it — which means Vue consumes it and
             *  it is NO LONGER in `$attrs`, so it must be forwarded explicitly
             *  above. Missing that silently disabled the typeahead on the stock
             *  location picker while leaving it looking fine. */
            useInput?: boolean;
            /** Force a behaviour, escaping the rule. Use only with a reason. */
            behavior?: 'default' | 'menu' | 'dialog';
            /** Heading shown beside the close button in the dialog case. */
            dialogTitle?: string;
        }>(),
        { useInput: false, dialogTitle: 'Choose an option' },
    );

    const emit = defineEmits<{ (e: 'update:modelValue', value: TValue): void }>();

    const $q = useQuasar();
    const slots = useSlots();

    /**
     * Where "short" stops. Quasar's mobile select dialog is capped at
     * `calc(100vh - 108px)`; at ~48px per option that's roughly 14 rows on a
     * 812px phone before it scrolls. An anchored menu has less room than that,
     * so the cutoff sits well below it: at 8 options a menu opens fully visible
     * next to the field on a phone, which is the whole point of preferring one.
     */
    const MENU_MAX_OPTIONS = 8;

    const resolvedBehavior = computed<'default' | 'menu' | 'dialog'>(() => {
        if (props.behavior) return props.behavior;
        // A typeahead list is unbounded by definition — its option count at
        // rest says nothing about what the user will filter it down from.
        if (props.useInput) return 'default';
        return props.options.length <= MENU_MAX_OPTIONS ? 'menu' : 'default';
    });

    /** True only when a dialog will actually render — mirrors QSelect's own
     *  condition so the close bar can't appear in a menu on desktop. */
    const showsDialog = computed(
        () => resolvedBehavior.value !== 'menu'
            && ($q.platform.is.mobile === true || resolvedBehavior.value === 'dialog'),
    );

    /**
     * Typeahead is desktop-only.
     *
     * Owner report 2026-08-20: *"all dropdown filters here open as mid-screen
     * modals except for location which opens at the top. Only difference I can
     * see is that the keyboard also opens up for this one."* Exactly that —
     * `use-input` makes QSelect's dialog auto-focus its input, the software
     * keyboard comes up, and Quasar pins the dialog to the top of the viewport
     * to keep it clear. One picker behaving unlike its four neighbours, for a
     * feature that isn't worth much on a phone anyway: filtering a location
     * list by thumb-typing is slower than scrolling it, and the keyboard eats
     * the room the list was given.
     *
     * The list is still a dialog rather than an anchored menu — `useInput`
     * keeps driving `resolvedBehavior` above, because a typeahead list is
     * unbounded by definition and needs the room. Only the input is dropped.
     */
    const resolvedUseInput = computed(
        () => props.useInput && $q.platform.is.mobile !== true,
    );

    /**
     * `$attrs`, minus the two props that only make sense alongside the
     * typeahead. `hide-selected` + `fill-input` are how a `use-input` select
     * shows the chosen option *in* its input; leave them on when the input is
     * gone (see `resolvedUseInput`) and the trigger renders blank with a
     * value selected. Both spellings are stripped — a template may pass
     * either, and Vue hands them through verbatim.
     */
    const attrs = useAttrs();
    const forwardedAttrs = computed(() => {
        if (resolvedUseInput.value) return attrs;
        const out: Record<string, unknown> = { ...attrs };
        for (const key of ['hide-selected', 'hideSelected', 'fill-input', 'fillInput']) {
            delete out[key];
        }
        return out;
    });

    /** Forward every slot the caller gave us EXCEPT the one we own. */
    const passthroughSlots = computed(() => {
        const out: Record<string, true> = {};
        for (const name of Object.keys(slots)) {
            if (name === 'before-options') continue;
            out[name] = true;
        }
        return out;
    });
</script>

<style scoped lang="scss">
    .base-select__dialog-bar {
        position: sticky;
        top: 0;
        z-index: 1;
        padding: 4px 4px 4px 16px;
        background: var(--surface-elevated);
        border-bottom: 1px solid var(--border-subtle);
    }
    .base-select__dialog-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-secondary);
    }
</style>
