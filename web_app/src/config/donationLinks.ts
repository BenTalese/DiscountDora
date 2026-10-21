import { ICONS } from 'src/style/icons';

// R-003 single source for the project's donation / "support the project"
// links. These are static AUTHOR channels baked into the open-source build —
// like the support channel (`support_channel.py`) they're the author's, not
// per-install admin config, so they live as a committed constant, not an
// AppSetting.
//
// PLACEHOLDER until FU-608 stands up the real accounts (GitHub Sponsors +
// Buy Me a Coffee + a third TBD platform). Swap the URLs here and every
// consumer updates at once: the three <DonateButton> placements (menu bar,
// auth shell, settings), `.github/FUNDING.yml`, and the README donate section.
// `DONATIONS_CONFIGURED` stays false while any link is still the sentinel, so
// a test can assert the swap happened and the UI can avoid implying a live page.

export interface DonationPlatform {
    /** Display label shown in the popover row. */
    label: string;
    /** External URL, opens in a new tab. PLACEHOLDER until FU-608. */
    url: string;
    /** Row icon (from the central ICONS catalogue). */
    icon: string;
    /** The single platform the buttons headline as the primary CTA. */
    primary?: boolean;
}

/** Sentinel every link carries until the owner swaps in the real URLs (FU-608). */
export const DONATION_PLACEHOLDER = 'https://example.com/PLACEHOLDER-see-FU-608';

// Three platforms: Buy Me a Coffee (casual one-off) + GitHub Sponsors
// (recurring / developer audience) span the meaningful spread; PayPal.me is the
// cheap universal catch-all for people who'd rather use PayPal than sign up
// anywhere new. Deliberately no Ko-fi (dupes BMC) / Patreon / crypto.
export const DONATION_PLATFORMS: DonationPlatform[] = [
    {
        // Instant to set up (no approval wait) → primary CTA while GitHub
        // Sponsors onboarding is pending. buymeacoffee.com/<handle>
        label: 'Buy Me a Coffee',
        url: DONATION_PLACEHOLDER,
        icon: ICONS.coffee,
        primary: true,
    },
    {
        // github.com/sponsors/BenTalese — needs GitHub approval + payout setup.
        label: 'GitHub Sponsors',
        url: DONATION_PLACEHOLDER,
        icon: ICONS.favorite,
    },
    {
        // paypal.me/<handle> — near-zero setup; universal catch-all.
        label: 'PayPal',
        url: DONATION_PLACEHOLDER,
        icon: ICONS.volunteer_activism,
    },
];

/** The headline platform the buttons default to (first `primary`, else first). */
export const PRIMARY_DONATION: DonationPlatform =
    DONATION_PLATFORMS.find((p) => p.primary) ?? DONATION_PLATFORMS[0]!;

/** False while every link is still the sentinel — the owner hasn't swapped
 *  the real URLs in yet (FU-608). */
export const DONATIONS_CONFIGURED: boolean = DONATION_PLATFORMS.some(
    (p) => !p.url.includes('PLACEHOLDER'),
);
