<template>
    <q-card flat bordered class="dora-chat-card column" style="width: 360px">
        <q-card-section class="row items-center q-pb-sm dora-chat-header">
            <DoraMascot :mood="latestMood" :size="40" />
            <div class="q-ml-md col">
                <div class="row items-center no-wrap">
                    <span class="text-weight-medium">Dora</span>
                    <q-chip
                        v-if="aiActive !== null"
                        dense
                        size="sm"
                        class="q-ml-sm dora-mode-chip"
                        :icon="aiActive ? 'auto_awesome' : 'chat_bubble_outline'"
                        :color="aiActive ? 'primary' : 'grey-4'"
                        :text-color="aiActive ? 'white' : 'grey-9'"
                    >
                        {{ aiActive ? 'AI' : 'Basic' }}
                        <q-tooltip>
                            {{ aiActive
                                ? 'AI mode: powered by your connected language model.'
                                : 'Basic mode: built-in rule-based replies. An admin can enable AI in Settings → System.' }}
                        </q-tooltip>
                    </q-chip>
                </div>
                <div class="text-caption text-grey">
                    Your in-app helper. {{ pageHintForHeader }}
                </div>
            </div>
            <q-btn flat round dense icon="close" @click="emit('close')" />
        </q-card-section>

        <q-separator />

        <div ref="messagesEl" class="dora-chat-messages col">
            <div
                v-for="(message, idx) in messages"
                :key="idx"
                class="dora-chat-message"
                :class="`dora-chat-message-${message.from}`"
            >
                <div class="dora-chat-bubble">
                    <div class="dora-chat-text">{{ message.text }}</div>
                    <div
                        v-if="message.navigateTo || message.externalLink"
                        class="dora-chat-actions q-mt-xs"
                    >
                        <q-btn
                            v-if="message.navigateTo"
                            size="sm"
                            no-caps
                            color="primary"
                            unelevated
                            :icon-right="iconForNav(message.navigateTo.path)"
                            :label="message.navigateTo.label"
                            @click="onNavigate(message.navigateTo.path)"
                        />
                        <q-btn
                            v-if="message.externalLink"
                            size="sm"
                            no-caps
                            outline
                            color="primary"
                            icon-right="open_in_new"
                            :label="message.externalLink.label"
                            class="q-ml-xs"
                            type="a"
                            :href="message.externalLink.url"
                            target="_blank"
                            rel="noopener"
                        />
                    </div>
                    <div
                        v-if="message.suggestions && message.suggestions.length > 0"
                        class="row q-gutter-xs q-mt-sm"
                    >
                        <q-chip
                            v-for="suggestion in message.suggestions"
                            :key="suggestion"
                            dense
                            clickable
                            color="grey-2"
                            text-color="grey-10"
                            @click="onIntentClick(suggestion)"
                        >
                            {{ labelFor(suggestion) }}
                        </q-chip>
                    </div>

                    <div
                        v-if="message.action && !message.action.no_primary"
                        class="dora-action-card q-mt-sm"
                    >
                        <div
                            v-for="(item, itemIdx) in message.action.items"
                            :key="itemIdx"
                            class="dora-action-item"
                        >
                            <div class="text-caption text-weight-medium">
                                <q-icon
                                    :name="itemIcon(item.status, message, itemIdx)"
                                    :color="itemIconColor(item.status, message, itemIdx)"
                                    size="16px"
                                    class="q-mr-xs"
                                />
                                <template v-if="item.status === 'ready'">
                                    {{ qtyLabel(item.quantity) }}{{ item.candidates[0]?.name }}
                                </template>
                                <template v-else-if="item.status === 'not_found'">
                                    Couldn't find “{{ item.query }}”
                                </template>
                                <template v-else-if="item.status === 'too_many'">
                                    Too many matches for “{{ item.query }}” — be more specific
                                </template>
                                <template v-else>
                                    Which “{{ item.query }}”?
                                </template>
                            </div>
                            <div
                                v-if="item.status === 'ambiguous' && !message.done"
                                class="row q-gutter-xs q-mt-xs"
                            >
                                <q-chip
                                    v-for="candidate in item.candidates"
                                    :key="candidate.stock_item_id"
                                    dense
                                    clickable
                                    :outline="message.selections?.[itemIdx] !== candidate.stock_item_id"
                                    color="primary"
                                    @click="selectCandidate(message, itemIdx, candidate.stock_item_id)"
                                >
                                    {{ candidate.name
                                    }}<span v-if="candidate.location"> · {{ candidate.location }}</span>
                                </q-chip>
                            </div>
                        </div>
                        <q-btn
                            v-if="!message.done"
                            size="sm"
                            no-caps
                            unelevated
                            color="primary"
                            icon-right="add_shopping_cart"
                            class="q-mt-sm"
                            :label="`Add to ${message.action.shopping_list?.name ?? 'list'}`"
                            :disable="!canCommit(message)"
                            @click="commitAction(message)"
                        />
                    </div>
                </div>
            </div>

            <div v-if="thinking" class="dora-chat-message dora-chat-message-dora">
                <div class="dora-chat-bubble dora-chat-thinking">
                    <q-spinner-dots size="20px" color="primary" />
                </div>
            </div>
        </div>

        <q-separator />

        <q-card-section class="q-py-sm">
            <div class="row q-gutter-xs q-mb-sm">
                <q-chip
                    v-for="action in quickActions"
                    :key="action"
                    dense
                    clickable
                    outline
                    color="primary"
                    @click="onIntentClick(action)"
                >
                    {{ labelFor(action) }}
                </q-chip>
            </div>

            <q-input
                v-model="draft"
                placeholder="Ask Dora anything…"
                outlined
                dense
                autogrow
                @keydown.enter.prevent="onSubmit"
            >
                <template #append>
                    <q-btn
                        flat
                        round
                        dense
                        icon="send"
                        :disable="!draft.trim()"
                        @click="onSubmit"
                    />
                </template>
            </q-input>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import type { DoraMood } from 'src/components/dora/doraTypes';
    import type { AuthenticatedUser } from 'src/models/auth';
    import AlertApiService from 'src/services/api/alertApiService';
    import AssistantApiService, {
        type CommitAddItem,
        type PendingAction,
    } from 'src/services/api/assistantApiService';
    import HelpApiService from 'src/services/api/helpApiService';
    import {
        QUICK_ACTIONS,
        detectIntent,
        labelFor,
        runIntent,
        type DoraContext,
        type DoraIntentId
    } from 'src/services/doraIntents';
    import { computed, nextTick, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    type Message = {
        from: 'user' | 'dora';
        text: string;
        mood?: DoraMood;
        navigateTo?: { path: string; label: string };
        externalLink?: { url: string; label: string };
        suggestions?: DoraIntentId[];
        // Proposed shopping-list addition awaiting the user's confirmation /
        // disambiguation. `selections` maps an ambiguous item index to the
        // chosen candidate id; `done` disables the card after committing.
        action?: PendingAction;
        selections?: Record<number, string>;
        done?: boolean;
    };

    const props = defineProps<{ currentUser: AuthenticatedUser | null }>();
    const emit = defineEmits<{ (e: 'close'): void }>();

    const route = useRoute();
    const router = useRouter();
    const helpApi = new HelpApiService();
    const alertApi = new AlertApiService();
    const assistantApi = new AssistantApiService();

    const messages = ref<Message[]>([]);
    const draft = ref('');
    const thinking = ref(false);
    const messagesEl = ref<HTMLElement | null>(null);
    const quickActions = QUICK_ACTIONS;
    // Whether the assistant is running on AI vs the rule-based fallback.
    // null = not yet known (hides the badge until the first status check).
    const aiActive = ref<boolean | null>(null);

    // Latest mood drives the header mascot face. Falls back to 'happy' so
    // first paint has a stable expression.
    const latestMood = computed<DoraMood>(() => {
        for (let i = messages.value.length - 1; i >= 0; i--) {
            const m = messages.value[i];
            if (m?.from === 'dora' && m.mood) return m.mood;
        }
        return 'happy';
    });

    const pageHintForHeader = computed(() => {
        const p = route.path;
        if (p === '/' || p === '') return 'Dashboard view.';
        const segment = p.split('/').filter(Boolean)[0];
        if (!segment) return '';
        return `${segment.replace(/-/g, ' ').replace(/^\w/, (c) => c.toUpperCase())} view.`;
    });

    function iconForNav(path: string): string {
        if (path === '/help') return 'help';
        if (path.startsWith('/stock')) return 'inventory_2';
        if (path.startsWith('/locations')) return 'place';
        if (path.startsWith('/recipes')) return 'menu_book';
        return 'arrow_forward';
    }

    function context(): DoraContext {
        return {
            currentPath: route.path,
            username: props.currentUser?.username,
            fetchFoodFact: async () => (await helpApi.getFoodFactAsync()).fact,
            fetchVersion: async () => {
                const v = await helpApi.getVersionAsync();
                return {
                    current: v.current_version,
                    latest: v.latest_version,
                    updateAvailable: v.update_available,
                    releaseUrl: v.release_url,
                };
            },
            fetchAttention: async () => {
                const a = await alertApi.getAlertsAsync();
                return {
                    high: a.high_count,
                    medium: a.medium_count,
                    low: a.low_count,
                    topMessages: a.items.slice(0, 3).map((alert) => alert.message),
                };
            },
        };
    }

    async function scrollToBottom() {
        await nextTick();
        const el = messagesEl.value;
        if (el) el.scrollTop = el.scrollHeight;
    }

    function pushDoraMessage(reply: Awaited<ReturnType<typeof runIntent>>) {
        messages.value.push({
            from: 'dora',
            text: reply.text,
            mood: reply.mood,
            navigateTo: reply.navigateTo,
            externalLink: reply.externalLink,
            suggestions: reply.suggestions,
        });
    }

    function qtyLabel(quantity: number | null): string {
        return quantity !== null ? `${quantity} ` : '';
    }

    function isResolved(message: Message, itemIdx: number): boolean {
        const item = message.action?.items[itemIdx];
        if (!item) return false;
        if (item.status === 'ready') return true;
        if (item.status === 'ambiguous') return Boolean(message.selections?.[itemIdx]);
        return false;
    }

    function itemIcon(status: string, message: Message, itemIdx: number): string {
        if (status === 'ready' || isResolved(message, itemIdx)) return 'check_circle';
        if (status === 'not_found' || status === 'too_many') return 'cancel';
        return 'help';
    }

    function itemIconColor(status: string, message: Message, itemIdx: number): string {
        if (status === 'ready' || isResolved(message, itemIdx)) return 'positive';
        if (status === 'not_found' || status === 'too_many') return 'negative';
        return 'warning';
    }

    function selectCandidate(message: Message, itemIdx: number, stockItemId: string) {
        if (!message.selections) message.selections = {};
        message.selections[itemIdx] = stockItemId;
    }

    // Build the concrete (stock_item_id, quantity) list to commit: ready items
    // use their sole match; ambiguous items use the user's pick. Not-found and
    // too-many items are silently dropped.
    function commitItems(message: Message): CommitAddItem[] {
        const action = message.action;
        if (!action) return [];
        const out: CommitAddItem[] = [];
        action.items.forEach((item, idx) => {
            if (item.status === 'ready' && item.candidates[0]) {
                out.push({ stock_item_id: item.candidates[0].stock_item_id, quantity: item.quantity });
            } else if (item.status === 'ambiguous') {
                const chosen = message.selections?.[idx];
                if (chosen) out.push({ stock_item_id: chosen, quantity: item.quantity });
            }
        });
        return out;
    }

    // Enabled only when there's a target list, something to add, and every
    // ambiguous item has been resolved (so we never commit a half-answered prompt).
    function canCommit(message: Message): boolean {
        const action = message.action;
        if (!action || !action.shopping_list || message.done) return false;
        const everyAmbiguousResolved = action.items.every(
            (item, idx) => item.status !== 'ambiguous' || Boolean(message.selections?.[idx]),
        );
        return everyAmbiguousResolved && commitItems(message).length > 0;
    }

    async function commitAction(message: Message) {
        const action = message.action;
        if (!action?.shopping_list || !canCommit(message)) return;
        const items = commitItems(message);
        message.done = true;
        thinking.value = true;
        await scrollToBottom();
        try {
            const result = await assistantApi.actAsync(action.shopping_list.id, items);
            pushDoraMessage({ text: result.answer, mood: 'happy' });
        } catch (err) {
            message.done = false;
            pushDoraMessage({
                text: `I couldn't update the list — ${String(err)}`,
                mood: 'confused',
            });
        } finally {
            thinking.value = false;
            await scrollToBottom();
        }
    }

    async function dispatch(intent: DoraIntentId, userText?: string) {
        if (userText) {
            messages.value.push({ from: 'user', text: userText });
            await scrollToBottom();
        }
        thinking.value = true;
        await scrollToBottom();
        try {
            // Small delay so the spinner registers visually even on instant
            // responses — keeps the "I'm thinking" affordance honest.
            const [reply] = await Promise.all([
                runIntent(intent, context()),
                new Promise((r) => setTimeout(r, 220)),
            ]);
            pushDoraMessage(reply);
        } catch (err) {
            pushDoraMessage({
                text: `Something went wrong while answering — ${String(err)}`,
                mood: 'confused',
            });
        } finally {
            thinking.value = false;
            await scrollToBottom();
        }
    }

    function onIntentClick(id: DoraIntentId) {
        void dispatch(id, labelFor(id));
    }

    // Free-form text goes to the SLM assistant first. The backend tells us
    // when it can't help — model unreachable (`available: false`) or the
    // message wasn't a data question (`defer_to_local: true`) — and in both
    // cases we fall back to the local rule-based intents so the assistant
    // keeps working with or without a model running.
    async function onSubmit() {
        const text = draft.value.trim();
        if (!text) return;
        draft.value = '';
        messages.value.push({ from: 'user', text });
        await scrollToBottom();
        thinking.value = true;
        await scrollToBottom();
        try {
            const reply = await assistantApi.askAsync(text, route.path);
            // Keep the AI/Basic badge honest with the latest real outcome.
            aiActive.value = reply.available;
            if (reply.available && !reply.defer_to_local && reply.answer) {
                messages.value.push({
                    from: 'dora',
                    text: reply.answer,
                    mood: (reply.mood as DoraMood) ?? 'happy',
                    ...(reply.navigate_to ? { navigateTo: reply.navigate_to } : {}),
                    ...(reply.pending_action
                        ? { action: reply.pending_action, selections: {} }
                        : {}),
                });
                await scrollToBottom();
                return;
            }
        } catch (err) {
            // Network/parse failure — degrade silently to the rule engine.
            aiActive.value = false;
            console.debug('Assistant backend unavailable, using local intents', err);
        } finally {
            thinking.value = false;
            await scrollToBottom();
        }
        const intent = detectIntent(text);
        await dispatch(intent);
    }

    function onNavigate(path: string) {
        void router.push(path);
        emit('close');
    }

    onMounted(() => {
        void dispatch('greet');
        // Show the AI/Basic badge from the start, before the first message.
        void assistantApi
            .getStatusAsync()
            .then((s) => {
                aiActive.value = s.ai_available;
            })
            .catch(() => {
                aiActive.value = false;
            });
    });

    // Re-summarise the page when the user navigates while the chat is open
    // so the header hint stays accurate. We don't auto-post a new message
    // (that would be noisy) — just update the header.
    watch(
        () => route.path,
        () => {
            void scrollToBottom();
        }
    );
</script>

<style scoped>
    .dora-chat-card {
        /* The card is a flex column. The messages region uses flex: 1 so
           it grows to fill whatever room is left after the (fixed-height)
           header and input footer, then scrolls internally. Without this,
           a long thread pushes the footer off-screen because the
           combined fixed sizes exceed the viewport. */
        max-height: 70vh;
        height: 70vh;
        background: white;
    }
    .body--dark .dora-chat-card {
        background: var(--q-component);
    }
    .dora-chat-header {
        background: linear-gradient(
            120deg,
            rgba(23, 176, 115, 0.08),
            rgba(254, 210, 36, 0.08)
        );
    }
    .dora-chat-messages {
        overflow-y: auto;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        /* `flex: 1` + a zero `min-height` is the documented incantation
           for "fill remaining flex space, allow overflow to scroll".
           Setting min-height: 0 is the key — without it Chrome refuses
           to shrink the box below content size, which pushes the footer
           out of view after a few replies. */
        flex: 1 1 0;
        min-height: 0;
    }
    .dora-chat-message {
        display: flex;
    }
    .dora-chat-message-user {
        justify-content: flex-end;
    }
    .dora-chat-bubble {
        max-width: 80%;
        padding: 8px 12px;
        border-radius: 12px;
        background: rgba(0, 0, 0, 0.05);
        font-size: 0.92em;
        line-height: 1.35;
    }
    .dora-chat-message-user .dora-chat-bubble {
        background: var(--q-primary);
        color: white;
    }
    .dora-chat-message-user .dora-chat-bubble .dora-chat-text {
        color: white;
    }
    .dora-chat-thinking {
        background: rgba(0, 0, 0, 0.03);
    }
    .dora-chat-text {
        white-space: pre-wrap;
    }
    .dora-action-card {
        border-top: 1px solid rgba(0, 0, 0, 0.08);
        padding-top: 8px;
    }
    .dora-action-item + .dora-action-item {
        margin-top: 6px;
    }
</style>
