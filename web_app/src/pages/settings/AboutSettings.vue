<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-gutter-md">
            <q-avatar size="56px" square>
                <img src="../../assets/logo-mascot.png" alt="Discount Dora" />
            </q-avatar>
            <div>
                <div class="text-h6" style="font-family: 'Cute Dino'">Discount Dora</div>
                <div class="text-caption text-grey">Your pantry at your fingertips.</div>
            </div>
        </q-card-section>

        <q-separator />

        <q-card-section>
            <q-list separator>
                <q-item>
                    <q-item-section>
                        <q-item-label>Build</q-item-label>
                        <q-item-label caption>
                            Local development. Versioning isn't tagged in this fork yet.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-chip dense color="grey-3" text-color="grey-9">{{ buildLabel }}</q-chip>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Install as an app</q-item-label>
                        <q-item-label caption>
                            Adds a Dora icon to your home screen / launcher
                            and runs in its own window. iOS Safari uses
                            "Add to Home Screen" instead.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <PwaInstallPrompt />
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Web client</q-item-label>
                        <q-item-label caption>
                            Quasar 2 / Vue 3, talks to two Flask APIs over CORS.
                        </q-item-label>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Dora API endpoint</q-item-label>
                        <q-item-label caption class="text-mono">{{ doraApiUrl }}</q-item-label>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Merchant API endpoint</q-item-label>
                        <q-item-label caption class="text-mono">{{ merchantApiUrl }}</q-item-label>
                    </q-item-section>
                </q-item>

                <q-item
                    clickable
                    tag="a"
                    href="https://github.com/BenTalese/DiscountDora"
                    target="_blank"
                    rel="noopener"
                >
                    <q-item-section avatar>
                        <q-icon name="open_in_new" />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label>Project repository</q-item-label>
                        <q-item-label caption>GitHub · BenTalese/DiscountDora</q-item-label>
                    </q-item-section>
                </q-item>

                <q-item
                    clickable
                    tag="a"
                    href="https://github.com/BenTalese/DiscountDora/issues/new"
                    target="_blank"
                    rel="noopener"
                >
                    <q-item-section avatar>
                        <q-icon name="bug_report" />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label>Report a bug</q-item-label>
                        <q-item-label caption>Opens a new issue on GitHub.</q-item-label>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card-section>

        <q-separator />

        <q-card-section class="text-caption text-grey">
            Dora is a hobby project. The mascot is doing its best.
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import PwaInstallPrompt from 'src/components/PwaInstallPrompt.vue';
    import { computed } from 'vue';

    // Reflects what AxiosHttpClient will actually use — keeps this section
    // honest for debugging deployments.
    const doraApiUrl = computed(() => {
        const env = import.meta.env.VITE_API_BASE_URL;
        if (env) return env;
        if (typeof window !== 'undefined') {
            const { protocol, hostname } = window.location;
            return `${protocol}//${hostname}:5170/api`;
        }
        return 'http://localhost:5170/api';
    });

    const merchantApiUrl = computed(() => {
        const env = import.meta.env.VITE_MERCHANT_API_BASE_URL;
        if (env) return env;
        if (typeof window !== 'undefined') {
            const { protocol, hostname } = window.location;
            return `${protocol}//${hostname}:5172/api`;
        }
        return 'http://localhost:5172/api';
    });

    const buildLabel = computed(() => (import.meta.env.PROD ? 'production' : 'dev'));
</script>

<style scoped>
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
</style>
