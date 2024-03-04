<template>
    <q-btn-dropdown
        :auto-close="true"
        class="bg-white q-ma-sm"
        dropdown-icon="expand_more"
        no-caps
        :no-route-dismiss="false"
        no-wrap
        :persistent="false"
        size="md"
        :dense="true"
        :split="false"
        :stack="false"
        :stretch="false"
        type="button"
        transition-duration ="300"
        transition-hide="fade"
        transition-show="fade"
    >
        <template v-slot:label>
            <span class="block q-pl-sm">{{label}}</span>
        </template>
        <q-list>
            <q-item v-for="(item, index) in listItems" :key="index" clickable v-close-popup>
                <q-item-section>
                    <q-item-label>{{item}}</q-item-label>
                </q-item-section>
            </q-item>
        </q-list>
    </q-btn-dropdown>
</template>
    <!-- :update:model-value="onDropdownOneUpdate('dropdownOne')" -->
    <!-- :v-model="dropdownOneModel" -->

<script setup lang="ts">
    defineProps<{
        label: string
        listItems: Array<string>
    }>()
</script>
