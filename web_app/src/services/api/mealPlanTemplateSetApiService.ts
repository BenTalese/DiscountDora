import type {
    MealPlanTemplateSetDetail,
    MealPlanTemplateSetSummary,
} from 'src/models/mealPlanTemplateSet';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';

export type CreateMealPlanTemplateSetCommand = {
    name: string;
    description?: string;
    /** Templates in rotation order. */
    template_ids: string[];
};

export type UpdateMealPlanTemplateSetCommand = {
    name?: string;
    description?: string;
    /** When present, fully replaces the ordered item list. */
    template_ids?: string[];
};

export default class MealPlanTemplateSetApiService {
    private httpClient = new AxiosHttpClient('dora');

    getAllAsync = async (): Promise<MealPlanTemplateSetSummary[]> =>
        await this.httpClient.get<MealPlanTemplateSetSummary[]>('/meal-plan-template-sets');

    getDetailAsync = async (id: string): Promise<MealPlanTemplateSetDetail> =>
        await this.httpClient.get<MealPlanTemplateSetDetail>(`/meal-plan-template-sets/${id}`);

    createAsync = async (command: CreateMealPlanTemplateSetCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/meal-plan-template-sets', command);

    updateAsync = async (id: string, command: UpdateMealPlanTemplateSetCommand): Promise<void> =>
        await this.httpClient.patch<void>(`/meal-plan-template-sets/${id}`, command);

    deleteAsync = async (id: string): Promise<void> =>
        await this.httpClient.delete(`/meal-plan-template-sets/${id}`);
}
