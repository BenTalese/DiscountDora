import type { RecipeCollection } from 'src/models/recipe';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type CreateRecipeCollectionCommand = { name: string };
export type UpdateRecipeCollectionCommand = { recipe_collection_id: string; name: string };

export default class RecipeCollectionApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient('dora');
    }

    createAsync = async (command: CreateRecipeCollectionCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/recipe-collections', command);

    deleteAsync = async (recipeCollectionId: string): Promise<void> =>
        await this.httpClient.delete(`/recipe-collections/${recipeCollectionId}`);

    getAllAsync = async (): Promise<Page<RecipeCollection>> =>
        await this.httpClient.get<Page<RecipeCollection>>('/recipe-collections');

    updateAsync = async (command: UpdateRecipeCollectionCommand): Promise<void> => {
        const { recipe_collection_id, ...payload } = command;
        await this.httpClient.patch<void>(`/recipe-collections/${recipe_collection_id}`, payload);
    };
}
