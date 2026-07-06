<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Users"
            description="Manage every account in this install."
            :icon="ICONS.group"
        >
            <template #actions>
                <BaseButton
                    variant="primary"
                    :icon="ICONS.person_add"
                    label="Add user"
                    @click="onAddClick"
                />
                <BaseButton
                    variant="icon"
                    :icon="ICONS.refresh"
                    :loading="loading"
                    @click="loadUsers"
                >
                    <q-tooltip>Refresh user list</q-tooltip>
                </BaseButton>
            </template>
        </SettingsPageHeader>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-list class="settings-list" separator>
            <q-item v-for="user in users" :key="user.user_id" class="q-py-md">
                <q-item-section avatar>
                    <UserAvatar
                        :user-id="user.user_id"
                        :has-image="user.has_image"
                        size="42px"
                        fallback="initials"
                        :username="user.username"
                        :color="user.is_admin ? 'accent' : undefined"
                        :class="user.is_admin ? '' : 'dora-bg-sunken dora-text-secondary'"
                        :text-color="user.is_admin ? 'dark' : undefined"
                    />
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
                        <BaseButton
                            variant="ghost"
                            dense
                            :icon="ICONS.edit"
                            label="Edit"
                            @click="onEdit(user)"
                        />
                        <BaseButton
                            variant="ghost"
                            dense
                            :icon="ICONS.lock_reset"
                            label="Reset pwd"
                            :loading="resettingId === user.user_id"
                            @click="onResetPassword(user)"
                        />
                        <BaseButton
                            variant="ghost"
                            dense
                            :icon="ICONS.delete"
                            label="Delete"
                            class="text-negative"
                            :disable="
                                user.user_id === currentUserId ||
                                deletingId === user.user_id
                            "
                            :loading="deletingId === user.user_id"
                            @click="onDelete(user)"
                        >
                            <q-tooltip v-if="user.user_id === currentUserId">
                                You can't delete your own account.
                            </q-tooltip>
                        </BaseButton>
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
            <AppSpinner size="48px" />
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
                    <BaseButton
                        label="Save"
                        :loading="savingEdit"
                        :disable="!editingUsername.trim()"
                        @click="onSaveEdit"
                    />
                </template>
        </BaseDialog>

        <!-- Add-user dialog ─────────────────────────────────────── -->
        <BaseDialog
            v-model="createOpen"
            title="Add user"
            closable
            card-style="min-width: 320px; max-width: 480px"
        >
            <q-card-section class="q-gutter-md">
                <q-input
                    v-model="createDraft.username"
                    outlined
                    label="Username *"
                    :error="!!createFieldErrors.username"
                    :error-message="createFieldErrors.username"
                    @update:model-value="() => clearCreateField('username')"
                    autofocus
                />
                <q-input
                    v-model="createDraft.email"
                    outlined
                    label="Email (optional)"
                    :error="!!createFieldErrors.email"
                    :error-message="createFieldErrors.email"
                    @update:model-value="() => clearCreateField('email')"
                />
                <q-toggle
                    v-model="createDraft.is_admin"
                    label="Admin"
                />
                <div class="text-caption dora-text-muted">
                    Dora will generate a one-time password. You'll see it once — copy it
                    and share it with the user out-of-band.
                </div>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    label="Create"
                    :loading="creating"
                    :disable="!createDraft.username.trim()"
                    @click="onSubmitCreate"
                />
            </template>
        </BaseDialog>

        <!-- One-time-password result dialog (shared by create + reset) ── -->
        <BaseDialog
            v-model="resetResultOpen"
            :title="resetResultKind === 'create' ? 'User created' : 'Password reset'"
            closable
            card-style="min-width: 320px"
        >
                <q-card-section>
                    <div class="text-caption dora-text-muted">
                        <span v-if="resetResultKind === 'create'">
                            Copy this one-time password and pass it to
                            {{ resetTargetName }} out-of-band. They'll be
                            able to log in with it and change it themselves.
                            It's shown once.
                        </span>
                        <span v-else>
                            Copy this and pass it to {{ resetTargetName }}
                            out-of-band. It's shown once.
                        </span>
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
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { copyToClipboard, useQuasar } from 'quasar';
    import UserAdminApiService, {
        type AdminCreateUserCommand,
        type AdminUser
    } from 'src/services/api/userAdminApiService';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import UserAvatar from 'src/components/UserAvatar.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { describeApiError, toastCaption } from 'src/services/errorHandling/apiErrorHandler';

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

    const deletingId = ref<string | null>(null);

    // Create-user dialog state. Fresh reactive draft each open (see openCreate).
    const createOpen = ref(false);
    const creating = ref(false);
    const createDraft = reactive<AdminCreateUserCommand & { username: string; email: string; is_admin: boolean }>({
        username: '',
        email: '',
        is_admin: false,
    });
    const createFieldErrors = ref<Record<string, string>>({});
    function clearCreateField(field: 'username' | 'email') {
        if (createFieldErrors.value[field]) {
            const next = { ...createFieldErrors.value };
            delete next[field];
            createFieldErrors.value = next;
        }
    }

    // One-time-password result dialog is shared by create + reset — the copy
    // text depends on which flow produced the password.
    const resetResultOpen = ref(false);
    const resetResult = ref('');
    const resetTargetName = ref('');
    const resetResultKind = ref<'create' | 'reset'>('reset');

    const currentUserId = computed(() => currentUser.value?.user_id ?? null);

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
            // FU-016 — when the admin is editing themselves (self-demote,
            // rename, email change), the admin-user list refresh above
            // doesn't touch `authStore.currentUser`. Without this refresh
            // the router guard, MainLayout, SettingsShell, and every
            // admin page keep reading a stale `is_admin`/`username`, so
            // the demoted admin still sees admin surfaces until the next
            // hard reload. Backend prevents removing the last admin so
            // this can't lock the caller out.
            if (user.user_id === currentUser.value?.user_id) {
                await authStore.refreshAsync();
            }
            return true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Update failed.',
                caption: toastCaption(err)
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
            resetResultKind.value = 'reset';
            resetResultOpen.value = true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Reset failed.',
                caption: toastCaption(err)
            });
        } finally {
            resettingId.value = null;
        }
    }

    // FU-461 close-out (2026-07-06) — Add / Delete on the users page.
    function onAddClick() {
        createDraft.username = '';
        createDraft.email = '';
        createDraft.is_admin = false;
        createFieldErrors.value = {};
        createOpen.value = true;
    }

    async function onSubmitCreate() {
        if (!createDraft.username.trim()) return;
        creating.value = true;
        createFieldErrors.value = {};
        try {
            const payload: AdminCreateUserCommand = {
                username: createDraft.username.trim(),
                is_admin: createDraft.is_admin,
            };
            const email = createDraft.email.trim();
            if (email.length > 0) payload.email = email;

            const { new_password } = await api.createAsync(payload);
            createOpen.value = false;
            resetResult.value = new_password;
            resetTargetName.value = payload.username;
            resetResultKind.value = 'create';
            resetResultOpen.value = true;
            await loadUsers();
        } catch (err) {
            // Server maps username-taken / email-taken to 400 with a friendly
            // detail; validation problems (bad email) come back as 422 with a
            // per-field errors map. Surface both inline.
            const problem = (err as { response?: { data?: { errors?: Record<string, string[]>; detail?: string } } })?.response?.data;
            if (problem?.errors) {
                const next: Record<string, string> = {};
                for (const [field, messages] of Object.entries(problem.errors)) {
                    if (Array.isArray(messages) && messages.length > 0) {
                        next[field] = messages[0]!;
                    }
                }
                createFieldErrors.value = next;
            } else if (problem?.detail?.toLowerCase().includes('username')) {
                createFieldErrors.value = { username: problem.detail };
            } else if (problem?.detail?.toLowerCase().includes('email')) {
                createFieldErrors.value = { email: problem.detail };
            } else {
                $q.notify({
                    type: 'negative',
                    position: 'bottom-right',
                    message: 'Could not create user.',
                    caption: toastCaption(err),
                });
            }
        } finally {
            creating.value = false;
        }
    }

    async function onDelete(user: AdminUser) {
        const confirm = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${user.username}"?`,
                message:
                    `Their sessions, alert preferences and push subscriptions ` +
                    `will be removed. Household-shared things they touched ` +
                    `(recipes, shopping lists) stay in the household.`,
                cancel: true,
                persistent: true,
                ok: { color: 'negative', label: 'Delete' },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!confirm) return;

        deletingId.value = user.user_id;
        try {
            await api.deleteAsync(user.user_id);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Deleted "${user.username}".`,
            });
            await loadUsers();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Delete failed.',
                caption: toastCaption(err),
            });
        } finally {
            deletingId.value = null;
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
                caption: toastCaption(err)
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
