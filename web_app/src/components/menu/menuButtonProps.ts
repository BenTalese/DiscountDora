export interface MenuButtonProps {
    caption?: string;
    icon: string;
    label: string;
    link: string;
    // Extra path prefixes that should also trigger the active state.
    // Use when one nav entry covers routes that aren't direct children of
    // `link` (e.g. Recipes menu lives at `/cookbook` but `/recipes/:id`
    // is the detail route).
    activePrefixes?: string[];
}
