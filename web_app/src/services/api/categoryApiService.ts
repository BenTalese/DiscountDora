import type { Category } from 'src/models/recipeVocab';
import AxiosHttpClient from './axiosHttpClient';

export type CreateCategoryCommand = { name: string };
export type UpdateCategoryCommand = { name: string };

export default class CategoryApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<Category[]> =>
        await this.httpClient.get<Category[]>('/categories');

    createAsync = async (
        command: CreateCategoryCommand,
    ): Promise<{ category_id: string }> =>
        await this.httpClient.post<{ category_id: string }, CreateCategoryCommand>(
            '/categories',
            command,
        );

    updateAsync = async (id: string, command: UpdateCategoryCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateCategoryCommand>(`/categories/${id}`, command);

    deleteAsync = async (id: string): Promise<{ recipes_affected: number }> =>
        await this.httpClient.delete<{ recipes_affected: number }>(`/categories/${id}`);
}
