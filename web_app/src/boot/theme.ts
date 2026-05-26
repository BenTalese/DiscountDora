import { useAuthStore } from 'src/stores/authStore';
import ThemeService from 'src/services/themeService';
import { watch } from 'vue';

const themeService = new ThemeService();

// Pre-auth, force the brand default light theme. Previously this honoured
// OS preference via `applyTheme()`, which would flip to the dark theme +
// Quasar Dark.set(true) before any user existed — breaking light-only
// surfaces like the login page. The login page also self-scopes its own
// palette so it survives any future theme-boot weirdness, but defaulting
// to a known light theme keeps the initial paint sane everywhere.
themeService.applyDefault();

const authStore = useAuthStore();
watch(
    () => authStore.currentUser,
    (user) => {
        if (!user) {
            // Signed out — back to the brand default. We don't honour OS
            // dark mode until the user has chosen a theme themselves.
            themeService.applyDefault();
            return;
        }
        themeService.applyForUser(user.theme, user.font_family, user.font_size);
    },
    { immediate: true }
);
