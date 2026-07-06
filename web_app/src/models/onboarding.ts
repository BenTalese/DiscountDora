// Mirrors OnboardingStateDto / SeedResultDto from
// dora_api/features/onboarding/onboarding.py.

export type StoreStatus = {
    total: number;
    enabled: number;
};

export type OnboardingState = {
    completed: boolean;
    completed_at: string | null;
    first_user: boolean;
    store_status: StoreStatus;
};

export type SeedRequest = {
    groups: boolean;
    locations: boolean;
    // FU-195 — optional per-name filter over the bundled defaults. Null
    // (or omitted) means "seed all" when the bool is true; a provided
    // list narrows the seed to just those names/paths.
    //
    // location_paths use "Zone" for a top-level zone alone, or
    // "Zone/Child" for a child under it. Selecting a child implicitly
    // creates its parent zone even when the parent's path isn't listed.
    group_names?: string[] | null;
    location_paths?: string[] | null;
};

export type SeedResult = {
    groups_created: number;
    groups_skipped: number;
    locations_created: number;
    locations_skipped: number;
};

// C-5.5 — starter catalogue (default groups/locations + starter packs) the
// wizard previews and lets the user pick from. Served by GET /onboarding/catalog.
export type LocationNode = {
    name: string;
    kind: string;
    children: LocationNode[];
};

export type StarterPackItem = {
    name: string;
    group: string | null;
    location: string | null;
};

export type StarterPack = {
    key: string;
    label: string;
    blurb: string;
    items: StarterPackItem[];
};

export type OnboardingCatalog = {
    groups: string[];
    locations: LocationNode[];
    packs: StarterPack[];
};

// C-5.5 — create stock items by NAME (group/location resolved server-side
// against the seeded catalogues). Used for both starter-pack picks and the
// wizard's first stock items. Idempotent (dedupe by name).
export type SeedItemInput = {
    name: string;
    group_name?: string | null;
    location_name?: string | null;
};

export type SeedItemsRequest = {
    items: SeedItemInput[];
};

export type SeedItemsResult = {
    created: number;
    skipped: number;
};

// FU-194 — opt-in demo dataset (one recipe + the StockItems it needs + a
// current-week MealPlan with one entry). The handler is idempotent; `seeded`
// is `false` when the demo recipe already existed (so a re-finish never
// duplicates rows).
export type SeedDemoResult = {
    seeded: boolean;
    items_created: number;
    recipe_created: boolean;
    meal_plan_created: boolean;
};
