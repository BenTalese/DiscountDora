import type { MealSlot } from 'src/models/mealSlot';
import AxiosHttpClient from './axiosHttpClient';

// household-wide meal-slot vocabulary CRUD. Mirrors
// cuisineApiService, plus a reorder verb (slot order is user-facing).

export type CreateMealSlotCommand = { name: string };
export type UpdateMealSlotCommand = { name: string };
export type ReorderMealSlotsCommand = {
    slots: { meal_slot_id: string; sequence: number }[];
};

export default class MealSlotApiService {
    private httpClient = new AxiosHttpClient();

    getAllAsync = async (): Promise<MealSlot[]> =>
        await this.httpClient.get<MealSlot[]>('/meal-slots');

    createAsync = async (
        command: CreateMealSlotCommand,
    ): Promise<{ meal_slot_id: string }> =>
        await this.httpClient.post<{ meal_slot_id: string }, CreateMealSlotCommand>(
            '/meal-slots',
            command,
        );

    updateAsync = async (id: string, command: UpdateMealSlotCommand): Promise<void> =>
        await this.httpClient.patch<void, UpdateMealSlotCommand>(`/meal-slots/${id}`, command);

    reorderAsync = async (command: ReorderMealSlotsCommand): Promise<void> =>
        await this.httpClient.patch<void, ReorderMealSlotsCommand>('/meal-slots/reorder', command);

    deleteAsync = async (id: string): Promise<{ entries_affected: number }> =>
        await this.httpClient.delete<{ entries_affected: number }>(`/meal-slots/${id}`);
}
