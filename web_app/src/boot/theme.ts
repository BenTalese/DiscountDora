import { useAuthStore } from 'src/stores/authStore';
import ThemeService from 'src/services/themeService';
import { watch } from 'vue';

const themeService = new ThemeService();

// Paint with the OS preference immediately so we don't flash light-on-dark
// (or vice versa) while waiting for /auth/me. Once the user's saved prefs
// load, apply them — and re-apply on every change.
themeService.applyTheme();

const authStore = useAuthStore();
watch(
    () => authStore.currentUser,
    (user) => {
        if (!user) {
            // Logged out — fall back to OS preference.
            themeService.applyTheme();
            return;
        }
        themeService.applyForUser(user.theme, user.font_family, user.font_size);
    },
    { immediate: true }
);
