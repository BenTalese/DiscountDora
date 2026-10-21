import AxiosHttpClient from './axiosHttpClient';

export type VersionInfo = {
    current_version: string;
    latest_version: string | null;
    update_available: boolean;
    release_url: string | null;
    error: string | null;
};

export type ChangelogEntry = {
    version: string;
    date: string | null;
    body: string;
};

export type ChangelogPayload = {
    entries: ChangelogEntry[];
};

export type FoodFact = { fact: string };

export default class HelpApiService {
    private httpClient = new AxiosHttpClient();

    getVersionAsync = async (): Promise<VersionInfo> =>
        await this.httpClient.get<VersionInfo>('/help/version');

    getChangelogAsync = async (): Promise<ChangelogPayload> =>
        await this.httpClient.get<ChangelogPayload>('/help/changelog');

    getFoodFactAsync = async (): Promise<FoodFact> =>
        await this.httpClient.get<FoodFact>('/help/food-fact');
}
