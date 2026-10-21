// C-cross Chunk 4 — location display policy (proposal §2.5).
//
// "Right shelf" / "Left side" is meaningless out of context. The
// universal rule is: **default to the zone** (top-level breadcrumb
// node) on every chip / inline label across the app, and reveal the
// full breadcrumb in a tooltip on hover / long-press.
//
// One helper, used at every render site. The per-user
// `location_detail` toggle the proposal mentioned in §4-4 is deferred
// for now — if real usage flags missing the full breadcrumb at a
// glance, add a `mode` arg and feed the user's preference in.

export type LocationFormatMode = 'zone' | 'full';

/** Render a breadcrumb path. `'zone'` returns the top-level node
 *  name (the zone — "Pantry" / "Fridge"); `'full'` returns the
 *  whole path joined with ` › `. Empty paths return an empty string
 *  so the caller can fall back to its own placeholder. */
export function formatLocation(
    breadcrumb: readonly string[] | null | undefined,
    mode: LocationFormatMode = 'zone',
): string {
    if (!breadcrumb || breadcrumb.length === 0) return '';
    if (mode === 'zone') return breadcrumb[0] ?? '';
    return breadcrumb.join(' › ');
}

/** True when the breadcrumb has sub-areas under the zone — i.e. the
 *  tooltip would actually reveal information. Used to suppress the
 *  tooltip when there's nothing to show (zone == full). */
export function locationHasDetail(
    breadcrumb: readonly string[] | null | undefined,
): boolean {
    return !!breadcrumb && breadcrumb.length > 1;
}

/** Narrow a location tree to the nodes matching `query` (case-insensitive
 *  substring on the name), keeping the shape intact.
 *
 *  A node survives if it matches itself **or** has a surviving descendant —
 *  otherwise a matching "Left" section would vanish along with the "Top
 *  shelf" area that doesn't match. A node that matches keeps its whole
 *  subtree, so you can see what's inside the thing you searched for.
 *
 *  Display-only (the settings page's filter box); the store keeps the
 *  unfiltered tree. */
export function filterLocationTree<
    T extends { name: string; children: T[] },
>(nodes: readonly T[], query: string): T[] {
    const needle = query.trim().toLowerCase();
    if (!needle) return [...nodes];

    const walk = (node: T): T | null => {
        if (node.name.toLowerCase().includes(needle)) return node;
        const children = node.children
            .map(walk)
            .filter((child): child is T => child !== null);
        return children.length > 0 ? { ...node, children } : null;
    };

    return nodes.map(walk).filter((node): node is T => node !== null);
}
