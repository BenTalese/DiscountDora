<template>
    <div class="column q-gutter-md">
        <VocabListEditor
            title="Cuisines"
            description="The cuisine options shown on recipes (single-select)."
            noun="cuisine"
            noun-plural="cuisines"
            :items="cuisineItems"
            :loading="loading"
            :busy="busy"
            @create="onCreateCuisine"
            @rename="onRenameCuisine"
            @delete="onDeleteCuisine"
        />

        <VocabListEditor
            title="Categories"
            description="The category options shown on recipes (single-select)."
            noun="category"
            noun-plural="categories"
            :items="categoryItems"
            :loading="loading"
            :busy="busy"
            @create="onCreateCategory"
            @rename="onRenameCategory"
            @delete="onDeleteCategory"
        />

        <VocabListEditor
            title="Tools"
            description="Kitchen tools recipes can require (multi-select + filterable)."
            noun="tool"
            noun-plural="tools"
            :items="toolItems"
            :loading="loading"
            :busy="busy"
            @create="onCreateTool"
            @rename="onRenameTool"
            @delete="onDeleteTool"
        />

        <!-- Dietary tags carry a grouping label, so they get a bespoke editor. -->
        <q-card flat bordered>
            <q-card-section class="row items-center">
                <div>
                    <div class="text-h6">Dietary tags</div>
                    <div class="text-caption dora-text-muted">
                        Dietary / allergen / nutritional tags recipes can be tagged with.
                        {{ dietaryTags.length }} tag{{ dietaryTags.length === 1 ? '' : 's' }}.
                    </div>
                </div>
                <q-space />
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.add"
                    label="New tag"
                    :loading="busy"
                    @click="onCreateDietaryTag"
                />
            </q-card-section>
            <q-separator />
            <q-list separator>
                <q-item v-for="tag in dietaryTags" :key="tag.dietary_tag_id" class="q-py-sm">
                    <q-item-section avatar><q-icon :name="ICONS.label" /></q-item-section>
                    <q-item-section>
                        <q-item-label>{{ tag.name }}</q-item-label>
                        <q-item-label caption>
                            {{ tag.category }} ·
                            {{ tag.recipe_count ?? 0 }} recipe{{ (tag.recipe_count ?? 0) === 1 ? '' : 's' }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs">
                            <q-btn flat dense round :icon="ICONS.edit" @click="onRenameDietaryTag(tag)">
                                <q-tooltip>Rename</q-tooltip>
                            </q-btn>
                            <q-btn flat dense round :icon="ICONS.delete_outline" @click="onDeleteDietaryTag(tag)">
                                <q-tooltip>Delete</q-tooltip>
                            </q-btn>
                        </div>
                    </q-item-section>
                </q-item>
                <q-item v-if="!loading && dietaryTags.length === 0">
                    <q-item-section class="dora-text-muted text-center">
                        No dietary tags yet.
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import VocabListEditor from 'src/components/settings/VocabListEditor.vue';
    import type { DietaryTag } from 'src/models/recipeVocab';
    import CuisineApiService from 'src/services/api/cuisineApiService';
    import CategoryApiService from 'src/services/api/categoryApiService';
    import DietaryTagApiService from 'src/services/api/dietaryTagApiService';
    import ToolApiService from 'src/services/api/toolApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { computed, onMounted, ref } from 'vue';

    const $q = useQuasar();
    const cuisineApi = new CuisineApiService();
    const categoryApi = new CategoryApiService();
    const dietaryTagApi = new DietaryTagApiService();
    const toolApi = new ToolApiService();

    const cuisines = ref<Awaited<ReturnType<CuisineApiService['getAllAsync']>>>([]);
    const categories = ref<Awaited<ReturnType<CategoryApiService['getAllAsync']>>>([]);
    const dietaryTags = ref<DietaryTag[]>([]);
    const tools = ref<Awaited<ReturnType<ToolApiService['getAllAsync']>>>([]);
    const loading = ref(false);
    const busy = ref(false);

    const cuisineItems = computed(() =>
        cuisines.value.map((c) => ({ id: c.cuisine_id, name: c.name, recipe_count: c.recipe_count ?? 0 })),
    );
    const categoryItems = computed(() =>
        categories.value.map((c) => ({ id: c.category_id, name: c.name, recipe_count: c.recipe_count ?? 0 })),
    );
    const toolItems = computed(() =>
        tools.value.map((t) => ({ id: t.tool_id, name: t.name, recipe_count: t.recipe_count ?? 0 })),
    );

    async function load() {
        loading.value = true;
        try {
            [cuisines.value, categories.value, dietaryTags.value, tools.value] = await Promise.all([
                cuisineApi.getAllAsync(),
                categoryApi.getAllAsync(),
                dietaryTagApi.getAllAsync(),
                toolApi.getAllAsync(),
            ]);
        } catch (err) {
            notifyError('Could not load recipe vocabularies.', err);
        } finally {
            loading.value = false;
        }
    }

    function notifyError(message: string, err: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: describeApiError(err) || '',
        });
    }

    async function run(action: () => Promise<unknown>) {
        busy.value = true;
        try {
            await action();
            await load();
        } catch (err) {
            notifyError('Could not save the change.', err);
        } finally {
            busy.value = false;
        }
    }

    // ── Cuisines ──────────────────────────────────────────────────────
    const onCreateCuisine = (name: string) => run(() => cuisineApi.createAsync({ name }));
    const onRenameCuisine = (id: string, name: string) => run(() => cuisineApi.updateAsync(id, { name }));
    const onDeleteCuisine = (id: string) => run(() => cuisineApi.deleteAsync(id).then(() => undefined));

    // ── Categories ────────────────────────────────────────────────────
    const onCreateCategory = (name: string) => run(() => categoryApi.createAsync({ name }));
    const onRenameCategory = (id: string, name: string) => run(() => categoryApi.updateAsync(id, { name }));
    const onDeleteCategory = (id: string) => run(() => categoryApi.deleteAsync(id).then(() => undefined));

    // ── Tools ─────────────────────────────────────────────────────────
    const onCreateTool = (name: string) => run(() => toolApi.createAsync({ name }));
    const onRenameTool = (id: string, name: string) => run(() => toolApi.updateAsync(id, { name }));
    const onDeleteTool = (id: string) => run(() => toolApi.deleteAsync(id).then(() => undefined));

    // ── Dietary tags (name + grouping category) ───────────────────────
    async function promptText(title: string, message: string, initial = ''): Promise<string | null> {
        return new Promise((resolve) => {
            $q.dialog({
                title,
                message,
                prompt: { model: initial, type: 'text' },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
    }

    async function onCreateDietaryTag() {
        const name = await promptText('New dietary tag', 'Tag name (e.g. "Vegan", "Gluten-free")');
        if (!name) return;
        const category = await promptText(
            'Tag group',
            'Which group does it belong to? (e.g. "Allergen-free", "Dietary pattern")',
            'Custom',
        );
        if (!category) return;
        await run(() => dietaryTagApi.createAsync({ name, category }));
    }

    async function onRenameDietaryTag(tag: DietaryTag) {
        const name = await promptText('Rename dietary tag', 'Tag name', tag.name);
        if (name === null) return;
        const category = await promptText('Tag group', 'Group', tag.category);
        if (category === null) return;
        await run(() => dietaryTagApi.updateAsync(tag.dietary_tag_id, { name, category }));
    }

    async function onDeleteDietaryTag(tag: DietaryTag) {
        const count = tag.recipe_count ?? 0;
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${tag.name}"?`,
                message:
                    count > 0
                        ? `${count} recipe${count === 1 ? '' : 's'} tagged with this will lose the tag.`
                        : 'Nothing currently uses this tag.',
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (ok) await run(() => dietaryTagApi.deleteAsync(tag.dietary_tag_id).then(() => undefined));
    }

    onMounted(load);
</script>
