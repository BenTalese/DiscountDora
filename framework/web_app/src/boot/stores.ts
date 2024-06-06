import { useMerchantStore } from '../stores/MerchantStore'
import { useProductStore } from '../stores/ProductStore'
import { useStockItemStore } from '../stores/stockItemStore'
import { useStockLevelStore } from '../stores/stockLevelStore'

const merchantStore = useMerchantStore()
const productStore = useProductStore()
const stockItemStore = useStockItemStore()
const stockLevelStore = useStockLevelStore()

merchantStore.getMerchantsAsync()
productStore.getProductsAsync()
stockItemStore.getStockItemsAsync()
stockLevelStore.getStockLevelsAsync()
