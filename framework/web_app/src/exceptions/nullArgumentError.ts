export default class NullArgumentError extends Error {

    constructor(argument: string) {
        super(`${argument} cannot be null`);
    };

}

NullArgumentError.prototype.name = 'NullArgumentError';
