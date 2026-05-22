import type {
    OnboardingState,
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
}
