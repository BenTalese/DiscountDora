export default class NotSupportedError extends Error {

    constructor(message: string = ''){
        super(message)
    };

}

NotSupportedError.prototype.name = 'NotSupportedError';
