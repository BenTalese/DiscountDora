<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <div>
                <div class="text-h5">Shopping lists</div>
                <div class="text-caption text-grey">
                    {{ activeCount }} active, {{ archivedCount }} archived.
                    <span v-if="!primarySummary && activeCount > 0">
                        · No primary list set — pick one for quick-add.
                    </span>
                </div>
            </div>
            <q-space />
            <q-btn-dropdown
                color="primary"
                no-caps
                icon="add"
                label="New list"
                :loading="creating || autogenerating"
                split
                @click="onCreate"
            >
                <q-list>
                    <q-item clickable v-close-popup @click="onAutogenerateNew">
                        <q-item-section avatar>
                            <q-icon name="auto_awesome" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>Auto-generate from flagged items</q-item-label>
                            <q-item-label caption>
                                Builds a list from every essential item that's low or out of stock.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item
                        v-if="primarySummary"
                        clickable
                        v-close-popup
                        @click="onAutogenerateOntoPrimary"
                    >
                        <q-item-section avatar>
                            <q-icon name="playlist_add" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>Top up the primary list</q-item-label>
                            <q-item-label caption>
                                Adds any flagged-and-low items missing from
                                "{{ primarySummary.name }}".
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item clickable v-close-popup @click="onPickTemplate">
                        <q-item-section avatar>
                            <q-icon name="bookmarks" color="primary" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>From a template…</q-item-label>
                            <q-item-label caption>
                                Pick a saved template to spin up a new list.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                    <q-item clickable v-close-popup to="/shopping-lists/templates">
                        <q-item-section avatar>
                            <q-icon name="settings" />
                        </q-item-section>
                        <q-item-section>Manage templates…</q-item-section>
                    </q-item>
                </q-list>
            </q-btn-dropdown>
        </div>

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-tabs
            v-model="tab"
            dense
            class="text-primary q-mb-sm"
            active-color="primary"
            indicator-color="primary"
            align="left"
        >
            <q-tab name="active" no-caps>
                Active
                <q-badge v-if="activeCount > 0" floating color="primary">{{ activeCount }}</q-badge>
            </q-tab>
            <q-tab name="archived" no-caps>
                Archived
                <q-badge v-if="archivedCount > 0" floating color="grey-5">{{ archivedCount }}</q-badge>
            </q-tab>
        </q-tabs>
        <q-separator />

        <div v-if="loading && summaries.length === 0" class="text-center q-py-xl">
            <q-spinner color="primary" size="48px" />
        </div>

        <div v-else-if="visibleLists.length === 0" class="text-center text-grey q-py-xl">
            <q-icon name="shopping_cart" size="60px" class="q-mb-sm" />
            <div v-if="tab === 'active'">No active shopping lists. Create one to start.</div>
            <div v-else>No archived lists yet — finished lists show up here.</div>
        </div>

        <div v-else class="row q-col-gutter-md q-mt-sm">
            <div
                v-for="list in visibleLists"
                :key="list.shopping_list_id"
                class="col-12 col-sm-6 col-md-4"
            >
                <q-card
                    flat
                    bordered
                    class="cursor-pointer shopping-list-card"
                    :class="{
                        'shopping-list-primary': list.is_primary,
                        'shopping-list-archived': list.is_archived,
                    }"
                    @click="openList(list.shopping_list_id)"
                >
                    <q-card-section class="row items-start">
                        <div class="col">
                            <div class="text-h6">
                                {{ list.name }}
                                <q-badge
                                    v-if="list.is_primary"
                                    color="primary"
                                    text-color="white"
                                    class="q-ml-sm"
                                >
                                    Primary
                                </q-badge>
                            </div>
                            <div class="text-caption text-grey">
                                Created {{ formatDate(list.created_at) }}
                                <span v-if="list.completed_at">
                                    · Finished {{ formatDate(list.completed_at) }}
                                </span>
                            </div>
                        </div>

                        <q-btn flat round dense icon="more_vert" @click.stop>
                            <q-menu>
                                <q-list dense style="min-width: 180px">
                                    <q-item
                                        v-if="!list.is_archived && !list.is_primary"
                                        clickable
                                        v-close-popup
                                        @click.stop="setPrimary(list.shopping_list_id)"
                                    >
                                        <q-item-section avatar><q-icon name="star" /></q-item-section>
                                        <q-item-section>Set as primary</q-item-section>
                                    </q-item>
                                    <q-item
                                        v-if="list.is_archived"
                                        clickable
                                        v-close-popup
                                        @click.stop="copyList(list.shopping_list_id, 'all')"
                                    >
                                        <q-item-section avatar><q-icon name="content_copy" /></q-item-section>
                                        <q-item-section>Copy to new list</q-item-section>
                                    </q-item>
                                    <q-item
                                        clickable
                                        v-close-popup
                                        @click.stop="onDelete(list)"
                                    >
                                        <q-item-section avatar>
                                            <q-icon name="delete" color="negative" />
                                        </q-item-section>
                                        <q-item-section class="text-negative">
                                            Delete list
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </q-menu>
                        </q-btn>
                    </q-card-section>

                    <q-separator />

                    <q-card-section class="row items-center">
                        <q-circular-progress
                            :value="progressValue(list)"
                            size="40px"
                            :thickness="0.2"
                            color="primary"
                            track-color="grey-3"
                        >
                            {{ list.ticked_count }}/{{ list.line_count }}
                        </q-circular-progress>
                        <div class="q-ml-md col">
                            <div class="text-body2">
                                {{ list.line_count }} item{{ list.line_count === 1 ? '' : 's' }}
                            </div>
                            <div class="text-caption text-grey">
                                {{ list.ticked_count }} ticked off
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
        </div>
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import type { ShoppingListSummary } from 'src/models/shoppingList';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ShoppingListTemplateApiService from 'src/services/api/shoppingListTemplateApiService';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const api = new ShoppingListApiService();
    const templateApi = new ShoppingListTemplateApiService();
    const store = useShoppingListStore();

    const tab = ref<'active' | 'archived'>('active');
    const creating = ref(false);
    const autogenerating = ref(false);

    const summaries = computed(() => store.summaries);
    const loading = computed(() => store.loading);
    const loadError = computed(() => store.loadError);
    const primarySummary = computed(() => store.primarySummary);

    const activeCount = computed(() => summaries.value.filter((s) => !s.is_archived).length);
    const archivedCount = computed(() => summaries.value.filter((s) => s.is_archived).length);

    const visibleLists = computed(() =>
        tab.value === 'active'
            ? summaries.value.filter((s) => !s.is_archived)
            : summaries.value.filter((s) => s.is_archived)
    );

    function progressValue(list: ShoppingListSummary): number {
        if (list.line_count === 0) return 0;
        return Math.round((list.ticked_count / list.line_count) * 100);
    }

    function formatDate(iso: string): string {
        try {
            return new Date(iso).toLocaleDateString();
        } catch {
            return iso;
        }
    }

    function openList(id: string) {
        void router.push(`/shopping-lists/${id}`);
    }

    async function onCreate() {
        // First list is auto-primary so the cart button starts working
        // immediately without a "pick a primary" hand-hold.
        const makePrimary = activeCount.value === 0;
        creating.value = true;
        try {
            const { shopping_list_id } = await api.createAsync({
                make_primary: makePrimary,
            });
            await store.refreshAsync();
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create list.',
                caption: String(err),
            });
        } finally {
            creating.value = false;
        }
    }

    async function runAutogen(targetListId: string | null) {
        autogenerating.value = true;
        try {
            const result = await api.autogenerateAsync({
                target_shopping_list_id: targetListId,
            });
            await store.refreshAsync();
            if (result.nothing_flagged) {
                // Nothing essential is low/out — surface this clearly so the
                // user knows it ran rather than silently doing nothing.
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message:
                        'Nothing to auto-add. Flag essentials on items that are low or out of stock first.',
                    timeout: 5000,
                });
                return;
            }
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Auto-generated: ${result.added_count} added` +
                    (result.skipped_already_on_list > 0
                        ? `, ${result.skipped_already_on_list} already on list`
                        : ''),
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not auto-generate.',
                caption: String(err),
            });
        } finally {
            autogenerating.value = false;
        }
    }

    function onAutogenerateNew() {
        void runAutogen(null);
    }
    function onAutogenerateOntoPrimary() {
        if (!primarySummary.value) return;
        void runAutogen(primarySummary.value.shopping_list_id);
    }

    async function onPickTemplate() {
        // Load templates lazily on click so the overview page doesn't pay
        // the fetch cost when the user never opens this menu.
        let templates;
        try {
            templates = await templateApi.getAllAsync();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load templates.',
                caption: String(err),
            });
            return;
        }
        if (templates.length === 0) {
            $q.dialog({
                title: 'No templates yet',
                message: 'Save a list as a template first (from any list\'s menu), or use the Manage templates page.',
                ok: { label: 'Open templates', noCaps: true, color: 'primary' },
                cancel: { noCaps: true },
            }).onOk(() => router.push('/shopping-lists/templates'));
            return;
        }
        const templateId = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Use which template?',
                message: 'A new shopping list will be created from the template\'s items.',
                options: {
                    type: 'radio',
                    model: templates[0]!.template_id,
                    items: templates.map((t) => ({
                        label: `${t.name} (${t.line_count} item${
                            t.line_count === 1 ? '' : 's'
                        })`,
                        value: t.template_id,
                    })),
                },
                ok: { label: 'Create list', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk((value: string) => resolve(value))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!templateId) return;
        try {
            // If there's no current primary, the freshly instantiated list
            // becomes primary — matches the auto-generate convention.
            const result = await templateApi.instantiateAsync(templateId, {
                make_primary: !primarySummary.value,
            });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Created list with ${result.line_count} item${
                    result.line_count === 1 ? '' : 's'
                }.`,
            });
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create from template.',
                caption: String(err),
            });
        }
    }

    async function setPrimary(id: string) {
        try {
            await api.updateAsync(id, { is_primary: true });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Primary list updated.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update primary.',
                caption: String(err),
            });
        }
    }

    async function copyList(id: string, include: 'all' | 'unticked') {
        try {
            const { shopping_list_id } = await api.copyAsync(id, { include });
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List copied.',
            });
            void router.push(`/shopping-lists/${shopping_list_id}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not copy list.',
                caption: String(err),
            });
        }
    }

    async function onDelete(list: ShoppingListSummary) {
        // Active lists require confirmation (per spec); archived ones don't.
        if (!list.is_archived) {
            const ok = await new Promise<boolean>((resolve) => {
                $q.dialog({
                    title: `Delete "${list.name}"?`,
                    message:
                        list.ticked_count < list.line_count
                            ? `${list.line_count - list.ticked_count} item${
                                  list.line_count - list.ticked_count === 1 ? '' : 's'
                              } not yet ticked off. Delete anyway?`
                            : 'This will remove the list and all its lines.',
                    cancel: true,
                    persistent: true,
                })
                    .onOk(() => resolve(true))
                    .onCancel(() => resolve(false))
                    .onDismiss(() => resolve(false));
            });
            if (!ok) return;
        }
        try {
            await api.deleteAsync(list.shopping_list_id);
            await store.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'List deleted.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: String(err),
            });
        }
    }

    onMounted(store.refreshAsync);
</script>

<style scoped>
    .shopping-list-card {
        transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .shopping-list-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .shopping-list-primary {
        border-left: 4px solid var(--q-primary);
    }
    .shopping-list-archived {
        opacity: 0.65;
    }
</style>
