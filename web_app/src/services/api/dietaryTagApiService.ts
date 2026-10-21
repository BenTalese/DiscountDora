import type { DietaryTag } from 'src/models/recipeVocab';
import AxiosHttpClient from './axiosHttpClient';

export type CreateDietaryTagCommand = { name: string; category: string };
export type UpdateDietaryTagCommand = { name?: string; category?: string };

export default class DietaryTagApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<DietaryTag[]> =>
        await this.httpClient.get<DietaryTag[]>('/dietary-tags');

    createAsync = async (
        command: CreateDietaryTagCommand,
    ): Promise<{ dietary_tag_id: string }> =>
        await this.httpClient.post<{ dietary_tag_id: string }, CreateDietaryTagCommand>(
            '/dietary-tags',
            command,
        );

    updateAsync = async (id: string, command: UpdateDietaryTagCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateDietaryTagCommand>(`/dietary-tags/${id}`, command);

    deleteAsync = async (id: string): Promise<{ recipes_affected: number }> =>
        await this.httpClient.delete<{ recipes_affected: number }>(`/dietary-tags/${id}`);
}
