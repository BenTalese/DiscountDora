import { defineStore } from 'pinia';
import { Merchant } from 'src/models/Merchant';
import MerchantApiService from 'src/services/api/MerchantApiService';
import { readonly, ref } from 'vue';
import { useProductStore } from './ProductStore';

const merchantApiService = new MerchantApiService();

export const useMerchantStore = defineStore('merchant', () => {

    const productStore = useProductStore();

    //#region Merchants

    const merchants = ref<Merchant[]>([]);

    async function getMerchantsAsync() {
        merchantApiService
            .getAllAsync()
            .then((merchantsData) => {
                const collator = new Intl.Collator('en', { 'sensitivity': 'base' });

                merchants.value = merchantsData.sort((merchant1, merchant2) =>
                    collator.compare(merchant1.name, merchant2.name));

                productStore.addStoresToProductSearchFilter(merchants.value);
            });
    };

    //#endregion Merchants

    return {
        merchants: readonly(merchants),
        getMerchantsAsync
    };

});
