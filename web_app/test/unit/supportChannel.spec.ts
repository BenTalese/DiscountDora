// FU-370 — the support-channel report-target helper carries the pre-fill
// contract (proposal §4.4): URL wins over email, query params append with the
// right separator (the GitHub new-issue URL already carries `?template=`), and
// a blank channel yields '' so callers render nothing. Pure function — no Vue,
// no network — so it lives in the unit corpus alongside doraIntents.
import { describe, expect, it } from 'vitest';

import { supportHref } from 'src/composables/useSupportChannel';

describe('supportHref — report target + pre-fill contract', () => {
    it('returns empty string when no channel is configured', () => {
        expect(supportHref({ url: '', email: '' })).toBe('');
        expect(supportHref({ url: '', email: '' }, { subject: 's', body: 'b' })).toBe('');
    });

    it('prefers the URL over the email when both are set', () => {
        const href = supportHref(
            { url: 'https://example.com/new', email: 'dora@example.com' },
            {},
        );
        expect(href).toBe('https://example.com/new');
    });

    it('appends title/body to a bare URL with ?', () => {
        const href = supportHref(
            { url: 'https://example.com/new', email: '' },
            { subject: 'Bug X', body: 'line1\nline2' },
        );
        expect(href.startsWith('https://example.com/new?')).toBe(true);
        expect(href).toContain('title=Bug+X');
        expect(href).toContain('body=line1%0Aline2');
    });

    it('appends with & when the URL already has a query (GitHub template case)', () => {
        const href = supportHref(
            {
                url: 'https://github.com/x/dashy-dora-issues/issues/new?template=bug_report.yml',
                email: '',
            },
            { subject: 'Bug' },
        );
        // Existing ?template= is preserved; new params joined with &.
        expect(href).toContain('template=bug_report.yml&');
        expect(href).toContain('title=Bug');
        expect((href.match(/\?/g) ?? []).length).toBe(1);
    });

    it('builds a mailto: link when only email is set', () => {
        const href = supportHref(
            { url: '', email: 'dora@example.com' },
            { subject: 'Bug Y', body: 'details' },
        );
        expect(href.startsWith('mailto:dora@example.com?')).toBe(true);
        expect(href).toContain('subject=Bug+Y');
        expect(href).toContain('body=details');
    });

    it('mailto: without a pre-fill has no query string', () => {
        expect(supportHref({ url: '', email: 'dora@example.com' })).toBe(
            'mailto:dora@example.com',
        );
    });
});
