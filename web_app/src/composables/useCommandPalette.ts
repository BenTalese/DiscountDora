import { ref } from 'vue';

// Module-level open state so any screen can pop the palette via openPalette().
// The CommandPalette component is mounted once in MainLayout and reads this.

const paletteOpen = ref(false);
const hasEverOpened = ref(false);

// Declared as arrow functions so destructuring them doesn't trip the
// no-unbound-method lint rule (they don't rely on `this`).
const openPalette = (): void => {
    hasEverOpened.value = true;
    paletteOpen.value = true;
};
const closePalette = (): void => {
    paletteOpen.value = false;
};
const togglePalette = (): void => {
    if (paletteOpen.value) paletteOpen.value = false;
    else openPalette();
};

export function useCommandPalette() {
    return { paletteOpen, hasEverOpened, openPalette, closePalette, togglePalette };
}
