/**
 * The unit picker's vocabulary.
 *
 * Pinned because the list stopped being a suggestion on 2026-08-26: the recipe
 * ingredient editor dropped `new-value-mode`, so whatever this returns is now
 * the *only* thing a user can pick. The narrowing is the part worth a test —
 * the generated `UNIT_TABLE` spans six dimensions, and a regeneration that
 * added, say, a new energy unit would silently put it in the ingredient
 * dropdown if the filter were dropped.
 */
import { describe, expect, it } from 'vitest';

import { useUnitOptions } from 'src/composables/useUnitOptions';

const INGREDIENT_DIMENSIONS = ['volume', 'mass', 'count'] as const;

describe('useUnitOptions', () => {
    it('de-duplicates the table down to one row per canonical form', () => {
        const { allUnitOptions } = useUnitOptions();
        const values = allUnitOptions.value.map((o) => o.value);
        expect(new Set(values).size).toBe(values.length);
        // "tablespoon" / "tablespoons" / "tbsp" / "T" are four aliases, one row.
        expect(values.filter((v) => v === 'tbsp')).toHaveLength(1);
    });

    it('narrows to the dimensions an ingredient can be measured in', () => {
        const { allUnitOptions } = useUnitOptions(INGREDIENT_DIMENSIONS);
        const values = allUnitOptions.value.map((o) => o.value);

        // Present: the three ingredient dimensions, including the informal
        // words the removed free-text escape used to be needed for.
        for (const unit of ['g', 'kg', 'ml', 'L', 'cup', 'tbsp', 'tsp',
            'ea', 'pack', 'dozen', 'pinch', 'dash']) {
            expect(values).toContain(unit);
        }
        // Absent: energy and length. Nobody measures an ingredient in kJ.
        for (const unit of ['kJ', 'kcal', 'J', 'cm', 'mm', 'm', 'ft', 'in']) {
            expect(values).not.toContain(unit);
        }
    });

    it('searches aliases but never escapes the narrowing', () => {
        const { unitOptions, onUnitFilter } = useUnitOptions(INGREDIENT_DIMENSIONS);

        // Typing a unit's long form finds its canonical abbreviation.
        onUnitFilter('tablespoons', (cb) => cb());
        expect(unitOptions.value.map((o) => o.value)).toContain('tbsp');

        // A term that only matches an out-of-dimension unit finds nothing,
        // rather than leaking it back in through the alias search.
        onUnitFilter('kilojoule', (cb) => cb());
        expect(unitOptions.value).toHaveLength(0);

        // Clearing restores the full narrowed list.
        onUnitFilter('', (cb) => cb());
        expect(unitOptions.value.length).toBeGreaterThan(10);
        expect(unitOptions.value.map((o) => o.value)).not.toContain('kJ');
    });
});
