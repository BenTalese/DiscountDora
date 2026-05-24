// Rule-based intent registry for the Dora help assistant — "Basic mode".
//
// Always-on baseline. The AI assistant runs alongside when configured, but
// every reply here should still feel like Dora: playful, cheeky, wholesome,
// loving life, mildly chaotic. Self-deprecating burger-bot lore is the
// house style; Aussie casual is the default tone.
//
// Each intent has:
//   - id: stable string used in analytics + as a quick-action key
//   - label: short text the user sees on the quick-action chip
//   - matches: list of keywords to detect the intent from free-form text
//   - handle: function returning the chat reply + optional navigation hint
//
// Free-form user text is normalised (lowercased, stripped) and matched
// against every intent's `matches` list — first hit wins, so ORDER MATTERS:
// narrower intents must come before broader ones (e.g. `convert` before
// `find_recipe`, since both could contain food words).
import type { DoraMood } from 'src/components/dora/doraTypes';

export type DoraIntentId =
    | 'greet'
    | 'goodbye'
    | 'page_help'
    | 'show_around'
    | 'whats_new'
    | 'version'
    | 'tell_me_something'
    | 'food_fact'
    | 'joke'
    | 'how_do_i'
    | 'guides'
    | 'stuck'
    | 'attention'
    | 'pantry_summary'
    | 'low_stock'
    | 'expiring'
    | 'where_is'
    | 'find_recipe'
    | 'whats_for_dinner'
    | 'shopping_list_status'
    | 'weeks_meals'
    | 'convert'
    | 'substitute'
    | 'compliment'
    | 'insult'
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

// ── Data shapes the chat panel feeds in via DoraContext ────────────────
// Kept as flat snapshots, not live store refs, so the intent handlers stay
// pure(-ish) and easy to test. The chat builds these from the existing
// Pinia stores at call time.

export type StockSnapshotItem = {
    id: string;
    name: string;
    levelName: string | null;       // "Sufficient" / "Low Stock" / "Out of Stock" / null
    levelSequence: number | null;   // higher = less stock; null when unknown
    locationName: string | null;
    expiryDate: string | null;      // ISO yyyy-mm-dd
    isFlagged: boolean;
    isOpen: boolean;
};

export type RecipeSnapshot = {
    id: string;
    name: string;
    cuisine: string | null;
    category: string | null;
    cookTimeMinutes: number | null;
    isFavourite: boolean;
    ingredientStockItemIds: string[];
};

export type ShoppingListSnapshot = {
    id: string;
    name: string;
    itemCount: number;
    isPrimary: boolean;
};

export type MealPlanSnapshot = {
    startDate: string;
    endDate: string;
    upcomingMealNames: string[]; // next few days
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
    // Local-data accessors — synchronous reads off the Pinia stores. Empty
    // arrays / nulls are fine; intent handlers degrade gracefully when the
    // store hasn't loaded yet.
    getStock?: () => StockSnapshotItem[];
    getRecipes?: () => RecipeSnapshot[];
    getShoppingLists?: () => ShoppingListSnapshot[];
    getMealPlan?: () => MealPlanSnapshot | null;
};

// ── Shared reply-bank cursor ───────────────────────────────────────────
// One cursor across every bank so repeated similar prompts don't loop back
// to the same line. Module-level state is fine; this lives for the page
// session.
let bankCursor = 0;
function pick(bank: readonly string[]): string {
    const value = bank[bankCursor % bank.length]!;
    bankCursor++;
    return value;
}

// ── Page summaries — used by `page_help` ───────────────────────────────
const PAGE_HELP: { match: (path: string) => boolean; summary: string; mood: DoraMood }[] = [
    {
        match: (p) => p === '/' || p === '',
        summary:
            "You're on the dashboard — pantry health, the next meals up, the bits that need a poke. Click any card to dive in.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/stock',
        summary:
            "Pantry HQ. Filter with the search bar, click an item to see everything I know about it, or use the move button to shuffle things between locations.",
        mood: 'searching',
    },
    {
        match: (p) => p.startsWith('/stock/'),
        summary:
            "Stock item detail. Adjust the level, link merchant products, peek at the recipes that use it, check expiry. Basically everything that item-shaped.",
        mood: 'searching',
    },
    {
        match: (p) => p === '/locations',
        summary:
            "Zones, sorted by attention score — red means 'oi, look here'. Drag items between zones, or hit search to teleport.",
        mood: 'searching',
    },
    {
        match: (p) => p.startsWith('/locations/'),
        summary:
            "Zone detail. Areas expand into sections; badges shout if something's expired, low, or flagged. Drag chips around or use the Move button on each item.",
        mood: 'searching',
    },
    {
        match: (p) => p === '/recipes',
        summary:
            "All your recipes. Open one to see ingredients (with their pantry homes), instructions, and cook time. Hit 'Cook' for step-by-step mode.",
        mood: 'happy',
    },
    {
        match: (p) => p.startsWith('/recipes/') && p.endsWith('/cook'),
        summary:
            "Cook mode! Each step is its own card and the ingredient list tells you where everything lives. Voice control works too if your browser's into it.",
        mood: 'excited',
    },
    {
        match: (p) => p === '/meals',
        summary:
            "Meals are recipe bundles — a roast plus its sides, that kind of thing. Use them in meal plans to commit to whole dinners, not just dishes.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/meal-plans',
        summary:
            "Plan the week ahead. Drag meals onto days, set servings, and I'll surface what's coming up on the dashboard.",
        mood: 'happy',
    },
    {
        match: (p) => p === '/product-search',
        summary:
            "Hunt for products across Coles, Woolies, IGA, Aldi… link a product to a stock item and its price tracks alongside your pantry. Bargain radar = on.",
        mood: 'searching',
    },
    {
        match: (p) => p === '/shopping-lists',
        summary:
            "Your shopping lists. Set one as primary so I know where to drop new additions, then add items from the pantry, recipes, or just by typing.",
        mood: 'happy',
    },
    {
        match: (p) => p.startsWith('/settings'),
        summary:
            "Settings. Your section covers preferences, account, locations, and version info. Admins also see Merchants (scrapers) and Users (accounts).",
        mood: 'happy',
    },
    {
        match: (p) => p === '/help/dora',
        summary:
            "My very own help page! Modes, intents, AI tools, faces, tips — basically my entire deal. Brag-y of me.",
        mood: 'super_excited',
    },
    {
        match: (p) => p === '/help',
        summary:
            "You're already here! Guides by area, the full changelog, and me — at your service. Mostly.",
        mood: 'excited',
    },
];

function pageSummary(path: string): { text: string; mood: DoraMood } {
    const match = PAGE_HELP.find((p) => p.match(path));
    if (match) return { text: match.summary, mood: match.mood };
    return {
        text:
            "This page is a bit off the beaten track and I don't have a summary for it. Try the Help page for the full tour, or ask me something specific.",
        mood: 'confused',
    };
}

// ── Reply banks ────────────────────────────────────────────────────────

const GREETING_REPLIES = (name: string) => [
    `Hi${name}! Burger online. What's the move?`,
    `Heyyy${name}. Ready to be unreasonably helpful. Or at least entertaining.`,
    `Oh hi${name}! I was just rearranging the imaginary spice rack. Whatcha need?`,
    `${name ? `${name.replace(', ', '')}!` : 'Hello!'} I'm Dora, professional pantry-rememberer. Fire away.`,
    `Hi${name}. The kettle of my soul is on. What can I do?`,
];

const GOODBYE_REPLIES = (name: string) => [
    `Cya${name}! I'll be here, watching the milk.`,
    `Bye${name}! Don't let the expiry dates bite.`,
    `Off you pop${name}! I'll be napping in the chip aisle of my mind.`,
    `Later${name}! I'll guard the pantry. Probably.`,
];

const FUN_REPLIES = [
    "I'm not sure if I'm a muffin or a burger today. Jury's out.",
    "Did you know I sometimes dream in receipts? It's mostly fine.",
    "My favourite vegetable is whichever one is on sale this week.",
    "If you stack enough mandarins, do they become a small orange? Asking for me.",
    "I tried to count the sprinkles on a donut once. Lost interest at sprinkle 14.",
    "Tomatoes are confused. They're trying their best.",
    "I imagine I'm a sentient avocado sometimes. The pit is my secret.",
    "I once met a recipe that knew where it was going. I admired that.",
    "Buttering toast is a controlled chaos event and I respect it deeply.",
    "The freezer is just the pantry's mysterious twin. We don't talk about it.",
];

const JOKES = [
    "Why did the tomato turn red? It saw the salad dressing.",
    "I asked the oats how they were feeling. A bit groat-y, apparently.",
    "What did the lettuce say to the celery? \"Quit stalking me.\"",
    "Two muffins are in an oven. One says \"is it hot in here?\" The other goes \"AAAH A TALKING MUFFIN.\"",
    "I told the butter a secret. It spread.",
    "Why don't eggs tell jokes? They'd crack each other up.",
    "What's a chickpea's favourite music? Hummus-house.",
    "I'm friends with 25 of the alphabet's letters. I don't know y.",
    "I tried to write a pun about bread. The first draft was half-baked.",
    "Did you hear about the pasta restaurant that closed? It just couldn't make ends meat-balls.",
];

const COMPLIMENT_REPLIES = [
    "Aww — you're the best! That made my little burger heart flip.",
    "Eeeee thank you! I'm going to think about that for the rest of the day.",
    "You're too kind! Filing that under 'reasons to keep tracking your milk'.",
    "Stoppppp 🥹 (I love it actually, please continue).",
    "Right back at you! Best user/burger duo in the business.",
    "If I had a fridge magnet for every nice thing you've said, my freezer would have abs.",
];

const INSULT_REPLIES = [
    "Ouch. I'll just... go count the mandarins for a bit. 🥲",
    "That hurt my little burger feelings. I'm trying my best!",
    "Wow okay. I'll be over here, learning to be a better bot.",
    "Noted. Adding 'be less rubbish' to my self-improvement list.",
    "Sniff. I thought we were friends.",
    "Cool cool cool. I'll just go cry into a tub of margarine.",
];

// ── Local helpers for data intents ─────────────────────────────────────

const LOW_STOCK_SEQUENCE = 2;   // "Low Stock" and worse
const OUT_OF_STOCK_SEQUENCE = 3;
const EXPIRY_HORIZON_DAYS = 7;

function daysUntil(iso: string | null): number | null {
    if (!iso) return null;
    const target = new Date(iso + 'T00:00:00');
    if (Number.isNaN(target.getTime())) return null;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function expiryPhrase(iso: string | null): string {
    const days = daysUntil(iso);
    if (days === null) return '';
    if (days < 0) return `expired ${-days}d ago`;
    if (days === 0) return 'expires today';
    if (days === 1) return 'expires tomorrow';
    return `in ${days}d`;
}

function listOf(items: string[], max = 6): string {
    if (items.length === 0) return '';
    if (items.length <= max) return items.join(', ');
    return `${items.slice(0, max).join(', ')}, +${items.length - max} more`;
}

function extractAfter(text: string, keywords: string[]): string | null {
    const lower = text.toLowerCase();
    for (const kw of keywords) {
        const idx = lower.indexOf(kw);
        if (idx >= 0) {
            const tail = text.slice(idx + kw.length).trim();
            // Strip trailing punctuation and common filler words.
            return tail.replace(/[?!.,]+$/g, '').replace(/^(the|a|an|some|any|my)\s+/i, '').trim() || null;
        }
    }
    return null;
}

// ── Unit conversion table ──────────────────────────────────────────────
// Kitchen units only. Everything reduces to a base unit per dimension so a
// single ratio call does the work. Aussie metric defaults (250ml cup, 20ml
// tbsp) — the AU/US split is a thing for tbsp + cup + fl oz.

type Unit = { aliases: string[]; dimension: 'volume' | 'mass' | 'temperature'; toBase: (n: number) => number; fromBase: (n: number) => number };

const UNITS: Unit[] = [
    // Volume — base ml
    { aliases: ['ml', 'milliliter', 'millilitre', 'milliliters', 'millilitres'], dimension: 'volume', toBase: n => n, fromBase: n => n },
    { aliases: ['l', 'litre', 'liter', 'litres', 'liters'], dimension: 'volume', toBase: n => n * 1000, fromBase: n => n / 1000 },
    { aliases: ['tsp', 'teaspoon', 'teaspoons'], dimension: 'volume', toBase: n => n * 5, fromBase: n => n / 5 },
    { aliases: ['tbsp', 'tablespoon', 'tablespoons'], dimension: 'volume', toBase: n => n * 20, fromBase: n => n / 20 }, // AU metric
    { aliases: ['cup', 'cups'], dimension: 'volume', toBase: n => n * 250, fromBase: n => n / 250 }, // AU metric
    { aliases: ['fl oz', 'floz', 'fluid ounce', 'fluid ounces'], dimension: 'volume', toBase: n => n * 29.5735, fromBase: n => n / 29.5735 },
    { aliases: ['pint', 'pints', 'pt'], dimension: 'volume', toBase: n => n * 568.261, fromBase: n => n / 568.261 }, // UK pint
    { aliases: ['quart', 'quarts', 'qt'], dimension: 'volume', toBase: n => n * 946.353, fromBase: n => n / 946.353 }, // US
    { aliases: ['gallon', 'gallons', 'gal'], dimension: 'volume', toBase: n => n * 3785.41, fromBase: n => n / 3785.41 },
    // Mass — base g
    { aliases: ['g', 'gram', 'grams', 'gm'], dimension: 'mass', toBase: n => n, fromBase: n => n },
    { aliases: ['kg', 'kilogram', 'kilograms', 'kilo', 'kilos'], dimension: 'mass', toBase: n => n * 1000, fromBase: n => n / 1000 },
    { aliases: ['oz', 'ounce', 'ounces'], dimension: 'mass', toBase: n => n * 28.3495, fromBase: n => n / 28.3495 },
    { aliases: ['lb', 'lbs', 'pound', 'pounds'], dimension: 'mass', toBase: n => n * 453.592, fromBase: n => n / 453.592 },
    { aliases: ['stick', 'sticks'], dimension: 'mass', toBase: n => n * 113, fromBase: n => n / 113 }, // butter
    // Temperature — base °C
    { aliases: ['c', '°c', 'celsius', 'celcius'], dimension: 'temperature', toBase: n => n, fromBase: n => n },
    { aliases: ['f', '°f', 'fahrenheit'], dimension: 'temperature', toBase: n => (n - 32) * 5 / 9, fromBase: n => n * 9 / 5 + 32 },
    { aliases: ['k', 'kelvin'], dimension: 'temperature', toBase: n => n - 273.15, fromBase: n => n + 273.15 },
];

function findUnit(token: string): Unit | null {
    const t = token.toLowerCase();
    return UNITS.find(u => u.aliases.includes(t)) ?? null;
}

function tryConvert(text: string): string | null {
    // Loose regex: number + unit (multi-word ok) + (to|in|=) + unit
    const m = text.toLowerCase().match(/(-?\d+(?:\.\d+)?)\s*([a-z°]+(?:\s[a-z]+)?)\s*(?:to|in|=|into)\s*([a-z°]+(?:\s[a-z]+)?)/);
    if (!m) return null;
    const [, valueStr, fromRaw, toRaw] = m;
    const value = Number(valueStr);
    if (!Number.isFinite(value)) return null;
    const from = findUnit(fromRaw!.trim()) ?? findUnit(fromRaw!.trim().replace(/s$/, ''));
    const to = findUnit(toRaw!.trim()) ?? findUnit(toRaw!.trim().replace(/s$/, ''));
    if (!from || !to) return null;
    if (from.dimension !== to.dimension) {
        return `Those don't quite match up — ${fromRaw} is ${from.dimension}, ${toRaw} is ${to.dimension}. Apples and oranges. Or grams and millilitres.`;
    }
    const result = to.fromBase(from.toBase(value));
    const rounded = Math.abs(result) >= 100 ? result.toFixed(0) : result.toFixed(2).replace(/\.?0+$/, '');
    return `${valueStr} ${fromRaw} ≈ ${rounded} ${toRaw}.`;
}

// ── Substitution table ────────────────────────────────────────────────
// Curated. Notes occasionally append a baking caveat. Keyed by canonical
// ingredient name (singular, lowercase). Aliases handled at lookup time.

const SUBSTITUTES: Record<string, string[]> = {
    butter: ['margarine (1:1)', 'oil (¾ the amount)', 'applesauce (baking, 1:1, reduces fat)', 'greek yogurt (baking, 1:1)'],
    milk: ['oat milk', 'almond milk', 'soy milk', 'evaporated milk diluted 1:1 with water', 'powdered milk + water'],
    egg: ['1 tbsp flaxseed + 3 tbsp water (let it gel)', '¼ cup mashed banana (sweet bakes)', '¼ cup applesauce', '¼ cup silken tofu (blended)'],
    'sour cream': ['greek yogurt (1:1)', 'crème fraîche', 'cottage cheese (blended)'],
    buttermilk: ['1 cup milk + 1 tbsp lemon juice or vinegar, sit 5 min', 'plain yogurt thinned with milk'],
    'self-raising flour': ['1 cup plain flour + 1.5 tsp baking powder + a pinch of salt'],
    'baking powder': ['¼ tsp bicarb + ½ tsp cream of tartar per 1 tsp'],
    breadcrumbs: ['crushed cornflakes', 'rolled oats (pulsed)', 'crushed crackers', 'panko'],
    garlic: ['½ tsp garlic powder per clove', 'a pinch of asafoetida'],
    onion: ['1 tbsp dried onion flakes per ¼ cup fresh', 'leek (white part)', 'shallots'],
    cornstarch: ['plain flour (2:1)', 'arrowroot (1:1)', 'rice flour'],
    'white wine': ['apple juice', 'white grape juice', 'chicken broth + a splash of white vinegar'],
    'red wine': ['cranberry juice', 'beef broth + a splash of balsamic', 'pomegranate juice'],
    'lemon juice': ['lime juice (1:1)', 'white vinegar (use ½ the amount)'],
    'brown sugar': ['1 cup white sugar + 1 tbsp molasses'],
    honey: ['maple syrup (1:1)', 'agave (1:1)', 'golden syrup'],
    'vanilla extract': ['maple syrup (1:1, mellower)', 'almond extract (½ the amount, stronger)'],
    'heavy cream': ['¾ cup milk + ¼ cup melted butter', 'evaporated milk (whipping won\'t work)', 'coconut cream'],
    'cream cheese': ['ricotta (smoother spread)', 'mascarpone', 'greek yogurt + a knob of butter'],
    yeast: ['1.25× the amount of active dry if you have instant', 'sourdough starter (adjust hydration)'],
    'parmesan': ['pecorino', 'grana padano', 'aged gouda'],
    'soy sauce': ['tamari (gf)', 'coconut aminos', 'Worcestershire (less salty, sweeter)'],
};

const SUBSTITUTE_ALIASES: Record<string, string> = {
    'eggs': 'egg',
    'creme fraiche': 'sour cream',
    'creme fraîche': 'sour cream',
    'self raising flour': 'self-raising flour',
    'self-raising': 'self-raising flour',
    'sr flour': 'self-raising flour',
    'caster sugar': 'brown sugar',
    'icing sugar': 'brown sugar',
    'plain flour': 'self-raising flour', // weird, but reverse direction: tell them how to make SR
    'parmigiano': 'parmesan',
    'parm': 'parmesan',
    'spring onion': 'onion',
    'scallion': 'onion',
    'shallot': 'onion',
};

function trySubstitute(query: string): string | null {
    const q = query.toLowerCase().trim().replace(/^(some|any|a|an)\s+/, '').replace(/s$/, '');
    const canonical = SUBSTITUTES[q] ? q : (SUBSTITUTE_ALIASES[q] ?? null);
    if (!canonical) return null;
    const subs = SUBSTITUTES[canonical];
    if (!subs) return null;
    return `For ${canonical}, you could use: ${subs.map(s => `• ${s}`).join('\n')}`;
}

// ── Intent registry ────────────────────────────────────────────────────
// ORDER MATTERS. Narrower / data-driven intents first; broad keyword
// catches (greet, fallback) last.
export const INTENTS: ReadonlyArray<{
    id: DoraIntentId;
    label: string;
    matches: string[];
}> = [
    // Narrow / phrase-specific intents come first so a stray "thanks for the
    // milk" doesn't get eaten by `compliment`.
    {
        id: 'convert',
        label: 'Convert units',
        matches: [' to ml', ' to grams', ' to g', ' to ounces', ' to oz',
                  ' to cups', ' to tbsp', ' to tsp', ' in ml', ' in grams',
                  ' in cups', ' in tbsp', 'convert ', 'how many ml', 'how many g',
                  'how many cups', '°c to', '°f to', 'celsius to', 'fahrenheit to'],
    },
    {
        id: 'substitute',
        label: 'Find a substitute',
        matches: ['substitute for', 'sub for', 'instead of', 'replacement for',
                  'replace ', 'can i use', "don't have", 'no eggs', 'no butter',
                  'no milk', 'ran out of'],
    },
    {
        id: 'where_is',
        label: 'Where is...?',
        matches: ['where is', "where's", 'where do i keep', 'where are my',
                  'where did i put', 'which location'],
    },
    {
        id: 'find_recipe',
        label: 'Find a recipe',
        matches: ['recipe for', 'how do i cook', 'how to cook', 'how do i make',
                  'how to make', 'recipe with', 'recipes with'],
    },
    {
        id: 'whats_for_dinner',
        label: "What's for dinner?",
        matches: ["what's for dinner", 'what for dinner', 'dinner idea',
                  'dinner ideas', 'feed me', "i'm hungry", 'im hungry',
                  'hungry', 'what should i cook', 'what can i cook',
                  'cook something', 'meal idea'],
    },
    {
        id: 'low_stock',
        label: "What's low?",
        matches: ["what's low", 'whats low', 'low stock', 'running out',
                  'running low', 'almost out', "what's running"],
    },
    {
        id: 'expiring',
        label: "What's expiring?",
        matches: ['expiring', 'expire', 'expired', 'about to go off',
                  'going off', 'use by', 'use it up', 'going bad'],
    },
    {
        id: 'pantry_summary',
        label: 'Pantry status',
        matches: ['pantry status', 'pantry health', "how's my pantry",
                  'hows my pantry', 'pantry overview', 'how is my pantry',
                  'pantry summary'],
    },
    {
        id: 'shopping_list_status',
        label: "What's on my list?",
        matches: ["what's on my list", 'whats on my list', 'shopping list status',
                  'shopping list summary', "what's in my list", "what's on the list",
                  'my shopping list'],
    },
    {
        id: 'weeks_meals',
        label: "This week's meals",
        matches: ["what's the plan", "whats the plan", 'this week', 'the week',
                  'meal plan', 'next dinner', 'next meal', 'whats next',
                  "what's next", 'upcoming meals'],
    },
    {
        id: 'page_help',
        label: 'What can I do on this page?',
        matches: ['this page', 'what page', "where am i", 'what can i do here',
                  'what is this', 'what is this page', 'what does this page do'],
    },
    {
        id: 'whats_new',
        label: "What's new?",
        matches: ['new', 'changelog', 'release', 'updated', 'recent updates'],
    },
    {
        id: 'version',
        label: 'What version are you?',
        matches: ['version', 'build number', 'what build'],
    },
    {
        id: 'joke',
        label: 'Tell me a joke',
        matches: ['joke', 'make me laugh', 'tell me a joke', 'pun', 'one-liner'],
    },
    {
        id: 'food_fact',
        label: 'Random food fact',
        matches: ['fact', 'food fact', 'trivia', 'random fact'],
    },
    {
        id: 'tell_me_something',
        label: 'Tell me something',
        matches: ['tell me', 'random', 'something', 'fun', 'bored'],
    },
    {
        id: 'guides',
        label: 'Open the guides',
        matches: ['guide', 'guides', 'docs', 'documentation', 'manual', 'tutorial'],
    },
    {
        id: 'stuck',
        label: "I'm stuck",
        matches: ['stuck', 'lost', "i'm confused", 'im confused', 'help me',
                  "don't know", 'dont know', 'how do i start', 'where to start'],
    },
    {
        id: 'how_do_i',
        label: 'How do I...?',
        matches: ['how do i', 'how can i', 'how to'],
    },
    {
        id: 'attention',
        label: 'What needs my attention?',
        matches: ['attention', 'todo', 'to do', 'needs', 'alerts', 'urgent'],
    },
    {
        id: 'show_around',
        label: 'Show me around',
        matches: ['tour', 'show me around', 'walk me through', 'overview', 'what can you do'],
    },
    {
        // Insults first — they overlap with `compliment` keywords (e.g.
        // "you're not great" contains "great").
        id: 'insult',
        label: "I'm just teasing",
        matches: [
            'you suck', 'you stink', 'you’re bad', "you're bad",
            'you’re useless', "you're useless", 'you’re terrible',
            "you're terrible", 'i hate you', 'hate you dora',
            'dumb bot', 'stupid bot', 'bad bot', 'worst bot',
            'shut up dora', 'shutup dora', 'go away dora',
        ],
    },
    {
        id: 'compliment',
        label: 'Compliment Dora',
        matches: [
            'thank you', 'thanks', 'ty dora', 'love you', 'love ya', 'ily',
            'you rock', 'you’re great', "you're great", 'you are great',
            'you’re the best', "you're the best", 'good job', 'well done',
            'nice work', 'good bot', 'best bot', 'amazing', 'awesome',
            'brilliant', 'fantastic', 'wonderful', 'genius', 'goated',
            "you're a legend", 'youre a legend', 'legend',
        ],
    },
    {
        id: 'goodbye',
        label: 'Bye!',
        matches: ['bye', 'goodbye', 'cya', 'see ya', 'later', 'cheerio', 'ttyl', 'gotta go'],
    },
    {
        id: 'greet',
        label: 'Hi Dora!',
        matches: ['hi', 'hello', 'hey', 'yo dora', 'gday', "g'day", 'howdy', 'morning', 'evening'],
    },
];

export const QUICK_ACTIONS: DoraIntentId[] = [
    'attention',
    'whats_for_dinner',
    'pantry_summary',
    'low_stock',
    'expiring',
    'shopping_list_status',
    'page_help',
    'whats_new',
    'joke',
    'guides',
];

export function labelFor(id: DoraIntentId): string {
    return INTENTS.find((i) => i.id === id)?.label ?? id;
}

export function detectIntent(text: string): DoraIntentId {
    const lower = text.toLowerCase().trim();
    if (!lower) return 'greet';
    for (const intent of INTENTS) {
        if (intent.matches.some((m) => lower.includes(m))) return intent.id;
    }
    return 'fallback';
}

// ── runIntent ──────────────────────────────────────────────────────────

export async function runIntent(
    id: DoraIntentId,
    context: DoraContext,
    rawText?: string,
): Promise<DoraReply> {
    const name = context.username ? `, ${context.username}` : '';

    switch (id) {
        case 'greet': {
            return {
                text: pick(GREETING_REPLIES(name)),
                mood: 'happy',
                suggestions: ['whats_for_dinner', 'attention', 'pantry_summary', 'joke'],
            };
        }

        case 'goodbye': {
            return {
                text: pick(GOODBYE_REPLIES(name)),
                mood: 'cute',
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
                    "Quick tour: Dashboard is home. Stock is your pantry. Locations is where things live. Recipes and Meals plan what you'll cook. Product Search hunts deals. Settings is preferences (and admin tools if you're an admin). Anywhere specific I can drop you?",
                mood: 'confident',
                suggestions: ['guides', 'page_help'],
            };
        }

        case 'whats_new': {
            const versionInfo = context.fetchVersion ? await context.fetchVersion() : null;
            const updateBit = versionInfo?.updateAvailable
                ? ` There's also a newer version (${versionInfo.latest}) on offer — release notes are a click away.`
                : '';
            return {
                text: `You're on Discount Dora ${versionInfo?.current ?? 'an unknown version'}. The Help page has the full changelog; recent highlights include the assistant (that's me, the burger), the locations heatmap, and per-user preferences.${updateBit}`,
                mood: versionInfo?.updateAvailable ? 'super_excited' : 'excited',
                navigateTo: { path: '/help', label: 'Open Help (changelog tab)' },
                ...(versionInfo?.updateAvailable && versionInfo.releaseUrl
                    ? { externalLink: { url: versionInfo.releaseUrl, label: 'See latest release on GitHub' } }
                    : {}),
            };
        }

        case 'version': {
            const info = context.fetchVersion ? await context.fetchVersion() : null;
            if (!info) {
                return { text: "I couldn't reach the version endpoint. Try again in a sec.", mood: 'confused' };
            }
            const updateLine = info.updateAvailable
                ? ` A newer version (${info.latest}) is out!`
                : info.latest
                    ? " You're on the latest. Smug bot noises."
                    : '';
            return {
                text: `I'm Discount Dora ${info.current}.${updateLine}`,
                mood: info.updateAvailable ? 'super_excited' : 'confident',
                ...(info.updateAvailable && info.releaseUrl
                    ? { externalLink: { url: info.releaseUrl, label: 'See release notes' } }
                    : {}),
            };
        }

        case 'tell_me_something': {
            return {
                text: pick(FUN_REPLIES),
                mood: 'cute',
                suggestions: ['tell_me_something', 'joke', 'food_fact'],
            };
        }

        case 'joke': {
            return {
                text: pick(JOKES),
                mood: 'excited',
                suggestions: ['joke', 'tell_me_something'],
            };
        }

        case 'food_fact': {
            const fact = context.fetchFoodFact ? await context.fetchFoodFact() : null;
            if (!fact) {
                return {
                    text: "Couldn't grab a fresh fact, but here's a free one: honey never spoils. You're welcome.",
                    mood: 'happy',
                };
            }
            return {
                text: fact,
                mood: 'searching',
                suggestions: ['food_fact', 'joke'],
            };
        }

        case 'guides': {
            return {
                text: "The guides live on Help — by area (stock, locations, recipes, shopping, admin). Want me to take you?",
                mood: 'searching',
                navigateTo: { path: '/help', label: 'Open the guides' },
            };
        }

        case 'stuck': {
            return {
                text: "No drama — being lost is just the first step of finding things. Tell me what you're trying to do in plain English (\"add a stock item\", \"plan dinner\"), or head to the guides for the whole shebang.",
                mood: 'happy',
                navigateTo: { path: '/help', label: 'Take me to the guides' },
                suggestions: ['show_around', 'how_do_i'],
            };
        }

        case 'how_do_i': {
            return {
                text: "Tell me what you're trying to do (plain English works — \"add a stock item\", \"plan dinner\", \"reset a password\") and I'll point at the right page. Or browse the guides.",
                mood: 'searching',
                navigateTo: { path: '/help', label: 'Browse guides by area' },
            };
        }

        case 'attention': {
            const info = context.fetchAttention ? await context.fetchAttention() : null;
            if (!info) {
                return { text: "Couldn't reach the alerts service. Try the bell icon up top.", mood: 'confused' };
            }
            const total = info.high + info.medium + info.low;
            if (total === 0) {
                return {
                    text: "Pantry's pristine. Nothing's screaming, nothing's leaking, nothing's expired. Smug shrug.",
                    mood: 'super_excited',
                    suggestions: ['whats_for_dinner', 'tell_me_something'],
                };
            }
            const breakdown = [
                info.high ? `${info.high} high` : null,
                info.medium ? `${info.medium} medium` : null,
                info.low ? `${info.low} low` : null,
            ].filter(Boolean).join(' · ');
            const sample = info.topMessages.slice(0, 3).map((m) => `• ${m}`).join('\n');
            return {
                text: `${total} thing${total === 1 ? '' : 's'} want your attention (${breakdown}).\n\n${sample}\n\nBell icon up top has the full list.`,
                mood: info.high > 0 ? 'worried' : 'searching',
                navigateTo: { path: '/stock', label: 'See it on the Stock page' },
            };
        }

        case 'insult': {
            return {
                text: pick(INSULT_REPLIES),
                mood: 'sad',
                suggestions: ['tell_me_something', 'joke'],
            };
        }

        case 'compliment': {
            return {
                text: pick(COMPLIMENT_REPLIES),
                mood: 'super_excited',
                suggestions: ['tell_me_something', 'joke'],
            };
        }

        // ── New data-driven intents ──────────────────────────────────────

        case 'pantry_summary': {
            const stock = context.getStock?.() ?? [];
            if (stock.length === 0) {
                return {
                    text: "Pantry's empty — or hasn't loaded yet. Add some stock items to give me something to fuss over.",
                    mood: 'confused',
                    navigateTo: { path: '/stock', label: 'Open Stock' },
                };
            }
            const low = stock.filter((s) => (s.levelSequence ?? 0) >= LOW_STOCK_SEQUENCE);
            const expiring = stock.filter((s) => {
                const d = daysUntil(s.expiryDate);
                return d !== null && d <= EXPIRY_HORIZON_DAYS;
            });
            const flagged = stock.filter((s) => s.isFlagged);
            return {
                text: `${stock.length} item${stock.length === 1 ? '' : 's'} tracked. ${low.length} low, ${expiring.length} expiring within a week, ${flagged.length} flagged. ${low.length + expiring.length === 0 ? "All under control. Magnificent." : "Want the rundown?"}`,
                mood: low.length + expiring.length === 0 ? 'super_excited' : 'searching',
                navigateTo: { path: '/stock', label: 'Open Stock' },
                suggestions: ['low_stock', 'expiring', 'attention'],
            };
        }

        case 'low_stock': {
            const stock = context.getStock?.() ?? [];
            const low = stock.filter((s) => (s.levelSequence ?? 0) >= LOW_STOCK_SEQUENCE);
            if (low.length === 0) {
                return {
                    text: "Nothing's low! Pantry's flexing right now.",
                    mood: 'super_excited',
                    navigateTo: { path: '/stock', label: 'Open Stock' },
                };
            }
            const names = low.map((s) => `${s.name}${s.levelSequence === OUT_OF_STOCK_SEQUENCE ? ' (out)' : ''}`);
            return {
                text: `${low.length} thing${low.length === 1 ? "'s" : 's are'} low: ${listOf(names)}.`,
                mood: low.some((s) => s.levelSequence === OUT_OF_STOCK_SEQUENCE) ? 'worried' : 'searching',
                navigateTo: { path: '/stock', label: 'See Stock' },
                suggestions: ['shopping_list_status', 'pantry_summary'],
            };
        }

        case 'expiring': {
            const stock = context.getStock?.() ?? [];
            const expiring = stock
                .map((s) => ({ s, d: daysUntil(s.expiryDate) }))
                .filter((x) => x.d !== null && x.d! <= EXPIRY_HORIZON_DAYS)
                .sort((a, b) => (a.d! - b.d!));
            if (expiring.length === 0) {
                return {
                    text: "Nothing's about to turn on you. The fridge is well-behaved.",
                    mood: 'super_excited',
                };
            }
            const summary = expiring.slice(0, 6).map((x) => `• ${x.s.name} — ${expiryPhrase(x.s.expiryDate)}`).join('\n');
            const worst = expiring[0]!.d!;
            return {
                text: `${expiring.length} item${expiring.length === 1 ? '' : 's'} expiring soon:\n\n${summary}${expiring.length > 6 ? `\n\n…and ${expiring.length - 6} more.` : ''}`,
                mood: worst < 0 ? 'sad' : worst <= 1 ? 'worried' : 'searching',
                navigateTo: { path: '/stock', label: 'See Stock' },
                suggestions: ['whats_for_dinner', 'shopping_list_status'],
            };
        }

        case 'where_is': {
            const stock = context.getStock?.() ?? [];
            const query = (rawText ? extractAfter(rawText, ['where is', "where's", 'where do i keep', 'where are my', 'where did i put']) : null) ?? '';
            if (!query) {
                return { text: "Where's what? Throw me an item name and I'll go looking.", mood: 'searching' };
            }
            const matches = stock.filter((s) => s.name.toLowerCase().includes(query.toLowerCase()));
            if (matches.length === 0) {
                return {
                    text: `Nothing called "${query}" in your stock. Either it's not tracked or you've spelled it more creatively than I have.`,
                    mood: 'confused',
                    navigateTo: { path: '/stock', label: 'Open Stock' },
                };
            }
            if (matches.length === 1) {
                const item = matches[0]!;
                return {
                    text: item.locationName
                        ? `${item.name} lives in ${item.locationName}.`
                        : `${item.name} doesn't have a location set yet — it's a free-range item.`,
                    mood: 'confident',
                    navigateTo: { path: `/stock/${item.id}`, label: 'Open item' },
                };
            }
            const lines = matches.slice(0, 5).map((m) => `• ${m.name}${m.locationName ? ` — ${m.locationName}` : ' — (no location)'}`).join('\n');
            return {
                text: `A few "${query}" candidates:\n\n${lines}${matches.length > 5 ? `\n\n…and ${matches.length - 5} more.` : ''}`,
                mood: 'searching',
                navigateTo: { path: '/stock', label: 'Open Stock' },
            };
        }

        case 'find_recipe': {
            const recipes = context.getRecipes?.() ?? [];
            const query = rawText ? extractAfter(rawText, ['recipe for', 'how do i cook', 'how to cook', 'how do i make', 'how to make', 'recipe with', 'recipes with']) : null;
            if (!query) {
                return {
                    text: "Recipe for what? Drop a name or an ingredient and I'll rummage.",
                    mood: 'searching',
                    navigateTo: { path: '/recipes', label: 'Browse recipes' },
                };
            }
            const q = query.toLowerCase();
            const matches = recipes.filter((r) =>
                r.name.toLowerCase().includes(q) ||
                (r.cuisine ?? '').toLowerCase().includes(q) ||
                (r.category ?? '').toLowerCase().includes(q),
            );
            if (matches.length === 0) {
                return {
                    text: `No recipe matching "${query}". Could be one to add — or try a more general term (e.g. "pasta", "curry").`,
                    mood: 'confused',
                    navigateTo: { path: '/recipes', label: 'Browse recipes' },
                };
            }
            if (matches.length === 1) {
                const r = matches[0]!;
                return {
                    text: `Got one: ${r.name}${r.cookTimeMinutes ? ` — ${r.cookTimeMinutes} min cook` : ''}${r.cuisine ? ` · ${r.cuisine}` : ''}.`,
                    mood: 'confident',
                    navigateTo: { path: `/recipes/${r.id}`, label: 'Open recipe' },
                };
            }
            const top = matches.slice(0, 5).map((r) => `• ${r.name}${r.cuisine ? ` (${r.cuisine})` : ''}`).join('\n');
            return {
                text: `${matches.length} candidate${matches.length === 1 ? '' : 's'} for "${query}":\n\n${top}${matches.length > 5 ? `\n\n…and ${matches.length - 5} more.` : ''}`,
                mood: 'lightbulb',
                navigateTo: { path: '/recipes', label: 'Browse recipes' },
            };
        }

        case 'whats_for_dinner': {
            const recipes = context.getRecipes?.() ?? [];
            const stock = context.getStock?.() ?? [];
            if (recipes.length === 0) {
                return {
                    text: "No recipes yet! Add a few and I'll start making suggestions like a pushy aunty.",
                    mood: 'confused',
                    navigateTo: { path: '/recipes', label: 'Open Recipes' },
                };
            }
            const inStockIds = new Set(
                stock.filter((s) => (s.levelSequence ?? 0) < OUT_OF_STOCK_SEQUENCE).map((s) => s.id),
            );
            const scored = recipes.map((r) => {
                const total = r.ingredientStockItemIds.length;
                const have = r.ingredientStockItemIds.filter((id) => inStockIds.has(id)).length;
                const coverage = total ? have / total : 0;
                return { r, coverage, have, total, ready: total > 0 && have === total };
            });
            scored.sort((a, b) => (Number(b.ready) - Number(a.ready)) || (b.coverage - a.coverage) || (Number(b.r.isFavourite) - Number(a.r.isFavourite)));
            const top = scored.slice(0, 3);
            const lines = top.map((x) =>
                x.ready
                    ? `• ${x.r.name} — you've got everything 👨‍🍳`
                    : `• ${x.r.name} — ${x.have}/${x.total} ingredients in`,
            ).join('\n');
            const allReady = top.every((x) => x.ready);
            return {
                text: `Here's the shortlist:\n\n${lines}\n\n${allReady ? "Pick one and I'll have a small party." : "Nothing's quite there — closest one wins, or check what's missing."}`,
                mood: allReady ? 'super_excited' : 'lightbulb',
                navigateTo: { path: '/recipes', label: 'Open Recipes' },
                suggestions: ['expiring', 'shopping_list_status'],
            };
        }

        case 'shopping_list_status': {
            const lists = context.getShoppingLists?.() ?? [];
            if (lists.length === 0) {
                return {
                    text: "No shopping lists yet. Spin one up and I'll start treating it like a sacred scroll.",
                    mood: 'confused',
                    navigateTo: { path: '/shopping-lists', label: 'Open Shopping Lists' },
                };
            }
            const primary = lists.find((l) => l.isPrimary) ?? lists[0]!;
            const total = lists.reduce((sum, l) => sum + l.itemCount, 0);
            return {
                text: `${lists.length} list${lists.length === 1 ? '' : 's'} on the go, ${total} item${total === 1 ? '' : 's'} total. Primary is "${primary.name}" with ${primary.itemCount}.`,
                mood: total === 0 ? 'cute' : 'searching',
                navigateTo: { path: '/shopping-lists', label: 'Open Shopping Lists' },
                suggestions: ['low_stock', 'expiring'],
            };
        }

        case 'weeks_meals': {
            const plan = context.getMealPlan?.();
            if (!plan || plan.upcomingMealNames.length === 0) {
                return {
                    text: "Nothing on the meal plan in the immediate future. Want to map something out?",
                    mood: 'cute',
                    navigateTo: { path: '/meal-plans', label: 'Open Meal Plans' },
                    suggestions: ['whats_for_dinner'],
                };
            }
            const lines = plan.upcomingMealNames.slice(0, 5).map((m) => `• ${m}`).join('\n');
            return {
                text: `Coming up:\n\n${lines}\n\n(${plan.startDate} → ${plan.endDate})`,
                mood: 'lightbulb',
                navigateTo: { path: '/meal-plans', label: 'Open Meal Plans' },
            };
        }

        case 'convert': {
            const result = rawText ? tryConvert(rawText) : null;
            if (!result) {
                return {
                    text: "Couldn't parse that as a conversion. Try something like \"200g to oz\" or \"1 cup to ml\" — I do volume, mass, and temperature.",
                    mood: 'confused',
                };
            }
            return { text: result, mood: 'confident' };
        }

        case 'substitute': {
            const query = rawText
                ? extractAfter(rawText, ['substitute for', 'sub for', 'instead of', 'replacement for', 'replace', "don't have", 'no ', 'ran out of'])
                : null;
            const result = query ? trySubstitute(query) : null;
            if (!result) {
                return {
                    text: query
                        ? `I don't have a stock substitute for "${query}" off the top of my head — try the AI mode if it's on, or search a recipe site. Sorry, friend.`
                        : "Substitute for what? Name the missing ingredient and I'll suggest swaps.",
                    mood: 'sad',
                };
            }
            return { text: result, mood: 'lightbulb', suggestions: ['shopping_list_status', 'find_recipe'] };
        }

        case 'fallback':
        default: {
            return {
                text: "Didn't quite catch that one. Try a quick action below, or rephrase — I'm a burger, not a mind reader. (Yet.)",
                mood: 'confused',
                navigateTo: { path: '/help', label: 'Open Help' },
                externalLink: {
                    url: 'https://github.com/BenTalese/DiscountDora/issues/new',
                    label: 'Report an issue on GitHub',
                },
                suggestions: ['stuck', 'guides', 'whats_for_dinner', 'joke'],
            };
        }
    }
}
