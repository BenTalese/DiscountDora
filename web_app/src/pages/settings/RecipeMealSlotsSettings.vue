<template>
    <TaxonomyManagerPage
        title="Meal slots"
        description="The meal slot options shown in meal plans and on recipes."
        noun="meal slot"
        noun-plural="meal slots"
        usage-label="entry"
        empty-action="Create one to schedule meals against."
        :preserves-label="true"
        :reorderable="true"
        :load="load"
        :create="create"
        :rename="rename"
        :remove="remove"
        :reorder="reorder"
    />
</template>

<script lang="ts" setup>
    import TaxonomyManagerPage, { type VocabItem } from 'src/components/settings/TaxonomyManagerPage.vue';
    import MealSlotApiService from 'src/services/api/mealSlotApiService';

    const api = new MealSlotApiService();

    // Slots come back sorted (sequence, then name) from the list endpoint; the
    // up/down controls rely on that order. `usage_count` carries the tally the
    // generic editor renders.
    const load = async (): Promise<VocabItem[]> =>
        (await api.getAllAsync()).map((s) => ({ id: s.meal_slot_id, name: s.name, recipe_count: s.usage_count }));
    const create = (name: string) => api.createAsync({ name });
    const rename = (id: string, name: string) => api.updateAsync(id, { name });
    const remove = (id: string) => api.deleteAsync(id).then(() => undefined);

    // Swap the moved slot's position with its up/down neighbour, then persist
    // the new ordering in one reorder call. `items` is already in display
    // order from the wrapper.
    const reorder = (id: string, direction: 'up' | 'down', items: VocabItem[]) => {
        const ordered = [...items];
        const index = ordered.findIndex((s) => s.id === id);
        const target = direction === 'up' ? index - 1 : index + 1;
        if (index < 0 || target < 0 || target >= ordered.length) return Promise.resolve();
        [ordered[index], ordered[target]] = [ordered[target]!, ordered[index]!];
        const slots = ordered.map((s, i) => ({ meal_slot_id: s.id, sequence: i }));
        return api.reorderAsync({ slots });
    };
</script>
