<template>
    <!--
        FU-030 — fullscreen 404 with the same warm "off-app" treatment as
        the login page (three drifting mesh-gradient blobs, floating
        mascot, glassy card). 404 can render pre-auth (typo'd URL while
        signed out) so styling is locally-scoped with forced light tokens
        — same rationale as `LoginPage.vue`, can't trust the app's
        `data-theme` cascade here.

        Uses `dorabot-fatal-error-or-offline.png` because semantically
        that's the closest "something went wrong, but it's fine" mascot.
    -->
    <div class="lost-shell" role="main">
        <div class="lost-bg" aria-hidden="true">
            <span class="lost-blob lost-blob--1" />
            <span class="lost-blob lost-blob--2" />
            <span class="lost-blob lost-blob--3" />
        </div>

        <img
            class="lost-mascot"
            src="../assets/dora/dorabot-fatal-error-or-offline.png"
            alt=""
            aria-hidden="true"
        />

        <q-card class="lost-card" flat>
            <q-card-section class="text-center lost-card-head">
                <div class="lost-code">404</div>
                <div class="lost-title" style="font-family: 'Cute Dino'">
                    This page wandered off
                </div>
                <div class="lost-sub">
                    Dora can't find what you were after — broken link, typo,
                    or something that used to live here. Head home and try
                    again from there.
                </div>
            </q-card-section>

            <q-card-section class="text-center q-pt-none">
                <q-btn
                    class="lost-submit"
                    size="lg"
                    unelevated
                    to="/"
                    label="Take me home"
                    no-caps
                />
            </q-card-section>
        </q-card>
    </div>
</template>

<script setup lang="ts"></script>

<style scoped>
    /* Mirrors `LoginPage.vue`'s locally-scoped token block. 404 can
       render pre-auth, so we deliberately ignore the app's `data-theme`
       tokens — they can flip dark before the user signs in. */
    .lost-shell {
        --lost-bg-base: #1f2647;
        --lost-blob-1: #ff7ad9;
        --lost-blob-2: #f5c462;
        --lost-blob-3: #4cd5b7;
        --lost-card-bg: rgba(255, 255, 255, 0.94);
        --lost-card-border: rgba(255, 255, 255, 0.6);
        --lost-text: #1f2330;
        --lost-text-muted: #5b6173;
        --lost-accent: #006a80;
        --lost-accent-strong: #17b073;
        --lost-shadow: 0 30px 80px -30px rgba(20, 12, 50, 0.55);

        color-scheme: light;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
        background: var(--lost-bg-base);
        color: var(--lost-text);
    }

    /* ───── Animated backdrop ─────────────────────────────────────── */
    .lost-bg {
        position: absolute;
        inset: 0;
        z-index: 0;
        overflow: hidden;
        pointer-events: none;
    }
    .lost-blob {
        position: absolute;
        width: 60vmax;
        height: 60vmax;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.75;
        mix-blend-mode: screen;
        will-change: transform;
    }
    .lost-blob--1 {
        top: -20vmax;
        left: -10vmax;
        background: var(--lost-blob-1);
        animation: lost-drift-1 22s ease-in-out infinite;
    }
    .lost-blob--2 {
        bottom: -20vmax;
        right: -10vmax;
        background: var(--lost-blob-2);
        animation: lost-drift-2 26s ease-in-out infinite;
    }
    .lost-blob--3 {
        top: 30%;
        left: 40%;
        background: var(--lost-blob-3);
        animation: lost-drift-3 30s ease-in-out infinite;
    }
    @keyframes lost-drift-1 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33%      { transform: translate(15vmax, 8vmax) scale(1.1); }
        66%      { transform: translate(-8vmax, 18vmax) scale(0.95); }
    }
    @keyframes lost-drift-2 {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33%      { transform: translate(-12vmax, -10vmax) scale(1.05); }
        66%      { transform: translate(6vmax, -16vmax) scale(1.15); }
    }
    @keyframes lost-drift-3 {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50%      { transform: translate(-30%, -70%) scale(1.2); }
    }

    /* ───── Mascot ────────────────────────────────────────────────── */
    .lost-mascot {
        position: absolute;
        top: 8%;
        right: 7%;
        width: 200px;
        height: 200px;
        object-fit: contain;
        z-index: 1;
        animation: lost-bob 6s ease-in-out infinite;
        filter: drop-shadow(0 18px 22px rgba(20, 12, 50, 0.45));
    }
    @keyframes lost-bob {
        0%, 100% { transform: translateY(0) rotate(-3deg); }
        50%      { transform: translateY(-14px) rotate(3deg); }
    }
    @media (max-width: 760px) {
        .lost-mascot {
            top: 2%;
            right: 50%;
            margin-right: -56px;
            width: 112px;
            height: 112px;
        }
    }
    @media (max-width: 360px) {
        .lost-mascot {
            margin-right: -40px;
            width: 80px;
            height: 80px;
        }
    }

    /* ───── Card ──────────────────────────────────────────────────── */
    .lost-card {
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 460px;
        padding: 12px 8px;
        border-radius: 22px;
        background: var(--lost-card-bg);
        border: 1px solid var(--lost-card-border);
        backdrop-filter: blur(18px) saturate(140%);
        -webkit-backdrop-filter: blur(18px) saturate(140%);
        box-shadow: var(--lost-shadow);
        color: var(--lost-text);
        animation: lost-card-enter 0.55s cubic-bezier(0.2, 0.9, 0.25, 1.1) both;
    }
    @keyframes lost-card-enter {
        from { opacity: 0; transform: translateY(18px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    .lost-card-head { padding-top: 28px; padding-bottom: 4px; }
    .lost-code {
        font-size: 4.5rem;
        line-height: 1;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, var(--lost-accent-strong), var(--lost-accent));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .lost-title {
        font-size: 1.7rem;
        line-height: 1.15;
        letter-spacing: 0.01em;
        margin-top: 6px;
        color: var(--lost-text);
    }
    .lost-sub {
        color: var(--lost-text-muted);
        font-size: 0.95rem;
        margin: 12px auto 0;
        max-width: 360px;
        line-height: 1.45;
    }

    .lost-submit {
        background: linear-gradient(135deg, var(--lost-accent-strong), var(--lost-accent));
        color: #fff;
        font-weight: 600;
        letter-spacing: 0.02em;
        border-radius: 12px;
        padding-left: 28px;
        padding-right: 28px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        box-shadow: 0 10px 24px -10px rgba(0, 106, 128, 0.55);
    }
    .lost-submit:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 28px -10px rgba(0, 106, 128, 0.65);
    }

    /* Respect reduced-motion — same discipline as LoginPage. */
    @media (prefers-reduced-motion: reduce) {
        .lost-blob,
        .lost-mascot,
        .lost-card { animation: none !important; }
        .lost-blob { opacity: 0.6; }
    }
</style>
