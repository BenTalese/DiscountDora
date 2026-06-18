export interface MenuButtonProps {
    caption?: string;
    icon: string;
    label: string;
    /** Internal route. Ignored when `href` is set. */
    link: string;
    // Extra path prefixes that should also trigger the active state.
    // Use when one nav entry covers routes that aren't direct children
    // of `link`. (No current consumers — Cookbook used to need this
    // when detail lived at `/recipes/:id`; since 2026-06-12 detail is
    // `/cookbook/:id` so the natural prefix match suffices.)
    activePrefixes?: string[];
    /** External URL — when set, the item renders as `<a target="_blank">`
     *  instead of a router-link. Used by the Phase D "Product Search" nav
     *  entry which opens an admin-configured URL. */
    href?: string;
    /** R-014 reveal-and-disable: render visible-disabled with a tooltip
     *  explaining how to enable it. Wins over `link` / `href`. */
    disabled?: boolean;
    /** Tooltip surfaced on a disabled item. */
    disabledTooltip?: string;
}
