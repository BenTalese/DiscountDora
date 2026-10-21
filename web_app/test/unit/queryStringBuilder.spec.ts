// FU-520 workstream 1 — unit coverage for the list-endpoint query builder.
//
// Every API list call routes its filter/sort/pagination through
// `createQueryString`, so the `field:op:value` wire format and the
// URL-encoding behaviour are a de-facto server contract — pin them.
//
// Pure function only — no Vue, no network (see vitest.config.ts).
import { describe, expect, it } from 'vitest';

import {
    createQueryString,
    FilterOperator,
    SortOrder,
} from 'src/services/api/queryStringBuilder';

describe('createQueryString — list-endpoint query wire format', () => {
    it('returns an empty string when nothing is requested', () => {
        expect(createQueryString()).toBe('');
        expect(createQueryString([], undefined, undefined)).toBe('');
    });

    it('encodes a single filter as field:op:value', () => {
        const qs = createQueryString([
            { field: 'name', operator: FilterOperator.CONTAINS, value: 'milk' },
        ]);
        expect(qs).toBe('?filter=name%3Act%3Amilk');
    });

    it('repeats the filter param for multiple filters, preserving order', () => {
        const qs = createQueryString([
            { field: 'name', operator: FilterOperator.EQUAL, value: 'milk' },
            { field: 'qty', operator: FilterOperator.GREATER_THAN, value: 2 },
        ]);
        expect(qs).toBe('?filter=name%3Aeq%3Amilk&filter=qty%3Agt%3A2');
    });

    it('stringifies number and boolean filter values', () => {
        const qs = createQueryString([
            { field: 'is_essential', operator: FilterOperator.EQUAL, value: true },
        ]);
        expect(qs).toBe('?filter=is_essential%3Aeq%3Atrue');
    });

    it('defaults sort order to ascending', () => {
        expect(createQueryString(undefined, { field: 'name' })).toBe('?sort=name%3Aasc');
    });

    it('honours an explicit descending sort', () => {
        expect(
            createQueryString(undefined, { field: 'created_at', order: SortOrder.DESCENDING }),
        ).toBe('?sort=created_at%3Adesc');
    });

    it('emits page and limit for pagination', () => {
        expect(createQueryString(undefined, undefined, { page: 2, limit: 50 })).toBe(
            '?page=2&limit=50',
        );
    });

    it('combines filters, sort, and pagination in one query string', () => {
        const qs = createQueryString(
            [{ field: 'name', operator: FilterOperator.CONTAINS, value: 'rice' }],
            { field: 'name', order: SortOrder.ASCENDING },
            { page: 1, limit: 20 },
        );
        expect(qs).toBe('?filter=name%3Act%3Arice&sort=name%3Aasc&page=1&limit=20');
    });

    it('URL-encodes reserved characters in filter values', () => {
        const qs = createQueryString([
            { field: 'name', operator: FilterOperator.CONTAINS, value: 'salt & pepper' },
        ]);
        // application/x-www-form-urlencoded: spaces become '+', '&' is escaped.
        expect(qs).toBe('?filter=name%3Act%3Asalt+%26+pepper');
    });
});
