import { computed, ref } from 'vue';

import { UNIT_TABLE } from 'src/generated/units_table';

/**
 * The app's unit picker vocabulary.
 *
 * `UNIT_TABLE` is generated from `dora_api/domain/units.py` and is mostly
 * synonyms — "tablespoon", "tablespoons", "tbsp" and "T" are four keys with one
 * canonical form. A dropdown built straight off it is 200 lines of the same
 * dozen units, so the list is de-duplicated by canonical form and the aliases
 * are used for *searching* instead: typing "tablespoons" finds `tbsp`.
 *
 * R-001/R-003 — this was written inside `SubstituteMetadataDialog` first; the
 * recipe ingredient editor needed the same list, so it lives here once rather
 * than being copied. Callers that need a *subset* (the price widget's
 * volume/mass/count units) still narrow it themselves.
 */
export interface UnitOption {
    label: string;
    value: string;
}

export function useUnitOptions() {
    const allUnitOptions = computed<UnitOption[]>(() => {
        const seen = new Set<string>();
        const out: UnitOption[] = [];
        for (const def of Object.values(UNIT_TABLE)) {
            if (seen.has(def.canonical)) continue;
            seen.add(def.canonical);
            out.push({ label: def.canonical, value: def.canonical });
        }
        out.sort((a, b) => a.label.localeCompare(b.label));
        return out;
    });

    /** The filtered list a `q-select` renders. Starts as the full vocabulary. */
    const unitOptions = ref<UnitOption[]>([...allUnitOptions.value]);

    /** `@filter` handler — matches against every alias, not just the canonical
     *  form, so a typed-out unit name finds its abbreviation. */
    function onUnitFilter(query: string, update: (cb: () => void) => void): void {
        update(() => {
            const q = query.trim().toLowerCase();
            if (!q) {
                unitOptions.value = [...allUnitOptions.value];
                return;
            }
            const matches = new Set<string>();
            for (const [alias, def] of Object.entries(UNIT_TABLE)) {
                if (alias.toLowerCase().includes(q) || def.canonical.toLowerCase().includes(q)) {
                    matches.add(def.canonical);
                }
            }
            unitOptions.value = allUnitOptions.value.filter((o) => matches.has(o.value));
        });
    }

    return { allUnitOptions, unitOptions, onUnitFilter };
}
