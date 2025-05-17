import { ref, watch } from 'vue';

export function useModalState<TModalProps extends { modelValue: boolean }>(
    props: TModalProps,
    emit: (name: 'update:modelValue', value: boolean) => void
) {
    const isModalVisible = ref(props.modelValue);

    watch(
        () => props.modelValue,
        (val) => {
            isModalVisible.value = val;
        }
    );

    watch(isModalVisible, (val) => {
        emit('update:modelValue', val);
    });

    return {
        isModalVisible
    };
}
