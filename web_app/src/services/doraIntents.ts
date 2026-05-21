// Rule-based intent registry for the Dora help assistant.
//
// Each intent has:
//   - id: stable string used in analytics + as a quick-action key
//   - label: short text the user sees on the quick-action chip
//   - matches: list of keywords to detect the intent from free-form text
//   - handle: function returning the chat reply + optional navigation hint
//
// Page context lets us route "what can I do here?" to a per-route summary.
// Free-form user text is normalised (lowercased, stripped) and matched
// against every intent's `matches` list — first hit wins. Falls back to a
// "I'm not sure" reply that nudges toward /help or GitHub issues.
import type { DoraMood } from 'src/components/dora/doraTypes';

export type DoraIntentId =
    | 'greet'
    | 'page_help'
    | 'show_around'
    | 'whats_new'
    | 'version'
    | 'tell_me_something'
    | 'food_fact'
    | 'how_do_i'
    | 'guides'
    | 'stuck'
    | 'attention'
    | 'fallback';

export type DoraReply = {
    text: string;
    mood: DoraMood;
    // Optional follow-up suggestions rendered as chips under the reply.
    suggestions?: DoraIntentId[];
    // Optional navigation. The chat UI renders a button when present.
    navigateTo?: { path: string; label: string };
    // External link (e.g. GitHub issues). Opens in a new tab.
    externalLink?: { url: string; label: string };
};

export type DoraContext = {
    currentPath: string;
    username?: string;
    // Hooks for handlers that need async data — set up by the chat panel.
    fetchFoodFact?: () => Promise<string>;
    fetchVersion?: () => Promise<{
        current: string;
        latest: string | null;
        updateAvailable: boolean;
        releaseUrl: string | null;
    }>;
    fetchAttention?: () => Promise<{
        high: number;
        medium: number;
        low: number;
        topMessages: string[];
    }>;
};

// Short, focused summaries of what each route lets the user do. Used by the
// "What can I do on this page?" intent and as a fallback when the user
// types something page-specific without a direct intent hit.
const PAGE_HELP: { match: (path: string) => boolean; summary: string; mood: DoraMood }[] = [
    {
        match: (p) => p === '/' || p === '',
        summary:
            "This is your dashboard. It surfaces stock health, the next meals in your plan, and quick stats. Click any card to drill in.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/stock',
        summary:
            "The stock overview lists everything you're tracking. Use the search bar to filter, click an item to see its full detail (linked recipes, products and history), or use the move action to shift it between locations.",
        mood: 'curious',
    },
    {
        match: (p) => p.startsWith('/stock/'),
        summary:
            "Stock item detail. From here you can adjust stock level, link merchant products, see which recipes use this item, and check expiry.",
        mood: 'curious',
    },
    {
        match: (p) => p === '/locations',
        summary:
            "Your zones, sorted by attention score (red = needs you most). Click a zone to drill into its areas and sections. You can drag items onto a zone to move them, or use the search button to jump to anything.",
        mood: 'curious',
    },
    {
        match: (p) => p.startsWith('/locations/'),
        summary:
            "Zone detail. Areas expand to show items. The colour bands and badges call out attention reasons — expired, low stock, flagged. Drag chips between areas or use the Move button on each item.",
        mood: 'curious',
    },
    {
        match: (p) => p === '/recipes',
        summary:
            "All your recipes. Open one to see ingredients (with their locations), instructions and cook-time. Tap 'Cook' to enter step-by-step mode.",
        mood: 'happy',
    },
    {
        match: (p) => p.startsWith('/recipes/') && p.endsWith('/cook'),
        summary:
            "Cook mode. Each step is its own card. Ingredients list shows where each one lives so you can grab them quickly. Voice control works too — try it if your browser supports it.",
        mood: 'excited',
    },
    {
        match: (p) => p === '/meals',
        summary:
            "Meals bundle one or more recipes together (a roast + sides, say). Use them to plan dinners more flexibly than picking recipes directly.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/meal-plans',
        summary:
            "Plan the week ahead. Drag meals onto days, set servings, and Dora will surface what's coming up on the dashboard.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/product-search',
        summary:
            "Search for products across configured merchants (Coles, Woolworths, IGA, Aldi…). Link products to stock items so the deal price tracks alongside your pantry.",
        mood: 'curious',
    },
    {
        match: (p) => p.startsWith('/settings'),
        summary:
            "Settings. Your section covers preferences, account, locations and version info. Admins also see a Merchants page (toggle scrapers) and a Users page (manage accounts).",
        mood: 'happy',
    },
    {
        match: (p) => p === '/help',
        summary:
            "You're already here! Browse the guides by area, check the changelog for what's new, or hit me with a question.",
        mood: 'excited',
    },
];

function pageSummary(path: string): { text: string; mood: DoraMood } {
    const match = PAGE_HELP.find((p) => p.match(path));
    if (match) return { text: match.summary, mood: match.mood };
    return {
        text:
            "This page is a bit off the beaten track and I don't have a summary for it. Try the Help page for the full tour, or ask me a more specific question.",
        mood: 'confused',
    };
}

// A handful of playful one-liners. "Tell me something" cycles them — keeps
// the personality alive without being noisy. Add freely.
const FUN_REPLIES: string[] = [
    "I'm not sure if I'm a muffin or a burger today. I'll get back to you.",
    "Did you know I sometimes dream in receipts? It's mostly fine.",
    "My favourite vegetable is whichever one is on sale this week.",
    "If you stack enough mandarins, do they become a small orange? Asking for me.",
    "I tried to count the sprinkles on a donut once. Lost interest at sprinkle 14.",
    "I think tomatoes are confused. They're trying their best.",
    "Sometimes I imagine I'm a sentient avocado. The pit is my secret.",
    "I once met a recipe that knew where it was going. I admired that.",
];
let funCursor = 0;
function nextFunReply(): string {
    const reply = FUN_REPLIES[funCursor % FUN_REPLIES.length]!;
    funCursor++;
    return reply;
}

// Each registered intent. `matches` is keyword-based — case-insensitive and
// whole-word-free (substring). Order matters: more specific intents come
// first so generic words ("help") don't shadow them.
export const INTENTS: ReadonlyArray<{
    id: DoraIntentId;
    label: string;
    matches: string[];
    requiresPath?: (path: string) => boolean;
}> = [
    { id: 'greet', label: 'Hi Dora!', matches: ['hi', 'hello', 'hey', 'yo dora'] },
    {
        id: 'page_help',
        label: 'What can I do on this page?',
        matches: ['this page', 'what page', "where am i", 'what can i do here', 'what is this'],
    },
    {
        id: 'whats_new',
        label: "What's new?",
        matches: ['new', 'changelog', 'release', 'updated', 'recent'],
    },
    {
        id: 'version',
        label: 'What version are you?',
        matches: ['version', 'build'],
    },
    {
        id: 'food_fact',
        label: 'Random food fact',
        matches: ['fact', 'food fact', 'trivia', 'random'],
    },
    {
        id: 'tell_me_something',
        label: 'Tell me something',
        matches: ['tell me', 'something', 'joke', 'fun', 'bored'],
    },
    {
        id: 'guides',
        label: 'Open the guides',
        matches: ['guide', 'guides', 'docs', 'documentation', 'manual'],
    },
    {
        id: 'stuck',
        label: "I'm stuck",
        matches: ['stuck', 'lost', 'confused', 'help me', "don't know", 'how do i start'],
    },
    {
        id: 'how_do_i',
        label: 'How do I...?',
        matches: ['how do i', 'how can i', 'how to'],
    },
    {
        id: 'attention',
        label: 'What needs my attention?',
        matches: ['attention', 'todo', 'to do', 'needs', 'alerts', 'urgent', 'expired', 'expiring'],
    },
];

export const QUICK_ACTIONS: DoraIntentId[] = [
    'attention',
    'page_help',
    'whats_new',
    'tell_me_something',
    'food_fact',
    'guides',
    'stuck',
];

function intentLabel(id: DoraIntentId): string {
    return INTENTS.find((i) => i.id === id)?.label ?? id;
}

export function labelFor(id: DoraIntentId): string {
    return intentLabel(id);
}

export function detectIntent(text: string): DoraIntentId {
    const lower = text.toLowerCase().trim();
    if (!lower) return 'greet';
    for (const intent of INTENTS) {
        if (intent.matches.some((m) => lower.includes(m))) return intent.id;
    }
    return 'fallback';
}

export async function runIntent(
    id: DoraIntentId,
    context: DoraContext,
): Promise<DoraReply> {
    switch (id) {
        case 'greet': {
            const name = context.username ? `, ${context.username}` : '';
            return {
                text: `Hi${name}! I'm Dora. I can show you around, summarise the page you're on, share what's new, or just tell you something silly. What's up?`,
                mood: 'happy',
                suggestions: ['page_help', 'whats_new', 'tell_me_something', 'stuck'],
            };
        }
        case 'page_help': {
            const summary = pageSummary(context.currentPath);
            return {
                text: summary.text,
                mood: summary.mood,
                suggestions: ['guides', 'how_do_i', 'whats_new'],
            };
        }
        case 'show_around': {
            return {
                text:
                    "Here's the tour: Dashboard is home. Stock is your pantry. Locations is where things live (drag stuff between zones). Recipes and Meals plan what you'll cook. Product Search pulls live deals. Settings holds your preferences (and admin tools if you're an admin).",
                mood: 'excited',
                suggestions: ['guides', 'page_help'],
            };
        }
        case 'whats_new': {
            const versionInfo = context.fetchVersion ? await context.fetchVersion() : null;
            const updateBit = versionInfo?.updateAvailable
                ? ` There's also a newer version (${versionInfo.latest}) available — want to see the release notes?`
                : '';
            return {
                text:
                    `You're on Discount Dora ${versionInfo?.current ?? 'an unknown version'}. Open the Help page to read the full changelog — recent highlights include the Dora assistant (that's me!), the hierarchical locations heatmap, and per-user preferences.${updateBit}`,
                mood: 'excited',
                navigateTo: { path: '/help', label: 'Open Help (changelog tab)' },
                ...(versionInfo?.updateAvailable && versionInfo.releaseUrl
                    ? { externalLink: { url: versionInfo.releaseUrl, label: 'See latest release on GitHub' } }
                    : {}),
            };
        }
        case 'version': {
            const info = context.fetchVersion ? await context.fetchVersion() : null;
            if (!info) {
                return {
                    text: "I couldn't reach the version endpoint. Try again in a moment.",
                    mood: 'confused',
                };
            }
            const updateLine = info.updateAvailable
                ? ` A newer version (${info.latest}) is available!`
                : info.latest
                  ? " You're on the latest."
                  : '';
            return {
                text: `I'm Discount Dora ${info.current}.${updateLine}`,
                mood: info.updateAvailable ? 'excited' : 'happy',
                ...(info.updateAvailable && info.releaseUrl
                    ? { externalLink: { url: info.releaseUrl, label: 'See release notes' } }
                    : {}),
            };
        }
        case 'tell_me_something': {
            return {
                text: nextFunReply(),
                mood: 'excited',
                suggestions: ['tell_me_something', 'food_fact'],
            };
        }
        case 'food_fact': {
            const fact = context.fetchFoodFact ? await context.fetchFoodFact() : null;
            if (!fact) {
                return {
                    text:
                        "I couldn't grab a fresh food fact. But did you know honey never spoils? That's free.",
                    mood: 'happy',
                };
            }
            return {
                text: fact,
                mood: 'curious',
                suggestions: ['food_fact', 'tell_me_something'],
            };
        }
        case 'guides': {
            return {
                text:
                    "The guides live on the Help page — categorised by area (stock, locations, recipes, shopping, admin). Want me to take you there?",
                mood: 'curious',
                navigateTo: { path: '/help', label: 'Open the guides' },
            };
        }
        case 'stuck': {
            return {
                text:
                    "No worries — being lost is the start of learning! Here's the plan: open the Help page for guided how-tos by area, or tell me what you're trying to do (e.g. 'add a stock item' or 'plan a meal') and I'll point you at the right page.",
                mood: 'happy',
                navigateTo: { path: '/help', label: "Take me to the guides" },
                suggestions: ['show_around', 'how_do_i'],
            };
        }
        case 'how_do_i': {
            return {
                text:
                    "Tell me what you're trying to do (in plain English — \"add a stock item\", \"plan dinner\", \"reset a password\") and I'll point you at the right page. Or open the guides for the full how-to list.",
                mood: 'curious',
                navigateTo: { path: '/help', label: 'Browse guides by area' },
            };
        }
        case 'attention': {
            const info = context.fetchAttention ? await context.fetchAttention() : null;
            if (!info) {
                return {
                    text:
                        "I couldn't reach the alerts service. Try the bell icon in the header.",
                    mood: 'confused',
                };
            }
            const total = info.high + info.medium + info.low;
            if (total === 0) {
                return {
                    text:
                        "All quiet! Nothing needs your attention right now — your pantry is in good shape.",
                    mood: 'happy',
                    suggestions: ['page_help', 'tell_me_something'],
                };
            }
            const breakdown = [
                info.high ? `${info.high} high` : null,
                info.medium ? `${info.medium} medium` : null,
                info.low ? `${info.low} low` : null,
            ]
                .filter(Boolean)
                .join(' · ');
            const sample = info.topMessages.slice(0, 3).map((m) => `• ${m}`).join('\n');
            return {
                text: `${total} thing${total === 1 ? '' : 's'} need attention right now (${breakdown}).\n\n${sample}\n\nOpen the bell in the header for the full list and inline actions.`,
                mood: info.high > 0 ? 'confused' : 'curious',
                navigateTo: { path: '/stock', label: 'See it on the Stock page' },
            };
        }
        case 'fallback':
        default: {
            return {
                text:
                    "I'm not sure I understood that one. Try a quick action below, or open the Help page for the full guides. If something's broken, the GitHub issues page is the right place.",
                mood: 'confused',
                navigateTo: { path: '/help', label: 'Open Help' },
                externalLink: {
                    url: 'https://github.com/BenTalese/DiscountDora/issues/new',
                    label: 'Report an issue on GitHub',
                },
                suggestions: ['stuck', 'guides'],
            };
        }
    }
}
