import type { Cuisine } from 'src/models/recipeVocab';
import AxiosHttpClient from './axiosHttpClient';

export type CreateCuisineCommand = { name: string };
export type UpdateCuisineCommand = { name: string };

export default class CuisineApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<Cuisine[]> =>
        await this.httpClient.get<Cuisine[]>('/cuisines');

    createAsync = async (
        command: CreateCuisineCommand,
    ): Promise<{ cuisine_id: string }> =>
        await this.httpClient.post<{ cuisine_id: string }, CreateCuisineCommand>(
            '/cuisines',
            command,
        );

    updateAsync = async (id: string, command: UpdateCuisineCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateCuisineCommand>(`/cuisines/${id}`, command);

    deleteAsync = async (id: string): Promise<{ recipes_affected: number }> =>
        await this.httpClient.delete<{ recipes_affected: number }>(`/cuisines/${id}`);
}
