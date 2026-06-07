import AxiosHttpClient from './axiosHttpClient';

/** Shape of GET /api/health from dora_api. Mobile + desktop clients
 *  use this to detect incompatible backend versions and to gate
 *  feature-specific UI on what the backend has enabled. Adding new
 *  fields is fine; removing fields is a breaking change for clients
 *  built against older shapes. */
export interface HealthInfo {
    ok: boolean;
    version: string;
    schema_version: string | null;
    profile: string;
    features: {
        auth: boolean;
        audit: boolean;
        scanning: boolean;
        multi_user: boolean;
        email: boolean;
        assistant: boolean;
        // Open shape — later additions like `reports`, `substitutes`
        // can land without breaking existing clients.
        [key: string]: boolean;
    };
}

export default class HealthApiService {
    private dapiHttpClient: AxiosHttpClient;
    private mapiHttpClient: AxiosHttpClient;

    constructor() {
        this.dapiHttpClient = new AxiosHttpClient('dora');
        this.mapiHttpClient = new AxiosHttpClient('merchant');
    }

    /** Used by the boot path. Returns true when *both* APIs answer.
     *  Doesn't care about the JSON shape — any 2xx is "alive". */
    healthCheckAsync = async (): Promise<boolean> => {
        const dapiOkay = await this.dapiHttpClient
            .get<HealthInfo | boolean>('/health').then(() => true).catch(() => false);
        const mapiOkay = await this.mapiHttpClient
            .get<boolean>('/health').then(() => true).catch(() => false);
        return dapiOkay && mapiOkay;
    };

    /** Fetch the full dora_api health payload for compatibility +
     *  feature-gating decisions. Throws on network error so callers
     *  can decide how to surface it (mobile onboarding shows a
     *  clearer "couldn't reach server" rather than silent false). */
    getInfoAsync = async (): Promise<HealthInfo> => {
        return await this.dapiHttpClient.get<HealthInfo>('/health');
    };
}
