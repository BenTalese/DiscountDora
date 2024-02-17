<script setup lang="ts">
const props = defineProps({
    msg: String
})
</script>

<template>
    <div v-if="props.msg" class="error-popup">
        <p>{{ props.msg }}</p>
    </div>
</template>

<style scoped>
.error-popup {
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #ff3333;
    color: #ffffff;
    padding: 10px;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
}
</style>
