<template>
    <div class="q-gutter-md">
        <q-banner class="bg-grey-2 text-grey-8 text-caption" dense rounded>
            <template #avatar>
                <q-icon name="info" size="18px" />
            </template>
            Import stock items from a spreadsheet (.xlsx or .csv). Map your
            columns to Dora's fields, preview the result, then commit. Errors
            are reported row-by-row.
        </q-banner>

        <!-- ── File picker ────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section class="row items-center q-gutter-md">
                <q-icon name="upload_file" size="32px" class="text-primary" />
                <div>
                    <div class="text-h6">Spreadsheet import</div>
                    <div class="text-caption text-grey">
                        Required column: <strong>name</strong>. Optional:
                        level, location, group, expiry, is&nbsp;essential.
                    </div>
                </div>
            </q-card-section>
            <q-separator />
            <q-card-section>
                <q-file
                    v-model="pickedFile"
                    accept=".xlsx,.csv"
                    outlined
                    dense
                    label="Choose a .xlsx or .csv file"
                    :loading="uploading || inspecting"
                    @update:model-value="onFilePicked"
                >
                    <template #prepend>
                        <q-icon name="attach_file" />
                    </template>
                    <template #append>
                        <q-btn
                            v-if="pickedFile"
                            flat
                            dense
                            round
                            icon="close"
                            @click.stop="onClearPick"
                        />
                    </template>
                </q-file>
                <div
                    v-if="uploading && progress > 0 && progress < 1"
                    class="q-mt-sm"
                >
                    <q-linear-progress
                        :value="progress"
                        rounded
                        size="6px"
                        color="primary"
                    />
                    <div class="text-caption text-grey-7 q-mt-xs">
                        Uploading {{ Math.round(progress * 100) }}%
                    </div>
                </div>
                <div
                    v-else-if="inspecting"
                    class="text-caption text-grey-7 q-mt-sm"
                >
                    Reading spreadsheet…
                </div>
            </q-card-section>
        </q-card>

        <!-- ── Sheet selector + warnings (when more than one sheet) ── -->
        <q-card v-if="inspect && inspect.sheets.length > 1" flat bordered>
            <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Pick a sheet</div>
                <q-option-group
                    v-model="selectedSheet"
                    :options="sheetOptions"
                    color="primary"
                    inline
                />
            </q-card-section>
        </q-card>
        <q-banner
            v-if="inspect && inspect.warnings.length"
            class="bg-orange-1 text-orange-9"
            dense
            rounded
        >
            <template #avatar>
                <q-icon name="warning" />
            </template>
            <ul class="q-my-none q-pl-md">
                <li v-for="(w, i) in inspect.warnings" :key="i">{{ w }}</li>
            </ul>
        </q-banner>

        <!-- ── Column mapping + preview ──────────────────────────────── -->
        <q-card v-if="inspect && selectedSheet" flat bordered>
            <q-card-section>
                <div class="text-subtitle1">Map columns</div>
                <div class="text-caption text-grey-7 q-mb-sm">
                    Pick a spreadsheet column for each Dora field. Auto-picks
                    obvious matches based on column name.
                </div>
                <div class="row q-col-gutter-md">
                    <div
                        v-for="target in targetFields"
                        :key="target"
                        class="col-12 col-sm-6 col-md-4"
                    >
                        <q-select
                            v-model="columnMap[target]"
                            :options="columnOptions"
                            :label="targetLabel(target)"
                            outlined
                            dense
                            clearable
                            emit-value
                            map-options
                        >
                            <template #after>
                                <q-icon
                                    v-if="target === 'name' && !columnMap[target]"
                                    name="warning"
                                    color="negative"
                                    size="20px"
                                >
                                    <q-tooltip>Required</q-tooltip>
                                </q-icon>
                            </template>
                        </q-select>
                    </div>
                </div>
            </q-card-section>
            <q-separator />
            <q-card-section v-if="previewRows.length">
                <div class="text-subtitle2 q-mb-sm">Preview ({{ previewRows.length }} row{{ previewRows.length === 1 ? '' : 's' }})</div>
                <q-markup-table dense flat bordered>
                    <thead>
                        <tr>
                            <th
                                v-for="target in targetFields"
                                :key="target"
                                class="text-left"
                            >
                                {{ targetLabel(target) }}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(row, idx) in resolvedPreview" :key="idx">
                            <td
                                v-for="target in targetFields"
                                :key="target"
                                :class="row[target] === null ? 'text-grey-5' : ''"
                            >
                                {{ row[target] ?? '—' }}
                            </td>
                        </tr>
                    </tbody>
                </q-markup-table>
            </q-card-section>
            <q-separator />
            <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Options</div>
                <q-checkbox
                    v-model="options.skip_duplicates"
                    label="Skip rows whose name already exists locally"
                />
                <br />
                <q-checkbox
                    v-model="options.create_missing_locations"
                    label="Create missing locations on the fly"
                />
                <br />
                <q-checkbox
                    v-model="options.create_missing_groups"
                    label="Create missing groups on the fly"
                />
                <br />
                <q-checkbox
                    v-model="options.halt_on_error"
                    label="Halt on first error (roll back the whole import)"
                />
            </q-card-section>
            <q-separator />
            <q-card-actions align="right">
                <q-btn flat label="Cancel" @click="onClearPick" />
                <q-btn
                    color="primary"
                    icon="check"
                    label="Import"
                    :loading="committing"
                    :disable="committing || !columnMap.name"
                    @click="onCommit"
                />
            </q-card-actions>
        </q-card>

        <!-- ── Result dialog ─────────────────────────────────────────── -->
        <q-dialog v-model="resultOpen" persistent>
            <q-card style="min-width: 420px; max-width: 720px">
                <q-card-section class="row items-center q-gutter-md">
                    <q-icon
                        :name="result?.ok ? 'check_circle' : 'error'"
                        :color="result?.ok ? 'positive' : 'negative'"
                        size="32px"
                    />
                    <div>
                        <div class="text-h6">
                            {{ result?.headline ?? '' }}
                        </div>
                        <div v-if="result?.subline" class="text-caption text-grey">
                            {{ result.subline }}
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section v-if="result?.rows.length" class="q-pa-none">
                    <q-virtual-scroll
                        :items="result.rows"
                        :virtual-scroll-item-size="38"
                        style="max-height: 360px"
                        v-slot="{ item }"
                    >
                        <q-item dense>
                            <q-item-section avatar>
                                <q-chip
                                    dense
                                    size="sm"
                                    :color="rowChipColour(item.status)"
                                    text-color="white"
                                >
                                    {{ rowChipLabel(item.status) }}
                                </q-chip>
                            </q-item-section>
                            <q-item-section>
                                <q-item-label class="text-caption">
                                    Row {{ item.row_number }}: {{ item.name || '(blank)' }}
                                </q-item-label>
                                <q-item-label
                                    v-if="item.reason"
                                    caption
                                    class="text-negative"
                                >
                                    {{ item.reason }}
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-virtual-scroll>
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn
                        v-if="errorRows.length"
                        flat
                        label="Download error rows (CSV)"
                        icon="download"
                        @click="downloadErrorRows"
                    />
                    <q-btn flat label="Close" @click="onResultClose" />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import { computed, reactive, ref, watch } from 'vue';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import { useChunkedUpload } from 'src/composables/useChunkedUpload';

    const $q = useQuasar();
    const { progress, upload, abort, reset: resetUpload } = useChunkedUpload();

    // Target field labels — match the brief / server-side TARGET_FIELDS.
    const FIELD_LABELS: Record<string, string> = {
        name: 'Name (required)',
        level: 'Stock level',
        location: 'Location',
        group: 'Group',
        expiry: 'Expiry date',
        is_essential: 'Is essential',
    };
    function targetLabel(target: string): string {
        return FIELD_LABELS[target] ?? target;
    }

    interface InspectResponse {
        sheets: string[];
        preview_rows: Record<string, Array<Array<unknown>>>;
        detected_columns: Record<string, string[]>;
        auto_mapping: Record<string, Record<string, string | null>>;
        target_fields: string[];
        warnings: string[];
    }

    interface RowReport {
        row_number: number;
        status: 'created' | 'skipped_duplicate' | 'error';
        name: string;
        reason: string | null;
    }

    interface ImportResult {
        ok: boolean;
        headline: string;
        subline: string;
        rows: RowReport[];
    }

    // ── State ────────────────────────────────────────────────────────
    const pickedFile = ref<File | null>(null);
    const uploadId = ref<string | null>(null);
    const uploading = ref(false);
    const inspecting = ref(false);
    const committing = ref(false);

    const inspect = ref<InspectResponse | null>(null);
    const selectedSheet = ref<string | null>(null);
    const columnMap = reactive<Record<string, string | null>>({
        name: null, level: null, location: null,
        group: null, expiry: null, is_essential: null,
    });
    const options = reactive({
        skip_duplicates: true,
        create_missing_locations: false,
        create_missing_groups: false,
        halt_on_error: false,
    });

    const result = ref<ImportResult | null>(null);
    const resultOpen = ref(false);

    const targetFields = computed(() => inspect.value?.target_fields ?? Object.keys(FIELD_LABELS));

    const sheetOptions = computed(() => (inspect.value?.sheets ?? []).map((name) => ({
        label: name, value: name,
    })));

    const columnOptions = computed(() => {
        if (!inspect.value || !selectedSheet.value) return [];
        const cols = inspect.value.detected_columns[selectedSheet.value] ?? [];
        return cols.filter((c) => c).map((c) => ({ label: c, value: c }));
    });

    const previewRows = computed(() => {
        if (!inspect.value || !selectedSheet.value) return [];
        return inspect.value.preview_rows[selectedSheet.value] ?? [];
    });

    // Walks the preview rows through the current column map so the user can
    // see exactly which cell maps to which target.
    const resolvedPreview = computed(() => {
        if (!inspect.value || !selectedSheet.value) return [];
        const header = inspect.value.detected_columns[selectedSheet.value] ?? [];
        return previewRows.value.map((row) => {
            const out: Record<string, unknown> = {};
            for (const target of targetFields.value) {
                const colName = columnMap[target];
                if (!colName) {
                    out[target] = null;
                    continue;
                }
                const idx = header.indexOf(colName);
                out[target] = idx >= 0 && idx < row.length ? row[idx] : null;
            }
            return out;
        });
    });

    const errorRows = computed(
        () => result.value?.rows.filter((r) => r.status === 'error') ?? [],
    );

    // When inspect lands or the user picks a different sheet, snap the
    // column map to the server's auto-pick for that sheet.
    watch(selectedSheet, (sheet) => {
        if (!inspect.value || !sheet) return;
        const auto = inspect.value.auto_mapping[sheet] ?? {};
        for (const target of targetFields.value) {
            columnMap[target] = auto[target] ?? null;
        }
    });

    // ── File pick → upload → inspect ─────────────────────────────────
    async function onFilePicked(file: File | null) {
        if (!file) return;
        inspect.value = null;
        selectedSheet.value = null;
        uploading.value = true;
        try {
            const id = await upload(file);
            uploadId.value = id;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Upload failed.',
                caption: err instanceof Error ? err.message : String(err),
            });
            await onClearPick();
            return;
        } finally {
            uploading.value = false;
        }

        inspecting.value = true;
        try {
            const baseUrl = resolveBaseURL('dora');
            const response = await fetch(`${baseUrl}/data/import/spreadsheet/inspect`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: uploadId.value,
                    filename: file.name,
                }),
            });
            if (!response.ok) {
                throw new Error(await describeError(response));
            }
            inspect.value = await response.json();
            // Default to the first sheet so the mapping UI is immediately useful.
            selectedSheet.value = inspect.value?.sheets[0] ?? null;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't read that spreadsheet.",
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
        if (uploadId.value) {
            await abort(uploadId.value);
            uploadId.value = null;
        }
        resetUpload();
        pickedFile.value = null;
        inspect.value = null;
        selectedSheet.value = null;
        for (const target of Object.keys(columnMap)) {
            columnMap[target] = null;
        }
    }

    // ── Commit ───────────────────────────────────────────────────────
    async function onCommit() {
        if (!uploadId.value || !selectedSheet.value || !pickedFile.value) return;
        if (!columnMap.name) {
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                message: 'Map a column to "Name" before importing.',
            });
            return;
        }

        const confirmed = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Confirm import',
                message: `Import rows from <strong>${selectedSheet.value}</strong>?<br><br>This can't be undone.`,
                html: true,
                ok: { label: 'Import', color: 'primary' },
                cancel: { label: 'Cancel', flat: true },
            }).onOk(() => resolve(true)).onCancel(() => resolve(false));
        });
        if (!confirmed) return;

        committing.value = true;
        try {
            const baseUrl = resolveBaseURL('dora');
            const response = await fetch(`${baseUrl}/data/import/spreadsheet/commit`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    upload_id: uploadId.value,
                    filename: pickedFile.value.name,
                    sheet: selectedSheet.value,
                    column_map: { ...columnMap },
                    options: { ...options },
                }),
            });
            if (!response.ok) {
                throw new Error(await describeError(response));
            }
            const body = await response.json() as {
                summary: { created: number; skipped: number; errors: number; halted: number };
                rows: RowReport[];
            };
            const headline =
                body.summary.halted
                    ? 'Import halted'
                    : `Imported ${body.summary.created} row(s)`;
            const subline =
                `${body.summary.skipped} skipped · ${body.summary.errors} error(s)` +
                (body.summary.halted ? ' (rolled back)' : '');
            result.value = {
                ok: !body.summary.halted && body.summary.errors === 0,
                headline,
                subline,
                rows: body.rows,
            };
            resultOpen.value = true;
            // The staged file was consumed on success; forget the id so
            // a later abort doesn't 404 chasing a phantom upload.
            uploadId.value = null;
        } catch (err) {
            result.value = {
                ok: false,
                headline: 'Import failed',
                subline: err instanceof Error ? err.message : String(err),
                rows: [],
            };
            resultOpen.value = true;
        } finally {
            committing.value = false;
        }
    }

    function onResultClose() {
        resultOpen.value = false;
        // After a successful import we want a clean slate; after a failure
        // the user might want to tweak the mapping and retry, so leave
        // state in place.
        if (result.value?.ok) {
            void onClearPick();
        }
    }

    function rowChipColour(status: RowReport['status']): string {
        if (status === 'created') return 'positive';
        if (status === 'skipped_duplicate') return 'grey-7';
        return 'negative';
    }
    function rowChipLabel(status: RowReport['status']): string {
        if (status === 'created') return 'ok';
        if (status === 'skipped_duplicate') return 'dup';
        return 'err';
    }

    // Lets the user iterate on a partially-bad spreadsheet without
    // squinting at the result dialog — they fix the highlighted rows
    // offline and re-import only those.
    function downloadErrorRows() {
        const rows = errorRows.value;
        if (!rows.length) return;
        const header = ['row_number', 'name', 'reason'];
        const escape = (v: unknown) => {
            const s = v === null || v === undefined ? '' : String(v);
            // RFC4180-ish: wrap in quotes, double internal quotes.
            if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
            return s;
        };
        const lines = [header.join(',')];
        for (const r of rows) {
            lines.push([r.row_number, r.name, r.reason ?? ''].map(escape).join(','));
        }
        const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'dora-import-errors.csv';
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
    }
</script>
