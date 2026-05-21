import { acceptHMRUpdate, defineStore } from 'pinia';
import type { Merchant } from 'src/models/merchant';
import MerchantApiService from 'src/services/api/merchantApiService';
import MerchantManagementApiService, {
    type DataProviderHealth
} from 'src/services/api/merchantManagementApiService';
import { computed, readonly, ref } from 'vue';
import { useProductStore } from './productStore';

const merchantApiService = new MerchantApiService();
const merchantManagementApiService = new MerchantManagementApiService();

export const useMerchantStore = defineStore('merchant', () => {
    const productStore = useProductStore();

    const merchants = ref<Merchant[]>([]);
    const providerHealth = ref<DataProviderHealth[]>([]);

    const collator = new Intl.Collator('en', { sensitivity: 'base' });

    const getMerchantsAsync = () =>
        merchantApiService.getAllAsync().then((data) => {
            merchants.value = [...data].sort((a, b) => collator.compare(a.name, b.name));
            productStore.addStoresToProductSearchFilter(getEnabledMerchants.value);
        });

    /** Provider health isn't critical for the search to function, so we
     *  swallow errors and just leave the array empty. The product search
     *  page treats unknown health as "available" rather than blocking. */
    const getProviderHealthAsync = async () => {
        try {
            providerHealth.value = await merchantManagementApiService.getDataProvidersHealthAsync();
        } catch {
            providerHealth.value = [];
        }
    };

    const getEnabledMerchants = computed(() => merchants.value.filter((m) => m.is_enabled));

    /** Best-guess health entry for a merchant name. The merchant_api doesn't
     *  return a strict link between providers and merchants, so we
     *  substring-match on the provider base URL. */
    const healthForMerchant = (merchantName: string): DataProviderHealth | undefined => {
        const needle = merchantName.toLowerCase();
        return providerHealth.value.find((h) => h.base_url.toLowerCase().includes(needle));
    };

    /** True when we either have no health data (assume healthy until told
     *  otherwise) or the matched provider isn't explicitly unhealthy. */
    const isMerchantHealthy = (merchantName: string): boolean => {
        const h = healthForMerchant(merchantName);
        if (!h) return true;
        if (h.skipped) return true;
        return h.is_healthy;
    };

    return {
        merchants: readonly(merchants),
        providerHealth: readonly(providerHealth),
        getMerchantsAsync,
        getProviderHealthAsync,
        getEnabledMerchants,
        healthForMerchant,
        isMerchantHealthy
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useMerchantStore, import.meta.hot));
}
