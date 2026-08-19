// @vitest-environment jsdom
/**
 * FU-520 workstream 1, component layer — the picker-avatar StockLevelDot.
 *
 * `components/stock/StockLevelDot.vue` is the simple level-dot avatar
 * shared by the three stock-level pickers (R-001). The former UX-v2
 * signal component at `components/StockLevelDot.vue` was retired — see
 * the shopping-list simplification pass for why (the "OK/Low/Out"
 * badge was a remnant of the old stock-item row component).
 */
import { mount } from '@vue/test-utils';
import { QAvatar, Quasar } from 'quasar';
import { describe, expect, it } from 'vitest';

import DotAvatar from 'src/components/stock/StockLevelDot.vue';

describe('StockLevelDot (picker avatar)', () => {
    function mountAvatar(props: Record<string, unknown>) {
        return mount(DotAvatar, {
            props: { sequence: null, ...props },
            global: { plugins: [Quasar], components: { QAvatar } },
        });
    }

    // FU-666: these two pinned the pre-D-001 mapping, where out-of-stock had no
    // palette colour and "low" borrowed red. `colourForSequence` moved to the
    // D-001 green→amber→red ramp (its docblock: "Out-of-stock is a *real* level
    // and now maps to red (negative) … it no longer routes through this null
    // branch"), so the spec had been failing on a clean tree ever since. The
    // contract worth pinning is the ramp itself plus the *narrowed* null case.
    it('colours by canonical sequence along the D-001 ramp', () => {
        expect(mountAvatar({ sequence: 0 }).find('.q-avatar').classes())
            .toContain('bg-positive');
        expect(mountAvatar({ sequence: 1 }).find('.q-avatar').classes())
            .toContain('bg-warning');
        expect(mountAvatar({ sequence: 2 }).find('.q-avatar').classes())
            .toContain('bg-negative');
    });

    it('falls back to the sunken neutral only when the level is unknown', () => {
        // No sequence at all (untracked item), and a custom level beyond the
        // seeded three — neither has a place on the ramp.
        expect(mountAvatar({ sequence: null }).find('.q-avatar').classes())
            .toContain('dora-bg-neutral');
        expect(mountAvatar({ sequence: 7 }).find('.q-avatar').classes())
            .toContain('dora-bg-neutral');
    });

    it('passes size and extra classes through', () => {
        const avatar = mountAvatar({ sequence: 0, size: '24px', dotClass: 'q-mr-sm' })
            .find('.q-avatar');

        expect(avatar.attributes('style')).toContain('font-size: 24px');
        expect(avatar.classes()).toContain('q-mr-sm');
    });
});
