import { computed } from 'vue';
import { useRoute } from 'vue-router';

// Vue Router's built-in active matching is route-record-based, so flat
// sibling routes (e.g. `/recipes` and `/recipes/:id` declared side-by-side
// rather than nested) don't trigger active state on the parent link. Menu
// links should highlight on any URL under their path, so match on path
// prefix instead. `extraPrefixes` covers cases where one nav entry spans
// paths that aren't direct children of `link`.
export function useMenuLinkActive(
    link: () => string,
    extraPrefixes: () => string[] | undefined = () => undefined,
) {
    const route = useRoute();
    return computed(() => {
        const path = route.path;
        const candidates = [link(), ...(extraPrefixes() ?? [])].filter(Boolean);
        return candidates.some((p) => path === p || path.startsWith(p + '/'));
    });
}
