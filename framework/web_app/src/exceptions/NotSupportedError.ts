export default class NotSupportedError extends Error {

    constructor(message: string = ''){
        super(message)

        this.name = 'NotSupportedError';
    }

}
