export interface MenuButtonProps {
    caption?: string;
    icon: string;
    label: string;
    link: string;
    // Extra path prefixes that should also trigger the active state.
    // Use when one nav entry covers routes that aren't direct children
    // of `link`. (No current consumers — Cookbook used to need this
    // when detail lived at `/recipes/:id`; since 2026-06-12 detail is
    // `/cookbook/:id` so the natural prefix match suffices.)
    activePrefixes?: string[];
}
