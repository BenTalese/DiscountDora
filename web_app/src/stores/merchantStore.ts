import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Merchant } from 'src/models/merchant';
import MerchantApiService from 'src/services/api/merchantApiService';
import { computed, readonly, ref } from 'vue';
import { useProductStore } from './productStore';

const merchantApiService = new MerchantApiService();

export const useMerchantStore = defineStore('merchant', () => {
    const productStore = useProductStore();

    //#region Merchants

    const merchants = ref<Merchant[]>([]);

    const getMerchantsAsync = () =>
        merchantApiService.getAllAsync().then((merchantsData) => {
            const collator = new Intl.Collator('en', { sensitivity: 'base' });

            merchants.value = merchantsData.sort((merchant1, merchant2) =>
                collator.compare(merchant1.name, merchant2.name)
            );

            productStore.addStoresToProductSearchFilter(getEnabledMerchants.value);
        });

    const getEnabledMerchants = computed(() => merchants.value.filter((m) => m.is_enabled));

    //#endregion Merchants

    return {
        merchants: readonly(merchants),
        getMerchantsAsync,
        getEnabledMerchants
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMerchantStore, import.meta.hot));
}
