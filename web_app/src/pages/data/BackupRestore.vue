<template>
    <div class="q-gutter-md">
        <q-banner class="dora-bg-sunken dora-text-secondary text-caption" dense rounded>
            <template #avatar>
                <q-icon :name="ICONS.info" size="18px" />
            </template>
            Backups capture your stock, lists, recipes, meal plans and saved products
            by default. Optional sections (system settings, user accounts,
            historic offers) can be ticked on per-backup. Passwords are never
            included.
        </q-banner>

        <div class="row q-col-gutter-md">
            <!-- ── Create ──────────────────────────────────────────── -->
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section class="row items-center q-gutter-md">
                        <q-icon :name="ICONS.cloud_download" size="32px" class="text-primary" />
                        <div>
                            <div class="text-h6">Create backup</div>
                            <div class="text-caption dora-text-muted">
                                Download a JSON snapshot of your install.
                            </div>
                            <div
                                v-if="lastBackupLabel"
                                class="text-caption dora-text-muted-7 q-mt-xs"
                            >
                                <q-icon :name="ICONS.schedule" size="14px" class="q-mr-xs" />
                                Last backup: {{ lastBackupLabel }}
                            </div>
                        </div>
                    </q-card-section>
                    <q-separator />
                    <q-card-section class="q-pb-none">
                        <div class="text-caption dora-text-muted-7 q-mb-xs">
                            Include in this backup:
                        </div>
                        <q-expansion-item
                            v-for="(group, idx) in backupSectionGroups"
                            :key="group.category"
                            :label="group.category"
                            :caption="`${countSelectedInGroup(group)} of ${group.sections.length} selected`"
                            :default-opened="idx === 0"
                            dense
                            header-class="q-px-none"
                        >
                            <div class="row items-center q-gutter-x-sm q-mb-xs">
                                <q-btn
                                    dense
                                    flat
                                    size="sm"
                                    label="All"
                                    @click="toggleGroup(group, true)"
                                />
                                <q-btn
                                    dense
                                    flat
                                    size="sm"
                                    label="None"
                                    @click="toggleGroup(group, false)"
                                />
                            </div>
                            <q-checkbox
                                v-for="section in group.sections"
                                :key="section.key"
                                v-model="backupSelected[section.key]"
                                dense
                                :label="section.label"
                                class="block"
                            />
                        </q-expansion-item>
                    </q-card-section>
                    <q-card-section>
                        <q-btn
                            color="primary"
                            :icon="ICONS.download"
                            label="Download backup"
                            :loading="downloading"
                            :disable="downloading || selectedBackupKeys.length === 0"
                            unelevated
                            @click="onDownload"
                        />
                    </q-card-section>
                </q-card>
            </div>

            <!-- ── Restore ─────────────────────────────────────────── -->
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section class="row items-center q-gutter-md">
                        <q-icon :name="ICONS.cloud_upload" size="32px" class="text-primary" />
                        <div>
                            <div class="text-h6">Restore from backup</div>
                            <div class="text-caption dora-text-muted">
                                Inspect a backup, then choose what to import.
                            </div>
                        </div>
                    </q-card-section>
                    <q-separator />
                    <q-card-section>
                        <q-file
                            v-model="pickedFile"
                            accept=".json,application/json"
                            outlined
                            dense
                            label="Choose a backup file"
                            :loading="inspecting"
                            @update:model-value="onFilePicked"
                        >
                            <template #prepend>
                                <q-icon :name="ICONS.attach_file" />
                            </template>
                            <template #append>
                                <q-btn
                                    v-if="pickedFile"
                                    flat
                                    dense
                                    round
                                    :icon="ICONS.close"
                                    @click.stop="onClearPick"
                                />
                            </template>
                        </q-file>
                        <div
                            v-if="inspecting && uploadProgressValue > 0 && uploadProgressValue < 1"
                            class="q-mt-sm"
                        >
                            <q-linear-progress
                                :value="uploadProgressValue"
                                rounded
                                size="6px"
                                color="primary"
                            />
                            <div class="text-caption dora-text-muted-7 q-mt-xs">
                                Uploading {{ Math.round(uploadProgressValue * 100) }}%
                            </div>
                        </div>
                        <div
                            v-else-if="inspecting && uploadProgressValue >= 1"
                            class="text-caption dora-text-muted-7 q-mt-sm"
                        >
                            Inspecting backup…
                        </div>
                    </q-card-section>
                </q-card>
            </div>
        </div>

        <!-- ── Preview tree (shows once /inspect returns) ─────────────────── -->
        <q-card v-if="preview" flat bordered>
            <q-card-section class="row items-center justify-between">
                <div>
                    <div class="text-subtitle1">Backup preview</div>
                    <div class="text-caption dora-text-muted">
                        Exported {{ formatDate(preview.exported_at) }} by
                        <strong>{{ preview.exported_by }}</strong>
                    </div>
                </div>
                <div class="text-caption dora-text-muted">
                    <strong>{{ selectedCount }}</strong> of <strong>{{ selectableTotal }}</strong> items selected
                    <span v-if="duplicateCount">
                        · <strong>{{ duplicateCount }}</strong> duplicate{{ duplicateCount === 1 ? '' : 's' }} skipped
                    </span>
                </div>
            </q-card-section>

            <q-separator />

            <q-card-section class="q-pt-none">
                <div class="row q-gutter-sm q-mb-sm">
                    <BaseButton variant="ghost" class="text-primary" label="Select all" @click="onSelectAll" />
                    <BaseButton variant="ghost" label="Clear selection" @click="onClearSelection" />
                </div>

                <q-tree
                    :nodes="treeNodes"
                    node-key="key"
                    tick-strategy="leaf"
                    v-model:ticked="tickedKeys"
                    v-model:expanded="expandedKeys"
                    :no-nodes-label="'Empty backup.'"
                >
                    <template #default-header="prop">
                        <div class="row items-center full-width">
                            <div class="col">
                                <span>{{ prop.node.label }}</span>
                                <q-chip
                                    v-if="prop.node.duplicate"
                                    dense
                                    size="sm"
                                    color="warning"
                                    text-color="white"
                                    class="q-ml-sm"
                                >
                                    duplicate
                                </q-chip>
                            </div>
                            <div
                                v-if="prop.node.count !== undefined"
                                class="text-caption dora-text-muted q-ml-sm"
                            >
                                {{ prop.node.count }}
                            </div>
                        </div>
                    </template>
                </q-tree>
            </q-card-section>

            <q-separator />

            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" @click="onClearPick" />
                <q-btn
                    color="grey"
                    :icon="ICONS.done_all"
                    label="Restore all (skip duplicates)"
                    :loading="restoring"
                    :disable="restoring"
                    @click="onRestoreAll"
                />
                <q-btn
                    color="primary"
                    :icon="ICONS.check"
                    label="Restore selection"
                    :loading="restoring"
                    :disable="restoring || selectedCount === 0"
                    @click="onRestoreSelection"
                />
            </q-card-actions>
        </q-card>

        <!-- ── Restore report (shown after a commit) ─────────────────── -->
        <BaseDialog v-model="reportOpen" card-style="min-width: 360px; max-width: 600px">
                <q-card-section class="row items-center q-gutter-md">
                    <q-icon
                        :name="report?.ok ? 'check_circle' : 'error'"
                        :color="report?.ok ? 'positive' : 'negative'"
                        size="32px"
                    />
                    <div>
                        <div class="text-h6">
                            {{ report?.ok ? 'Restore complete' : 'Restore failed' }}
                        </div>
                        <div class="text-caption dora-text-muted">
                            {{ report?.headline ?? '' }}
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section v-if="report?.rows.length" class="q-py-none">
                    <q-list dense separator>
                        <q-item v-for="row in report.rows" :key="row.section">
                            <q-item-section>
                                <q-item-label>{{ row.label }}</q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <q-item-label class="text-caption">
                                    <span class="text-positive">+{{ row.created }}</span>
                                    <span class="dora-text-secondary"> · {{ row.skipped }} skipped</span>
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
                <q-card-section v-if="report?.warnings.length" class="q-pt-sm">
                    <q-expansion-item
                        :label="`${report.warnings.length} warning(s)`"
                        :icon="ICONS.warning"
                        dense
                    >
                        <q-list dense>
                            <q-item v-for="(w, i) in report.warnings" :key="i">
                                <q-item-section class="text-caption">{{ w }}</q-item-section>
                            </q-item>
                        </q-list>
                    </q-expansion-item>
                </q-card-section>
                <template #actions>
                    <BaseButton variant="ghost" label="Close" @click="reportOpen = false" />
                    <q-btn
                        v-if="report?.ok"
                        color="primary"
                        :icon="ICONS.refresh"
                        label="Reload now"
                        @click="reloadNow"
                    />
                </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';
    import { computed, ref } from 'vue';
    import { useChunkedUpload } from 'src/composables/useChunkedUpload';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import { useAuthStore } from 'src/stores/authStore';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const downloading = ref(false);
    const inspecting = ref(false);
    const restoring = ref(false);

    const pickedFile = ref<File | null>(null);
    const uploadId = ref<string | null>(null);
    const preview = ref<InspectResponse | null>(null);
    const tickedKeys = ref<string[]>([]);
    const expandedKeys = ref<string[]>([]);
    // Upload progress (0..1) used by the file picker overlay.
    // Shared chunked upload — same composable DataImport uses. The
    // composable owns its own `progress` ref and `inFlight` flag.
    const chunkedUpload = useChunkedUpload();
    const uploadProgressValue = chunkedUpload.progress;

    // 2 GB hard cap on the client. Matches the server's chunked-upload cap.
    const MAX_BACKUP_BYTES = 2 * 1024 * 1024 * 1024;

    // ── Restore report state ──────────────────────────────────────────
    interface ReportRow {
        section: string;
        label: string;
        created: number;
        skipped: number;
    }
    interface RestoreReport {
        ok: boolean;
        headline: string;
        rows: ReportRow[];
        warnings: string[];
    }
    const report = ref<RestoreReport | null>(null);
    const reportOpen = ref(false);

    // ── Last backup label ─────────────────────────────────────────────
    const lastBackupLabel = computed(() => {
        const iso = currentUser.value?.last_backup_at ?? null;
        if (!iso) return null;
        try {
            const when = new Date(iso);
            const diffMs = Date.now() - when.getTime();
            const diffMins = Math.floor(diffMs / 60000);
            if (diffMins < 1) return 'just now';
            if (diffMins < 60) return `${diffMins} min ago`;
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours} hr ago`;
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
            return when.toLocaleDateString();
        } catch {
            return iso;
        }
    });

    interface InspectSampleRow {
        id: string;
        name: string;
    }
    interface InspectSample {
        rows: InspectSampleRow[];
        truncated: boolean;
    }
    interface InspectResponse {
        schema_version: number;
        exported_at: string | null;
        exported_by: string | null;
        sections: string[];
        entity_counts: Record<string, number>;
        duplicates: Record<string, string[]>;
        samples: Record<string, InspectSample>;
    }

    // Mirrors dora_api/features/data/restore_shared.SECTIONS. Keep this in
    // sync if new sections land server-side — the order here drives the
    // checkbox order in the Create-backup card, and `defaultOn` drives the
    // initial state of each toggle.
    interface BackupSection {
        key: string;
        label: string;
        category: string;
        defaultOn: boolean;
    }
    const BACKUP_SECTIONS: BackupSection[] = [
        { key: 'stock_groups', label: 'Stock groups', category: 'Core data', defaultOn: true },
        { key: 'stock_levels', label: 'Stock levels', category: 'Core data', defaultOn: true },
        { key: 'stock_locations', label: 'Stock locations', category: 'Core data', defaultOn: true },
        { key: 'saved_products', label: 'Saved products', category: 'Core data', defaultOn: true },
        { key: 'stock_items', label: 'Stock items', category: 'Core data', defaultOn: true },
        { key: 'product_stock_item_links', label: 'Product ↔ stock-item links', category: 'Core data', defaultOn: true },
        { key: 'stock_item_substitutes', label: 'Stock-item substitutes', category: 'Core data', defaultOn: true },
        { key: 'shopping_lists', label: 'Shopping lists', category: 'Core data', defaultOn: true },
        { key: 'shopping_list_items', label: 'Shopping list items', category: 'Core data', defaultOn: true },
        { key: 'shopping_list_templates', label: 'Shopping list templates', category: 'Core data', defaultOn: true },
        { key: 'shopping_list_template_lines', label: 'Template lines', category: 'Core data', defaultOn: true },
        { key: 'recipe_collections', label: 'Recipe collections', category: 'Core data', defaultOn: true },
        { key: 'recipes', label: 'Recipes', category: 'Core data', defaultOn: true },
        { key: 'recipe_ingredients', label: 'Recipe ingredients', category: 'Core data', defaultOn: true },
        { key: 'meal_plans', label: 'Meal plans', category: 'Core data', defaultOn: true },
        { key: 'meal_plan_entries', label: 'Meal plan entries', category: 'Core data', defaultOn: true },
        { key: 'product_barcodes', label: 'Product barcodes', category: 'Core data', defaultOn: true },
        { key: 'app_settings', label: 'System settings', category: 'Optional', defaultOn: false },
        { key: 'users', label: 'User accounts (no passwords)', category: 'Optional', defaultOn: false },
        { key: 'product_historic_offers', label: 'Historic product offers', category: 'Optional', defaultOn: false },
    ];

    const backupSelected = ref<Record<string, boolean>>(
        Object.fromEntries(BACKUP_SECTIONS.map((s) => [s.key, s.defaultOn])),
    );

    interface BackupSectionGroup {
        category: string;
        sections: BackupSection[];
    }
    const backupSectionGroups = computed<BackupSectionGroup[]>(() => {
        const byCategory = new Map<string, BackupSection[]>();
        for (const s of BACKUP_SECTIONS) {
            const bucket = byCategory.get(s.category) ?? [];
            bucket.push(s);
            byCategory.set(s.category, bucket);
        }
        return Array.from(byCategory.entries()).map(([category, sections]) => ({
            category,
            sections,
        }));
    });

    function countSelectedInGroup(group: BackupSectionGroup): number {
        return group.sections.filter((s) => backupSelected.value[s.key]).length;
    }

    function toggleGroup(group: BackupSectionGroup, on: boolean) {
        for (const s of group.sections) {
            backupSelected.value[s.key] = on;
        }
    }

    const selectedBackupKeys = computed(() =>
        BACKUP_SECTIONS.filter((s) => backupSelected.value[s.key]).map((s) => s.key),
    );

    // Labels for the restore tree share the BACKUP_SECTIONS catalogue so the
    // two stay in sync as sections come and go.
    const SECTION_LABELS: Record<string, string> = Object.fromEntries(
        BACKUP_SECTIONS.map((s) => [s.key, s.label]),
    );

    // Sections the user can pick into in the restore tree. Sub-tables
    // (lines, ingredients, m2m, historic offers) ride along server-side via
    // CHILD_AUTO_INCLUDE, so we don't surface them.
    const TOP_LEVEL_KEYS = [
        'stock_groups',
        'stock_levels',
        'stock_locations',
        'saved_products',
        'stock_items',
        'shopping_lists',
        'shopping_list_templates',
        'recipe_collections',
        'recipes',
        'meal_plans',
        'app_settings',
        'users',
    ];

    // Tree node structure tracks two things:
    //  - `composite` (m2m) entries use "<id>|<id>"; everything else uses the
    //    plain UUID. We mirror the server-side composite_key tuple format.
    interface TreeNode {
        key: string;
        label: string;
        section?: string;
        compositeId?: string;
        duplicate?: boolean;
        count?: number;
        children?: TreeNode[];
        tickable?: boolean;
        noTick?: boolean;
        disabled?: boolean;
    }

    const treeNodes = computed<TreeNode[]>(() => {
        if (!preview.value) return [];
        const dupes = preview.value.duplicates;
        const out: TreeNode[] = [];

        for (const section of TOP_LEVEL_KEYS) {
            const sample = preview.value.samples[section];
            const total = preview.value.entity_counts[section] ?? 0;
            if (!sample || total === 0) continue;

            const dupNames = new Set(dupes[section] ?? []);
            const children: TreeNode[] = sample.rows.map((row) => {
                const isDuplicate = dupNames.has(row.name);
                return {
                    key: `${section}:${row.id}`,
                    label: row.name,
                    section,
                    compositeId: row.id,
                    duplicate: isDuplicate,
                    // q-tree honours `noTick` to keep a leaf in the tree but
                    // skip ticking; combined with `disabled` it greys out.
                    noTick: isDuplicate,
                    disabled: isDuplicate,
                };
            });

            // For truncated sections, surface an overflow leaf so the user
            // knows there's more — selection beyond the sample requires
            // "Restore all (skip duplicates)".
            if (sample.truncated) {
                const hidden = total - sample.rows.length;
                children.push({
                    key: `${section}:__truncated__`,
                    label: `… and ${hidden.toLocaleString()} more not shown`,
                    section,
                    noTick: true,
                    disabled: true,
                });
            }

            out.push({
                key: `section:${section}`,
                label: SECTION_LABELS[section] ?? section,
                count: total,
                children,
            });
        }

        return out;
    });

    const selectableTotal = computed(() => {
        let n = 0;
        for (const root of treeNodes.value) {
            for (const child of root.children ?? []) {
                if (child.disabled) continue;
                if (child.duplicate) continue;
                n += 1;
            }
        }
        return n;
    });

    const duplicateCount = computed(() => {
        if (!preview.value) return 0;
        return Object.values(preview.value.duplicates).reduce((acc, arr) => acc + arr.length, 0);
    });

    // `tick-strategy="leaf"` keeps roots out of `tickedKeys`, so a plain
    // length is what we want here.
    const selectedCount = computed(() => tickedKeys.value.length);

    function formatDate(iso: string | null): string {
        if (!iso) return 'an unknown time';
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return iso;
        }
    }

    // ── Download ──────────────────────────────────────────────────────
    async function onDownload() {
        downloading.value = true;
        try {
            const baseUrl = resolveBaseURL('dora');
            const query = selectedBackupKeys.value.length
                ? `?sections=${encodeURIComponent(selectedBackupKeys.value.join(','))}`
                : '';
            const response = await fetch(`${baseUrl}/data/backup${query}`, {
                method: 'GET',
                credentials: 'include',
            });
            if (!response.ok) {
                throw new Error(`Backup failed (${response.status})`);
            }
            const filename = parseFilename(response.headers.get('content-disposition'))
                ?? defaultFilename();
            const blob = await response.blob();
            triggerSave(blob, filename);
            // The backup endpoint stamps `last_backup_at` on the user as a
            // side effect; refresh /me so the card label updates without
            // waiting for the next page navigation.
            void authStore.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Backup downloaded.',
                timeout: 3000,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't download backup.",
                caption: err instanceof Error ? err.message : String(err),
            });
        } finally {
            downloading.value = false;
        }
    }

    function parseFilename(header: string | null): string | null {
        if (!header) return null;
        const match = /filename="?([^";]+)"?/i.exec(header);
        return match?.[1] ?? null;
    }

    function defaultFilename(): string {
        const today = new Date().toISOString().slice(0, 10);
        return `dora-backup-${today}.json`;
    }

    function triggerSave(blob: Blob, filename: string) {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
    }

    // ── Restore: pick → chunked upload → inspect → tree → commit ──────
    async function onFilePicked(file: File | null) {
        if (!file) return;
        if (file.size > MAX_BACKUP_BYTES) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: `That file is over the ${(MAX_BACKUP_BYTES / 1024 / 1024 / 1024).toFixed(0)} GB limit (${(file.size / 1024 / 1024).toFixed(1)} MB).`,
            });
            pickedFile.value = null;
            return;
        }

        inspecting.value = true;
        const baseUrl = resolveBaseURL('dora');

        try {
            // ── Upload via the shared chunked-upload composable ──────
            const id = await chunkedUpload.upload(file);
            uploadId.value = id;

            // ── Inspect (server stream-parses the staged file) ───────
            const inspectResponse = await fetch(`${baseUrl}/data/backup/inspect`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ upload_id: id }),
            });
            if (!inspectResponse.ok) {
                throw new Error(await describeError(inspectResponse));
            }
            preview.value = await inspectResponse.json();

            // Default expansion: first 3 top-level sections with rows.
            const sectionsWithRows = TOP_LEVEL_KEYS.filter((k) =>
                (preview.value?.entity_counts[k] ?? 0) > 0,
            );
            expandedKeys.value = sectionsWithRows.slice(0, 3).map((k) => `section:${k}`);
            tickedKeys.value = [];
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't read that backup file.",
                caption: err instanceof Error ? err.message : String(err),
            });
            await onClearPick();
        } finally {
            inspecting.value = false;
        }
    }

    async function describeError(response: Response): Promise<string> {
        const body = await response.json().catch(() => null);
        return body?.detail ?? body?.title ?? `HTTP ${response.status}`;
    }

    async function onClearPick() {
        // Best-effort abort of the staged upload so we don't leave dead
        // files lying around when the user backs out. TTL would clean
        // them eventually, but proactive is friendlier.
        if (uploadId.value) {
            await chunkedUpload.abort(uploadId.value);
        }
        chunkedUpload.reset();
        pickedFile.value = null;
        uploadId.value = null;
        preview.value = null;
        tickedKeys.value = [];
        expandedKeys.value = [];
    }

    function onSelectAll() {
        const keys: string[] = [];
        for (const root of treeNodes.value) {
            for (const child of root.children ?? []) {
                if (child.disabled || child.duplicate) continue;
                keys.push(child.key);
            }
        }
        tickedKeys.value = keys;
    }

    function onClearSelection() {
        tickedKeys.value = [];
    }

    async function onRestoreSelection() {
        await confirmAndRestore('partial');
    }

    async function onRestoreAll() {
        await confirmAndRestore('all_skip_duplicates');
    }

    function confirmAndRestore(mode: 'partial' | 'all_skip_duplicates') {
        return new Promise<void>((resolve) => {
            const summary = mode === 'partial'
                ? `${selectedCount.value} selected item(s) will be imported. Duplicates will be skipped.`
                : `Everything in the backup will be imported, except rows that already exist locally.`;
            $q.dialog({
                title: 'Confirm restore',
                message: `${summary}<br><br>This can't be undone.`,
                html: true,
                ok: { label: 'Restore', color: 'primary' },
                cancel: { label: 'Cancel', flat: true },
            }).onOk(() => {
                void (async () => {
                    await doRestore(mode);
                    resolve();
                })();
            }).onCancel(() => resolve());
        });
    }

    async function doRestore(mode: 'partial' | 'all_skip_duplicates') {
        if (!uploadId.value) return;
        restoring.value = true;
        try {
            const selection: Record<string, string[]> = {};
            if (mode === 'partial') {
                for (const key of tickedKeys.value) {
                    const sep = key.indexOf(':');
                    if (sep < 0) continue;
                    const section = key.slice(0, sep);
                    const id = key.slice(sep + 1);
                    if (!selection[section]) selection[section] = [];
                    selection[section].push(id);
                }
            }
            const baseUrl = resolveBaseURL('dora');
            const response = await fetch(`${baseUrl}/data/backup/restore`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: uploadId.value,
                    selection,
                    mode,
                }),
            });
            if (!response.ok) {
                const body = await response.json().catch(() => null);
                const detail = body?.detail ?? body?.title ?? `HTTP ${response.status}`;
                throw new Error(detail);
            }
            const summary = await response.json() as {
                created: Record<string, number>;
                skipped: Record<string, number>;
                warnings: string[];
            };
            const totalCreated = Object.values(summary.created).reduce((a, b) => a + b, 0);
            const totalSkipped = Object.values(summary.skipped).reduce((a, b) => a + b, 0);

            // Build the per-section report rows — only show sections that
            // actually saw activity (created or skipped). Sub-tables that
            // were touched by parent auto-include get reported too.
            const rows: ReportRow[] = [];
            for (const section of BACKUP_SECTIONS) {
                const created = summary.created[section.key] ?? 0;
                const skipped = summary.skipped[section.key] ?? 0;
                if (created === 0 && skipped === 0) continue;
                rows.push({
                    section: section.key,
                    label: section.label,
                    created,
                    skipped,
                });
            }

            report.value = {
                ok: true,
                headline:
                    `Restored ${totalCreated} row(s), skipped ${totalSkipped}` +
                    (summary.warnings.length
                        ? ` (${summary.warnings.length} warning${summary.warnings.length === 1 ? '' : 's'}).`
                        : '.'),
                rows,
                warnings: summary.warnings,
            };
            reportOpen.value = true;
            // The staged file was consumed server-side; forget the id so a
            // later abort doesn't 404 chasing a phantom upload.
            uploadId.value = null;
        } catch (err) {
            report.value = {
                ok: false,
                headline: err instanceof Error ? err.message : String(err),
                rows: [],
                warnings: [],
            };
            reportOpen.value = true;
        } finally {
            restoring.value = false;
        }
    }

    function reloadNow() {
        // Hard reload — cheapest way to make sure every store reflects the
        // new data with zero risk of stale in-memory state.
        window.location.reload();
    }
</script>
