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
    // FU-345 — install-wide image compression knobs the client applies
    // at upload time. Optional in the type because older backends won't
    // emit it; callers default to 85 / 1920.
    image_policy?: {
        quality: number;         // 30–100
        max_dimension: number;   // longest edge in px
    };
}

export default class HealthApiService {
    private httpClient = new AxiosHttpClient();

    /** Boot probe. Any 2xx from dora_api is "alive". */
    healthCheckAsync = async (): Promise<boolean> => {
        return await this.httpClient
            .get<HealthInfo | boolean>('/health')
            .then(() => true)
            .catch(() => false);
    };

    /** Fetch the full health payload for compatibility + feature gating. */
    getInfoAsync = async (): Promise<HealthInfo> => {
        return await this.httpClient.get<HealthInfo>('/health');
    };
}
