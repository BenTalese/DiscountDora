import { acceptHMRUpdate, defineStore } from 'pinia';
import type { AuthenticatedUser } from 'src/models/auth';
import type {
    ChangePasswordCommand,
    LoginCommand,
    RegisterCommand,
    UpdateMeCommand
} from 'src/services/api/authApiService';
import AuthApiService from 'src/services/api/authApiService';
import { setUnauthorizedHandler } from 'src/services/api/axiosHttpClient';
import { computed, readonly, ref } from 'vue';

const authApiService = new AuthApiService();

export const useAuthStore = defineStore('auth', () => {
    const currentUser = ref<AuthenticatedUser | null>(null);
    // Tracks the boot probe so route guards can wait for it instead of
    // redirecting to /login on the very first navigation.
    const isBootstrapped = ref(false);

    const isAuthenticated = () => currentUser.value !== null;
    const isAdmin = computed(() => currentUser.value?.is_admin === true);

    const bootstrapAsync = async () => {
        if (isBootstrapped.value) return;
        currentUser.value = await authApiService.getMeAsync();
        isBootstrapped.value = true;
    };

    /** Force a fresh /me probe (e.g. after the user restarts onboarding so
     *  `onboarding_completed_at` flips back to null and the guard kicks in). */
    const refreshAsync = async () => {
        currentUser.value = await authApiService.getMeAsync();
    };

    const loginAsync = async (command: LoginCommand) => {
        currentUser.value = await authApiService.loginAsync(command);
    };

    const registerAsync = async (command: RegisterCommand) => {
        currentUser.value = await authApiService.registerAsync(command);
    };

    const updateMeAsync = async (command: UpdateMeCommand) => {
        currentUser.value = await authApiService.updateMeAsync(command);
    };

    const changePasswordAsync = async (command: ChangePasswordCommand) => {
        await authApiService.changePasswordAsync(command);
    };

    const logoutAsync = async () => {
        try {
            await authApiService.logoutAsync();
        } finally {
            currentUser.value = null;
        }
    };

    // Called by the axios interceptor when any non-auth-probe request returns
    // 401 — typically means the cookie expired or was cleared server-side.
    const handleSessionExpired = () => {
        currentUser.value = null;
    };
    setUnauthorizedHandler(handleSessionExpired);

    return {
        currentUser: readonly(currentUser),
        isBootstrapped: readonly(isBootstrapped),
        isAdmin,
        isAuthenticated,
        bootstrapAsync,
        refreshAsync,
        loginAsync,
        registerAsync,
        updateMeAsync,
        changePasswordAsync,
        logoutAsync
    };
});

if (import.meta.hot) {
    import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot));
}
