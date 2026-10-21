import type { Tool } from 'src/models/recipeVocab';
import AxiosHttpClient from './axiosHttpClient';

export type CreateToolCommand = { name: string };
export type UpdateToolCommand = { name: string };

export default class ToolApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<Tool[]> =>
        await this.httpClient.get<Tool[]>('/tools');

    createAsync = async (command: CreateToolCommand): Promise<{ tool_id: string }> =>
        await this.httpClient.post<{ tool_id: string }, CreateToolCommand>('/tools', command);

    updateAsync = async (id: string, command: UpdateToolCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateToolCommand>(`/tools/${id}`, command);

    deleteAsync = async (id: string): Promise<{ recipes_affected: number }> =>
        await this.httpClient.delete<{ recipes_affected: number }>(`/tools/${id}`);
}
