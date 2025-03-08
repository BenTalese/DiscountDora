export default class NotImplementedError extends Error {
    constructor(message: string = '') {
        super(message);
    }
}

// For memory efficiency, an object prototype,
// should be used for properties/methods that
// are shared across every instance of the object.
NotImplementedError.prototype.name = 'NotImplementedError';
