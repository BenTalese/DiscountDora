import NullArgumentError from '../exceptions/NullArgumentError';
import NotImplementedError from '../exceptions/NotImplementedError';

/**
 * Retrieves the name of a property or method from a given selector function.
 * @param selector A function that selects a property or method from an object.
 * @returns The name of the selected property or method as a string.
 */
export const nameof = <TObject>(selector: (obj: TObject) => unknown): string => {

    if (!selector)
        throw new NullArgumentError('Selector');

    const selectorParts = selector.toString().split('.');

    if (selectorParts.length > 1)
        return selectorParts[selectorParts.length - 1];

    else
        throw new NotImplementedError('NameOf is only implemented for instance members, not for the instance itself. ');
};
