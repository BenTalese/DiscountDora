import { describe, expect, it } from 'vitest';
import { compareByCostPerServing } from 'src/helpers/recipeCostSort';
import type { Recipe } from 'src/models/recipe';

function recipe(name: string, costPerServing: number | null): Recipe {
    return { name, estimated_cost_per_serving: costPerServing } as unknown as Recipe;
}

function order(recipes: Recipe[]): string[] {
    return [...recipes].sort((a, b) => compareByCostPerServing(a, b)).map((r) => r.name);
}

describe('compareByCostPerServing', () => {
    it('ranks cheapest first', () => {
        expect(order([recipe('Dear', 9), recipe('Cheap', 2), recipe('Mid', 5)]))
            .toEqual(['Cheap', 'Mid', 'Dear']);
    });

    it('sinks recipes with no figure, whichever side they start on', () => {
        expect(order([recipe('Unpriced', null), recipe('Priced', 5)]))
            .toEqual(['Priced', 'Unpriced']);
        expect(order([recipe('Priced', 5), recipe('Unpriced', null)]))
            .toEqual(['Priced', 'Unpriced']);
    });

    it('breaks ties by name — including between two unpriced recipes', () => {
        expect(order([recipe('B', 4), recipe('A', 4)])).toEqual(['A', 'B']);
        expect(order([recipe('B', null), recipe('A', null)])).toEqual(['A', 'B']);
    });

    it('reverses on a negative direction sign, and nulls still sink', () => {
        const sorted = [recipe('Cheap', 2), recipe('Unpriced', null), recipe('Dear', 9)]
            .sort((a, b) => compareByCostPerServing(a, b, -1))
            .map((r) => r.name);

        expect(sorted).toEqual(['Dear', 'Cheap', 'Unpriced']);
    });
});
