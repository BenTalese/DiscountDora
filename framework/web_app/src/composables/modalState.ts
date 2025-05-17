import { ref, watch } from "vue";

export function useModalState(props: { modelValue: boolean }, emit: (name: 'update:modelValue', value: boolean) => void) {
    const isModalVisible = ref(props.modelValue);

    watch(() => props.modelValue, (val) => {
        isModalVisible.value = val;
    });

    watch(isModalVisible, (val) => {
      emit('update:modelValue', val);
    });

    return {
        isModalVisible
    };
  }
