<template>
    <q-card flat bordered>
        <q-card-section class="row items-center">
            <div>
                <div class="text-h6">
                    <q-icon :name="ICONS.store" size="20px" class="q-mr-xs" />
                    Stores
                </div>
                <div class="text-caption dora-text-muted">
                    The retail stores you actually shop at. Curate this list
                    yourself — Dora ships zero pre-seeded stores. Upload a
                    logo so each store is recognisable on cards and lines.
                </div>
            </div>
            <q-space />
            <q-btn
                flat
                round
                dense
                :icon="ICONS.refresh"
                :loading="loading"
                @click="reload"
            >
                <q-tooltip>Refresh</q-tooltip>
            </q-btn>
            <q-btn
                color="primary"
                no-caps
                :icon="ICONS.add"
                label="Add store"
                class="q-ml-sm"
                @click="openCreate"
            />
        </q-card-section>

        <q-banner
            v-if="loadError"
            class="dora-bg-negative-soft text-negative q-mx-md q-mb-md"
            dense
            rounded
        >
            {{ loadError }}
        </q-banner>

        <q-list v-if="stores.length > 0" separator>
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
    </q-card>

    <!-- Create / edit dialog. The picker is reused for both modes; `editing`
         carries the row when editing, null when creating. -->
    <BaseDialog v-model="dialogOpen" :title="editing ? 'Edit store' : 'Add store'">
        <template #content>
            <q-input
                v-model="draft.name"
                outlined
                dense
                label="Store name"
                autofocus
                class="q-mb-md"
                :rules="[(v) => !!v && v.trim().length > 0 || 'Name is required']"
            />

            <div class="row items-center q-gutter-md q-mb-sm">
                <StoreLogo
                    :name="draft.name || '?'"
                    :store-id="editing?.store_id ?? null"
                    :has-image="!!draft.image || (!!editing?.has_image && !clearImage)"
                    :height="48"
                    :width="80"
                />
                <div class="col">
                    <div class="text-caption dora-text-muted q-mb-xs">
                        Optional logo (PNG/JPG/WebP, up to ~6 MB).
                    </div>
                    <q-file
                        v-model="imageFile"
                        outlined
                        dense
                        :accept="ACCEPT"
                        :max-file-size="MAX_BYTES"
                        @rejected="onImageRejected"
                        @update:model-value="onPickImage"
                        clearable
                    >
                        <template #prepend>
                            <q-icon :name="ICONS.upload" />
                        </template>
                    </q-file>
                    <q-btn
                        v-if="editing?.has_image && !clearImage && !draft.image"
                        flat
                        dense
                        no-caps
                        color="negative"
                        label="Remove existing logo"
                        @click="clearImage = true"
                    />
                </div>
            </div>
        </template>
        <template #actions>
            <q-btn flat no-caps label="Cancel" @click="dialogOpen = false" />
            <q-btn
                unelevated
                color="primary"
                no-caps
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
    import StoreLogo from 'src/components/StoreLogo.vue';
    import { useQuasar } from 'quasar';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useStoresStore } from 'src/stores/storesStore';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { onMounted, reactive, ref } from 'vue';
    import type { Store } from 'src/models/store';

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
    const imageFile = ref<File | null>(null);
    const clearImage = ref(false);

    const ACCEPT = 'image/png, image/jpeg, image/webp';
    const MAX_BYTES = 6_000_000;

    function reload(): void {
        loading.value = true;
        loadError.value = null;
        storesStore
            .listAsync()
            .catch((e) => {
                loadError.value = describeApiError(e);
            })
            .finally(() => {
                loading.value = false;
            });
    }

    onMounted(() => {
        // Use R-016 ensureLoaded on first open; the explicit refresh
        // button calls listAsync directly for a forced refetch.
        loading.value = true;
        storesStore
            .ensureLoadedAsync()
            .catch((e) => {
                loadError.value = describeApiError(e);
            })
            .finally(() => {
                loading.value = false;
            });
    });

    function resetDraft(): void {
        draft.name = '';
        draft.image = null;
        imageFile.value = null;
        clearImage.value = false;
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

    function onImageRejected(): void {
        $q.notify({
            type: 'warning',
            message: `Image must be PNG/JPG/WebP, under ${(MAX_BYTES / 1_000_000).toFixed(0)} MB.`,
        });
    }

    async function onPickImage(file: File | null): Promise<void> {
        if (!file) {
            draft.image = null;
            return;
        }
        clearImage.value = false;
        // Read as data URL (same convention as stock-item / product / recipe
        // image upload). The backend stores the UTF-8 bytes verbatim and
        // serves them back via `GET /stores/<id>/image`.
        draft.image = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const result = reader.result;
                resolve(typeof result === 'string' ? result : '');
            };
            reader.onerror = () =>
                reject(reader.error ?? new Error('Failed to read image.'));
            reader.readAsDataURL(file);
        });
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
            $q.notify({ type: 'negative', message: describeApiError(e) });
        } finally {
            saving.value = false;
        }
    }

    function onDelete(store: Store): void {
        $q.dialog({
            title: `Delete ${store.name}?`,
            message:
                "Stock items and shopping-list lines that referenced this store will keep working — their reference is just cleared. Products linked to this store would be orphaned and the delete will be rejected.",
            cancel: true,
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
                    $q.notify({ type: 'negative', message: describeApiError(e) });
                });
        });
    }
</script>
