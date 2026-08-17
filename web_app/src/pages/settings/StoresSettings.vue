<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Stores"
            description="The retail stores you actually shop at. Upload a logo so each store is recognisable on cards and lines."
            :icon="ICONS.store"
        >
            <template #actions>
                <BaseButton
                    :icon="ICONS.add"
                    label="Add store"
                    @click="openCreate"
                />
            </template>
        </SettingsPageHeader>

        <q-banner
            v-if="loadError"
            class="dora-bg-negative-soft text-negative q-mb-md"
            dense
            rounded
        >
            {{ loadError }}
        </q-banner>

        <q-list v-if="stores.length > 0" class="settings-list" separator>
            <q-item v-for="s in stores" :key="s.store_id">
                <q-item-section avatar>
                    <StoreLogo
                        :name="s.name"
                        :store-id="s.store_id"
                        :has-image="s.has_image"
                        :height="40"
                        :width="64"
                    />
                </q-item-section>
                <q-item-section>
                    <q-item-label>{{ s.name }}</q-item-label>
                    <q-item-label caption v-if="!s.has_image">
                        No logo uploaded — the hash-swatch fallback is shown.
                    </q-item-label>
                </q-item-section>
                <q-item-section side>
                    <div class="row q-gutter-xs">
                        <BaseButton
                            variant="icon"
                            :icon="ICONS.edit"
                            @click="openEdit(s)"
                        >
                            <q-tooltip>Edit</q-tooltip>
                        </BaseButton>
                        <BaseButton
                            variant="icon"
                            :icon="ICONS.delete"
                            class="text-negative"
                            @click="onDelete(s)"
                        >
                            <q-tooltip>Delete</q-tooltip>
                        </BaseButton>
                    </div>
                </q-item-section>
            </q-item>
        </q-list>

        <div v-else-if="!loading" class="text-center q-pa-lg dora-text-muted">
            <q-icon :name="ICONS.store" size="48px" class="q-mb-sm" />
            <div>No stores yet. Add the ones you actually shop at.</div>
        </div>
    </div>

    <!-- Create / edit dialog. The picker is reused for both modes; `editing`
         carries the row when editing, null when creating. -->
    <BaseDialog
        v-model="dialogOpen"
        :title="editing ? 'Edit store' : 'Add store'"
        closable
    >
        <!-- The body belongs in BaseDialog's DEFAULT slot. It was written as
             `#content` (a slot BaseDialog does not define), so the whole form
             — name field and logo picker — silently rendered nowhere. -->
        <q-card-section class="column q-gutter-md">
            <q-input
                v-model="draft.name"
                outlined
                dense
                label="Store name"
                autofocus
                :rules="[(v) => !!v && v.trim().length > 0 || 'Name is required']"
                @keydown.enter.prevent="onSave"
            />

            <div>
                <div class="text-caption dora-text-muted q-mb-sm">
                    Logo (optional)
                </div>
                <div class="row items-center q-gutter-md">
                    <!-- Same click-the-picture affordance as the profile
                         picture on Account (ImageEditTile), sized to the
                         logo's rectangle rather than an avatar circle. -->
                    <ImageEditTile
                        :label="pickerVerb"
                        shape="rounded"
                        :width="80"
                        :height="48"
                        accept="image/png,image/jpeg,image/webp"
                        @pick="onPickImage"
                        @error="onPickError"
                    >
                        <StoreLogo
                            :name="draft.name || '?'"
                            :store-id="editing?.store_id ?? null"
                            :has-image="!!editing?.has_image && !clearImage"
                            :preview-src="draft.image"
                            :height="48"
                            :width="80"
                        />
                    </ImageEditTile>
                    <BaseButton
                        v-if="(editing?.has_image && !clearImage) || draft.image"
                        variant="danger-ghost"
                        dense
                        :icon="ICONS.delete_outline"
                        label="Remove logo"
                        @click="onRemoveImage"
                    />
                </div>
                <div v-if="pickError" class="text-caption text-negative q-mt-xs">
                    {{ pickError }}
                </div>
            </div>
        </q-card-section>

        <template #actions="{ cancel }">
            <BaseButton variant="ghost" label="Cancel" @click="cancel" />
            <BaseButton
                :label="editing ? 'Save' : 'Add'"
                :loading="saving"
                :disable="!draft.name || draft.name.trim().length === 0"
                @click="onSave"
            />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import ImageEditTile from 'src/components/ImageEditTile.vue';
    import StoreLogo from 'src/components/StoreLogo.vue';
    import { useQuasar } from 'quasar';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useStoresStore } from 'src/stores/storesStore';
    import { ICONS } from 'src/style/icons';
    import type { ProcessedImage } from 'src/services/files/imageService';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, reactive, ref } from 'vue';
    import type { Store } from 'src/models/store';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const storesStore = useStoresStore();
    const { stores } = storeToRefs(storesStore);

    const loading = ref(false);
    const loadError = ref<string | null>(null);

    const dialogOpen = ref(false);
    const editing = ref<Store | null>(null);
    const saving = ref(false);
    const draft = reactive<{ name: string; image: string | null }>({
        name: '',
        image: null,
    });
    const clearImage = ref(false);
    const pickError = ref<string | null>(null);

    // the picker verb tracks the current state so screen-reader
    // users hear "Add" for a new store and "Change" for one that already
    // has a logo. Matches the language ImageUploadField uses on the other
    // upload surfaces.
    const pickerVerb = computed(() => {
        const hasExisting = !!editing.value?.has_image && !clearImage.value;
        return hasExisting || draft.image ? 'Change logo' : 'Add logo';
    });

    onMounted(() => {
        // R-016 ensureLoaded. There is no manual refresh control — every
        // mutation on this page already refreshes the store, so a refresh
        // button was a no-op affordance.
        loading.value = true;
        storesStore
            .ensureLoadedAsync()
            .catch((e) => {
                loadError.value = toastCaption(e);
            })
            .finally(() => {
                loading.value = false;
            });
    });

    function resetDraft(): void {
        draft.name = '';
        draft.image = null;
        clearImage.value = false;
        pickError.value = null;
        editing.value = null;
    }

    function openCreate(): void {
        resetDraft();
        dialogOpen.value = true;
    }

    function openEdit(store: Store): void {
        resetDraft();
        editing.value = store;
        draft.name = store.name;
        dialogOpen.value = true;
    }

    function onPickImage(image: ProcessedImage): void {
        // ImageSourcePicker → processImageFile() already resized + re-encoded
        // to JPEG using the install-wide image policy (R-003). We just hold
        // the data URL for the save round-trip; the backend accepts it as-is
        // (`POST /stores` / `PUT /stores/<id>` store the bytes verbatim and
        // serve them via `GET /stores/<id>/image`).
        clearImage.value = false;
        pickError.value = null;
        draft.image = image.dataUrl;
    }

    function onPickError(message: string): void {
        pickError.value = message;
    }

    // Clears both a just-picked logo and (when editing) the saved one — the
    // save below sends `clear_image` only when there is something on the
    // server left to clear.
    function onRemoveImage(): void {
        draft.image = null;
        pickError.value = null;
        if (editing.value?.has_image) clearImage.value = true;
    }

    async function onSave(): Promise<void> {
        const name = draft.name.trim();
        if (!name) return;
        saving.value = true;
        try {
            if (editing.value) {
                await storesStore.updateAsync({
                    store_id: editing.value.store_id,
                    name,
                    ...(clearImage.value
                        ? { clear_image: true }
                        : draft.image
                            ? { image: draft.image }
                            : {}),
                });
                $q.notify({ type: 'positive', message: `Updated ${name}.` });
            } else {
                await storesStore.createAsync({
                    name,
                    ...(draft.image ? { image: draft.image } : {}),
                });
                $q.notify({ type: 'positive', message: `Added ${name}.` });
            }
            dialogOpen.value = false;
            resetDraft();
        } catch (e) {
            $q.notify({
                type: 'negative',
                message: editing.value ? "Couldn't update the store." : "Couldn't add the store.",
                caption: toastCaption(e),
            });
        } finally {
            saving.value = false;
        }
    }

    function onDelete(store: Store): void {
        $q.dialog({
            title: `Delete ${store.name}?`,
            message:
                "Stock items and shopping-list lines that referenced this store will keep working — their reference is just cleared. Products linked to this store would be orphaned and the delete will be rejected.",
            cancel: { noCaps: true },
            ok: { label: 'Delete', color: 'negative', noCaps: true, flat: true },
        }).onOk(() => {
            storesStore
                .deleteAsync(store.store_id)
                .then((result) => {
                    const tail =
                        result.items_affected || result.lines_affected
                            ? ` (${result.items_affected} stock item(s) and ${result.lines_affected} shopping line(s) had their store reference cleared.)`
                            : '';
                    $q.notify({
                        type: 'positive',
                        message: `Deleted ${store.name}.${tail}`,
                    });
                })
                .catch((e) => {
                    $q.notify({
                        type: 'negative',
                        message: `Couldn't delete ${store.name}.`,
                        caption: toastCaption(e),
                    });
                });
        });
    }
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
</style>
