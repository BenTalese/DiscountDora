import AxiosHttpClient from './axiosHttpClient';

export type AppSettings = {
    llm_enabled: boolean;
    llm_base_url: string;
    llm_model: string;
    scanning_enabled: boolean;
};

export type UpdateAppSettingsCommand = Partial<AppSettings>;

export type ProbeResult = {
    reachable: boolean;
    models: string[];
    error: string | null;
};

export default class AppSettingsApiService {
    private httpClient = new AxiosHttpClient();

    getAsync = async (): Promise<AppSettings> =>
        await this.httpClient.get<AppSettings>('/app-settings');

    updateAsync = async (command: UpdateAppSettingsCommand): Promise<AppSettings> =>
        await this.httpClient.patch<AppSettings, UpdateAppSettingsCommand>('/app-settings', command);

    probeAsync = async (baseUrl: string): Promise<ProbeResult> =>
        await this.httpClient.post<ProbeResult, { base_url: string }>('/app-settings/probe', {
            base_url: baseUrl,
        });
}
