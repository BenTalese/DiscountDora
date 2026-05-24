import { acceptHMRUpdate, defineStore } from 'pinia';
import type { AuthenticatedUser } from 'src/models/auth';
import type {
    ChangePasswordCommand,
    LoginCommand,
    RegisterCommand,
    UpdateMeCommand
} from 'src/services/api/authApiService';
import AuthApiService from 'src/services/api/authApiService';
import { NormalisedApiError, setUnauthorizedHandler } from 'src/services/api/axiosHttpClient';
import { computed, readonly, ref } from 'vue';

const authApiService = new AuthApiService();

export const useAuthStore = defineStore('auth', () => {
    const currentUser = ref<AuthenticatedUser | null>(null);
    // Tracks the boot probe so route guards can wait for it instead of
    // redirecting to /login on the very first navigation.
    const isBootstrapped = ref(false);
    // Set when the boot probe fails to reach the backend. The splash screen
    // watches this and surfaces a retry button instead of hanging silently.
    const bootstrapError = ref<string | null>(null);

    // Resolver for the in-flight bootstrap waiter: when bootstrap fails we
    // park the loop on a promise, then the splash's Retry button resolves it
    // to make us attempt the probe again.
    let retryResolver: (() => void) | null = null;
    // App.vue front-loads bootstrap and the router guard also awaits it.
    // We share the same in-flight promise so the second caller doesn't kick
    // off a duplicate /auth/me request.
    let inflightBootstrap: Promise<void> | null = null;

    const isAuthenticated = () => currentUser.value !== null;
    const isAdmin = computed(() => currentUser.value?.is_admin === true);

    const runBootstrap = async () => {
        while (!isBootstrapped.value) {
            try {
                currentUser.value = await authApiService.getMeAsync();
                isBootstrapped.value = true;
                bootstrapError.value = null;
            } catch (error) {
                bootstrapError.value =
                    error instanceof NormalisedApiError && error.isNetworkError
                        ? "Can't reach the server. Check your connection and try again."
                        : 'Something went wrong starting up. Try again in a moment.';
                await new Promise<void>((resolve) => {
                    retryResolver = resolve;
                });
            }
        }
    };

    const bootstrapAsync = (): Promise<void> => {
        if (isBootstrapped.value) return Promise.resolve();
        if (!inflightBootstrap) inflightBootstrap = runBootstrap();
        return inflightBootstrap;
    };

    const retryBootstrap = () => {
        bootstrapError.value = null;
        const resolve = retryResolver;
        retryResolver = null;
        resolve?.();
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
        bootstrapError: readonly(bootstrapError),
        isAdmin,
        isAuthenticated,
        bootstrapAsync,
        retryBootstrap,
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
