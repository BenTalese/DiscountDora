import { ref } from 'vue';

// module-level state for the log-price sheet. Mirrors useQuickAdd
// so any screen can pop it without owning the component. <LogPriceSheet> is
// mounted once in MainLayout and reads this state; openLogPrice() flips it
// open. Optionally pre-selects a stock item (skips straight to the
// PriceEntry form).

export type LogPriceOptions = {
    stockItemId?: string | null;
};

const isOpen = ref(false);
const presetStockItemId = ref<string | null>(null);

export function useLogPrice() {
    function openLogPrice(options: LogPriceOptions = {}) {
        presetStockItemId.value = options.stockItemId ?? null;
        isOpen.value = true;
    }

    function closeLogPrice() {
        isOpen.value = false;
    }

    return {
        isOpen,
        presetStockItemId,
        openLogPrice,
        closeLogPrice,
    };
}
