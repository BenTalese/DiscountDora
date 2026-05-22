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
