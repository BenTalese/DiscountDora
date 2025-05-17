import { ref, watch } from "vue";

export function useModalState(modelValue: boolean, emit: (name: 'update:modelValue', value: boolean) => void) {
    const isModalVisible = ref(modelValue);

    watch(() => modelValue, (val) => {
        isModalVisible.value = val;
    });

    watch(isModalVisible, (val) => {
      emit('update:modelValue', val);
    });

    return {
        isModalVisible
    };
  }
