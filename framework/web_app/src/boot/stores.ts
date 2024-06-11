import { Notify } from 'quasar'
import HealthApiService from 'src/services/api/healthApiService'
import { useMerchantStore } from '../stores/MerchantStore'
import { useProductStore } from '../stores/ProductStore'
import { useStockItemStore } from '../stores/stockItemStore'
import { useStockLevelStore } from '../stores/stockLevelStore'

async function waitForApiStartupAsync() {
    const healthApiService = new HealthApiService();
    let retryCount = 0;
    while (retryCount < 5) {
        if (await healthApiService.healthCheckAsync()) {
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
        retryCount++;
    }

    if (retryCount == 5) {
        Notify.create({ type: 'oopsie' })
    }
}

await waitForApiStartupAsync()
await Promise.all([
    useMerchantStore().getMerchantsAsync(),
    useProductStore().getProductsAsync(),
    useStockItemStore().getStockItemsAsync(),
    useStockLevelStore().getStockLevelsAsync()
]);
