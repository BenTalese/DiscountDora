import HealthApiService from 'src/services/api/healthApiService'
import { useMerchantStore } from '../stores/MerchantStore'
import { useProductStore } from '../stores/ProductStore'
import { useStockItemStore } from '../stores/stockItemStore'
import { useStockLevelStore } from '../stores/stockLevelStore'

async function waitForApiStartupAsync() {
    const healthApiService = new HealthApiService();
    while (true) {
        if (await healthApiService.healthCheckAsync()) {
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

async function initialiseStoresAsync() {
    await useMerchantStore().getMerchantsAsync()
    await useProductStore().getProductsAsync()
    await useStockItemStore().getStockItemsAsync()
    await useStockLevelStore().getStockLevelsAsync()
}

await waitForApiStartupAsync()
await initialiseStoresAsync()
