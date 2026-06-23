<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Users"
            description="Manage every account in this install."
            :icon="ICONS.group"
        >
            <template #actions>
                <q-btn
                    flat
                    round
                    dense
                    :icon="ICONS.refresh"
                    :loading="loading"
                    @click="loadUsers"
                >
                    <q-tooltip>Refresh user list</q-tooltip>
                </q-btn>
            </template>
        </SettingsPageHeader>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-list class="settings-list" separator>
            <q-item v-for="user in users" :key="user.user_id" class="q-py-md">
                <q-item-section avatar>
                    <q-avatar
                        :color="user.is_admin ? 'accent' : undefined"
                        :class="user.is_admin ? '' : 'dora-bg-sunken dora-text-secondary'"
                        :text-color="user.is_admin ? 'dark' : undefined"
                        size="42px"
                    >
                        {{ initials(user.username) }}
                    </q-avatar>
                </q-item-section>
                <q-item-section>
                    <q-item-label class="text-weight-medium">
                        {{ user.username }}
                        <q-badge
                            v-if="user.is_admin"
                            color="warning"
                            text-color="white"
                            class="q-ml-sm"
                        >
                            admin
                        </q-badge>
                        <q-badge
                            v-if="user.user_id === currentUserId"
                            color="grey"
                            text-color="white"
                            class="q-ml-xs"
                        >
                            you
                        </q-badge>
                    </q-item-label>
                    <q-item-label caption>
                        {{ user.email ?? 'No email on file' }}
                    </q-item-label>
                </q-item-section>

                <q-item-section side>
                    <div class="row q-gutter-sm items-center">
                        <q-toggle
                            :model-value="user.is_admin"
                            label="Admin"
                            dense
                            :disable="
                                togglingId === user.user_id ||
                                user.user_id === currentUserId
                            "
                            @update:model-value="onToggleAdmin(user, $event)"
                        >
                            <q-tooltip v-if="user.user_id === currentUserId">
                                Use Preferences to manage your own account.
                            </q-tooltip>
                        </q-toggle>
                        <q-toggle
                            :model-value="user.deals_email_enabled"
                            label="Deals email"
                            dense
                            :disable="togglingId === user.user_id"
                            @update:model-value="onToggleDeals(user, $event)"
                        />
                        <q-btn
                            flat
                            dense
                            no-caps
                            :icon="ICONS.edit"
                            label="Edit"
                            @click="onEdit(user)"
                        />
                        <q-btn
                            flat
                            dense
                            no-caps
                            :icon="ICONS.lock_reset"
                            label="Reset pwd"
                            :loading="resettingId === user.user_id"
                            @click="onResetPassword(user)"
                        />
                    </div>
                </q-item-section>
            </q-item>

            <q-item v-if="!loading && users.length === 0">
                <q-item-section>
                    <q-item-label class="dora-text-muted">No users found.</q-item-label>
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && users.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>

        <!-- Edit dialog ─────────────────────────────────────────── -->
        <BaseDialog v-model="editOpen" :title="`Edit ${editingUser?.username ?? ''}`" closable card-style="min-width: 320px; max-width: 480px">
                <q-card-section>
                    <q-input
                        v-model="editingUsername"
                        label="Username"
                        outlined
                        dense
                        class="q-mb-md"
                    />
                    <q-input
                        v-model="editingEmail"
                        label="Email"
                        outlined
                        dense
                        placeholder="No email on file"
                    />
                </q-card-section>
                <template #actions>
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <q-btn
                        color="primary"
                        no-caps
                        label="Save"
                        :loading="savingEdit"
                        :disable="!editingUsername.trim()"
                        @click="onSaveEdit"
                    />
                </template>
        </BaseDialog>

        <!-- Password-reset result dialog ────────────────────────── -->
        <BaseDialog v-model="resetResultOpen" title="Password reset" closable card-style="min-width: 320px">
                <q-card-section>
                    <div class="text-caption dora-text-muted">
                        Copy this and pass it to {{ resetTargetName }} out-of-band.
                        It's shown once.
                    </div>
                </q-card-section>
                <q-card-section>
                    <q-input
                        :model-value="resetResult"
                        readonly
                        outlined
                        dense
                        class="reset-password-readout"
                    >
                        <template #append>
                            <q-btn
                                flat
                                round
                                dense
                                :icon="ICONS.content_copy"
                                @click="copyReset"
                            />
                        </template>
                    </q-input>
                </q-card-section>
                <template #actions>
                    <BaseButton variant="ghost" label="Done" v-close-popup />
                </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { copyToClipboard, useQuasar } from 'quasar';
    import UserAdminApiService, {
        type AdminUser
    } from 'src/services/api/userAdminApiService';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const api = new UserAdminApiService();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const users = ref<AdminUser[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const togglingId = ref<string | null>(null);
    const resettingId = ref<string | null>(null);

    const editOpen = ref(false);
    const editingUser = ref<AdminUser | null>(null);
    const editingUsername = ref('');
    const editingEmail = ref('');
    const savingEdit = ref(false);

    const resetResultOpen = ref(false);
    const resetResult = ref('');
    const resetTargetName = ref('');

    const currentUserId = computed(() => currentUser.value?.user_id ?? null);

    function initials(name: string): string {
        return name.length > 0 ? name.charAt(0).toUpperCase() : '?';
    }

    async function loadUsers() {
        loading.value = true;
        loadError.value = null;
        try {
            const page = await api.getAllAsync();
            users.value = page.items;
        } catch (err) {
            loadError.value = `Could not load users: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    async function patch(user: AdminUser, command: Parameters<typeof api.updateAsync>[1]) {
        togglingId.value = user.user_id;
        try {
            await api.updateAsync(user.user_id, command);
            await loadUsers();
            return true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Update failed.',
                caption: describeApiError(err) || ''
            });
            return false;
        } finally {
            togglingId.value = null;
        }
    }

    async function onToggleAdmin(user: AdminUser, value: boolean) {
        await patch(user, { is_admin: value });
    }

    async function onToggleDeals(user: AdminUser, value: boolean) {
        await patch(user, { deals_email_enabled: value });
    }

    function onEdit(user: AdminUser) {
        editingUser.value = user;
        editingUsername.value = user.username;
        editingEmail.value = user.email ?? '';
        editOpen.value = true;
    }

    async function onSaveEdit() {
        if (!editingUser.value) return;
        savingEdit.value = true;
        const ok = await patch(editingUser.value, {
            username: editingUsername.value.trim(),
            email:
                editingEmail.value.trim() === '' ? null : editingEmail.value.trim()
        });
        savingEdit.value = false;
        if (ok) editOpen.value = false;
    }

    async function onResetPassword(user: AdminUser) {
        const confirm = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Reset password',
                message: `Generate a new one-time password for "${user.username}"?`,
                cancel: true,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!confirm) return;

        resettingId.value = user.user_id;
        try {
            const { new_password } = await api.resetPasswordAsync(user.user_id);
            resetResult.value = new_password;
            resetTargetName.value = user.username;
            resetResultOpen.value = true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Reset failed.',
                caption: describeApiError(err) || ''
            });
        } finally {
            resettingId.value = null;
        }
    }

    async function copyReset() {
        try {
            await copyToClipboard(resetResult.value);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Copied to clipboard.'
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not copy.',
                caption: describeApiError(err) || ''
            });
        }
    }

    onMounted(loadUsers);
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; position: relative; }
    .settings-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .reset-password-readout :deep(input) {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        letter-spacing: 0.05em;
    }
</style>
