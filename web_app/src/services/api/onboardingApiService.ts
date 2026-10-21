import type {
    OnboardingCatalog,
    OnboardingState,
    SeedDemoResult,
    SeedItemsRequest,
    SeedItemsResult,
    SeedRequest,
    SeedResult,
} from 'src/models/onboarding';
import AxiosHttpClient from './axiosHttpClient';

export default class OnboardingApiService {
    private httpClient = new AxiosHttpClient();

    getStateAsync = async (): Promise<OnboardingState> =>
        await this.httpClient.get<OnboardingState>('/onboarding/state');

    completeAsync = async (): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>(
            '/onboarding/complete',
            {},
        );

    restartAsync = async (): Promise<void> =>
        await this.httpClient.post<void, Record<string, never>>(
            '/onboarding/restart',
            {},
        );

    seedAsync = async (request: SeedRequest): Promise<SeedResult> =>
        await this.httpClient.post<SeedResult, SeedRequest>(
            '/onboarding/seed',
            request,
        );

    getCatalogAsync = async (): Promise<OnboardingCatalog> =>
        await this.httpClient.get<OnboardingCatalog>('/onboarding/catalog');

    seedItemsAsync = async (request: SeedItemsRequest): Promise<SeedItemsResult> =>
        await this.httpClient.post<SeedItemsResult, SeedItemsRequest>(
            '/onboarding/seed-items',
            request,
        );

    /** FU-194 — opt-in demo dataset (one recipe + the StockItems it needs + a
     *  current-week MealPlan with one entry). Idempotent server-side: a
     *  second call returns `seeded: false` if the demo recipe already exists. */
    seedDemoAsync = async (): Promise<SeedDemoResult> =>
        await this.httpClient.post<SeedDemoResult, Record<string, never>>(
            '/onboarding/seed-demo',
            {},
        );
}
