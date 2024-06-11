import AxiosHttpClient from "./AxiosHttpClient";

export default class HealthApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient(5170);
        this.mapiHttpClient = new AxiosHttpClient(5172);
    }

    healthCheckAsync = async (): Promise<boolean> => {
        const dapiOkay = await this.dapiHttpClient.get<boolean>('/health').catch(() => false);
        const mapiOkay = await this.mapiHttpClient.get<boolean>('/health').catch(() => false);

        return dapiOkay && mapiOkay
    }
}
