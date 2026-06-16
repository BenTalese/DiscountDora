// Mirrors OnboardingStateDto / SeedResultDto from
// dora_api/features/onboarding/onboarding.py.

export type MerchantStatus = {
    total: number;
    enabled: number;
};

export type OnboardingState = {
    completed: boolean;
    completed_at: string | null;
    first_user: boolean;
    has_locations: boolean;
    has_groups: boolean;
    has_stock_items: boolean;
    merchant_status: MerchantStatus;
};

export type SeedRequest = {
    groups: boolean;
    locations: boolean;
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
