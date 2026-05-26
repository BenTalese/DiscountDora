<template>
    <div class="data-shell q-pa-md">
        <q-breadcrumbs class="q-mb-sm" active-color="grey-9">
            <q-breadcrumbs-el label="Data" icon="storage" />
            <q-breadcrumbs-el :label="activeLabel" />
        </q-breadcrumbs>

        <div class="row items-center q-mb-md">
            <div class="text-caption text-grey">
                Backup, import, export and barcode tools for your Dora data.
            </div>
        </div>

        <div class="row q-col-gutter-md">
            <!-- Side nav ──────────────────────────────────────────────── -->
            <aside class="col-12 col-md-3">
                <q-card flat bordered>
                    <q-list>
                        <q-item-label header class="data-group-header">
                            Data tools
                        </q-item-label>
                        <q-item
                            v-for="section in sections"
                            :key="section.path"
                            clickable
                            :to="section.path"
                            active-class="data-section-active"
                            exact
                        >
                            <q-item-section avatar>
                                <q-icon :name="section.icon" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ section.label }}</q-item-label>
                                <q-item-label caption>{{ section.caption }}</q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card>
            </aside>

            <!-- Active section ─────────────────────────────────────────── -->
            <main class="col-12 col-md-9">
                <router-view />
            </main>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';
    import { useRoute } from 'vue-router';

    type Section = { path: string; label: string; caption: string; icon: string };

    const sections: Section[] = [
        {
            path: '/data/backup',
            label: 'Backup & restore',
            caption: 'Export everything to JSON; restore on demand',
            icon: 'cloud_download'
        },
        {
            path: '/data/import',
            label: 'Import',
            caption: 'Bring in stock, recipes, or shopping lists',
            icon: 'file_upload'
        },
        {
            path: '/data/export',
            label: 'Export & print',
            caption: 'Printable views and CSV exports',
            icon: 'print'
        },
        {
            path: '/data/barcodes',
            label: 'Barcodes & QR',
            caption: 'Generate item QR codes; register product barcodes',
            icon: 'qr_code_2'
        }
    ];

    const route = useRoute();
    const activeLabel = computed(() => {
        const match = sections.find((s) => route.path.startsWith(s.path));
        return match ? match.label : '';
    });
</script>

<style scoped>
    .data-section-active {
        background: var(--brand-primary-soft);
        font-weight: 600;
    }
    .data-group-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        padding-top: 12px;
    }
</style>
