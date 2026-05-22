import AxiosHttpClient from './axiosHttpClient';

export default class HealthApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient('dora');
        this.mapiHttpClient = new AxiosHttpClient('merchant');
    }

    healthCheckAsync = async (): Promise<boolean> => {
        const dapiOkay = await this.dapiHttpClient.get<boolean>('/health').catch(() => false);
        const mapiOkay = await this.mapiHttpClient.get<boolean>('/health').catch(() => false);

        return dapiOkay && mapiOkay;
    };
}
