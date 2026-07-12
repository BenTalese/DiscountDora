// Shared accessibility (axe-core) helper for component specs — FU-542.
//
// jsdom has no layout/paint engine, so two axe rules can't be meaningfully
// evaluated here and are disabled:
//   - `color-contrast` — needs computed colours + geometry jsdom doesn't have.
//     (Colour contrast is covered by the manual a11y pass / FU-010 / FU-224.)
//   - `region` — a component mounted in isolation legitimately has no landmark
//     wrapper; that's a page-composition concern, not a component defect.
// Everything axe CAN verify statically stays on: control names/labels, ARIA
// roles + states, `aria-*` validity, duplicate ids, list/table structure, etc.
//
// We assert on `results.violations` directly (rather than the vitest-axe
// matcher) so there's no `expect.extend` / type-augmentation to thread through
// every spec, and so failures print the offending rule + node HTML.
import { axe } from 'vitest-axe';

interface AxeOptions {
    // Some components legitimately render an ARIA role that REQUIRES a parent
    // role (e.g. `listitem` needs an ancestor `list`). Mounted in isolation
    // that parent is absent — in the real app it's always there. Pass the
    // required parent role to wrap the node during the scan so the check
    // reflects real usage instead of the test harness (e.g. wrapRole: 'list').
    wrapRole?: string;
}

export async function expectAccessible(
    element: Element,
    options: AxeOptions = {},
): Promise<void> {
    // axe needs the node in the document for name-computation rules to resolve
    // (labels via `for`, aria-labelledby, etc.). The existing mount helpers
    // don't `attachTo`, so park it on document.body for the scan then detach.
    const wasAttached = element.isConnected;
    let scanTarget: Element = element;
    let wrapper: HTMLElement | null = null;
    if (options.wrapRole) {
        wrapper = document.createElement('div');
        wrapper.setAttribute('role', options.wrapRole);
        wrapper.appendChild(element);
        document.body.appendChild(wrapper);
        scanTarget = wrapper;
    } else if (!wasAttached) {
        document.body.appendChild(element);
    }
    try {
        const results = await axe(scanTarget, {
            rules: {
                'color-contrast': { enabled: false },
                region: { enabled: false },
            },
        });
        const violations = results.violations ?? [];
        if (violations.length > 0) {
            const detail = violations
                .map((v) => {
                    const nodes = v.nodes.map((n) => `      ${n.html}`).join('\n');
                    return `  • [${v.impact ?? 'n/a'}] ${v.id} — ${v.help}\n${nodes}`;
                })
                .join('\n');
            throw new Error(
                `Expected no accessibility violations, found ${violations.length}:\n${detail}`,
            );
        }
    } finally {
        if (wrapper && wrapper.parentNode === document.body) {
            document.body.removeChild(wrapper);
        } else if (!wasAttached && element.parentNode === document.body) {
            document.body.removeChild(element);
        }
    }
}
