<template>
    <q-card flat bordered>
        <q-card-section>
            <div class="text-h6">Account</div>
            <div class="text-caption text-grey">Your sign-in identity.</div>
        </q-card-section>

        <q-separator />

        <q-card-section v-if="currentUser">
            <div class="row items-center q-gutter-md">
                <q-avatar size="60px" color="amber-3" text-color="grey-10">
                    {{ initials }}
                </q-avatar>
                <div>
                    <div class="text-h6">{{ currentUser.username }}</div>
                    <div class="text-caption text-grey">
                        {{ currentUser.email ?? 'No email on file.' }}
                    </div>
                </div>
            </div>

            <q-list class="q-mt-md" separator>
                <q-item>
                    <q-item-section>
                        <q-item-label caption>User ID</q-item-label>
                        <q-item-label class="text-mono">{{ currentUser.user_id }}</q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card-section>

        <q-card-section v-else>
            <q-banner class="bg-grey-2" dense>Not signed in.</q-banner>
        </q-card-section>

        <q-separator />

        <q-card-section>
            <div class="text-subtitle2 q-mb-sm">Danger zone</div>
            <div class="text-caption text-grey q-mb-md">
                Sign out of this device. Your data stays where it is on the server.
            </div>
            <q-btn
                color="negative"
                no-caps
                icon="logout"
                label="Sign out"
                :loading="signingOut"
                @click="onSignOut"
            />
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const signingOut = ref(false);

    const initials = computed(() => {
        const name = currentUser.value?.username ?? '';
        return name.length > 0 ? name.charAt(0).toUpperCase() : '?';
    });

    async function onSignOut() {
        signingOut.value = true;
        try {
            await authStore.logoutAsync();
            void router.push('/login');
        } finally {
            signingOut.value = false;
        }
    }
</script>

<style scoped>
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85em;
    }
</style>
