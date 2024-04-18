import { defineStore } from 'pinia';
import { Merchant } from 'src/models/Merchant';
import MerchantApiService from 'src/services/api/MerchantApiService';
import { ref } from 'vue';

const merchantApiService = new MerchantApiService();

export const useMerchantStore = defineStore('merchant', () => {

//#region Merchants

const merchants = ref<Merchant[]>([]);

async function getMerchantsAsync(){
    merchantApiService
        .getAllAsync()
        .then((merchantsData) => {
            const collator = new Intl.Collator('en', {'sensitivity': 'base'});

            merchants.value = merchantsData.sort((merchant1, merchant2) =>
                collator.compare(merchant1.name, merchant2.name));
        });
};

//#endregion Merchants

return {
    merchants,
    getMerchantsAsync
};

});
