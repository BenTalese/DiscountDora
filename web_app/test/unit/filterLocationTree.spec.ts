// Pure-helper coverage — `filterLocationTree` backs the search box on the
// Stock locations settings page. The interesting behaviour is the two-way
// survival rule (a node lives if it matches OR has a matching descendant),
// which is easy to get subtly wrong and expensive to re-check by hand on a
// deep tree.
import { describe, expect, it } from 'vitest';

import { filterLocationTree } from 'src/helpers/locationDisplay';

type Node = { name: string; children: Node[] };

const n = (name: string, children: Node[] = []): Node => ({ name, children });

const tree: Node[] = [
    n('Pantry', [
        n('Top shelf', [n('Left'), n('Right')]),
        n('Bottom shelf', []),
    ]),
    n('Freezer', [n('Top drawer', [n('Middle')])]),
];

const names = (nodes: Node[]): string[] =>
    nodes.flatMap((node) => [node.name, ...names(node.children)]);

describe('filterLocationTree', () => {
    it('returns every node for an empty or whitespace query', () => {
        expect(filterLocationTree(tree, '')).toHaveLength(2);
        expect(filterLocationTree(tree, '   ')).toHaveLength(2);
    });

    it('does not hand back the caller its own array', () => {
        expect(filterLocationTree(tree, '')).not.toBe(tree);
    });

    it('keeps the ancestors of a deep match', () => {
        expect(names(filterLocationTree(tree, 'Left'))).toEqual([
            'Pantry',
            'Top shelf',
            'Left',
        ]);
    });

    it('keeps the whole subtree of a node that matches itself', () => {
        expect(names(filterLocationTree(tree, 'Top shelf'))).toEqual([
            'Pantry',
            'Top shelf',
            'Left',
            'Right',
        ]);
    });

    it('matches case-insensitively on a substring', () => {
        expect(names(filterLocationTree(tree, 'drAWer'))).toEqual([
            'Freezer',
            'Top drawer',
            'Middle',
        ]);
    });

    it('keeps every branch that matches, across roots', () => {
        expect(names(filterLocationTree(tree, 'top'))).toEqual([
            'Pantry',
            'Top shelf',
            'Left',
            'Right',
            'Freezer',
            'Top drawer',
            'Middle',
        ]);
    });

    it('returns nothing when no node matches', () => {
        expect(filterLocationTree(tree, 'garage')).toEqual([]);
    });

    it('leaves the source tree untouched', () => {
        filterLocationTree(tree, 'Left');
        expect(names(tree)).toHaveLength(8);
    });
});
