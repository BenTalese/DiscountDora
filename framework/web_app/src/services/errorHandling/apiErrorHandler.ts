import type { AxiosError } from 'axios';
import type { Ref } from 'vue';

export class ApiErrorResponse extends Error {
    errors!: Record<string, string[]>;
    status!: number;
    title!: string;
    type!: string;
}

const isDoraApiErrorResponse = (error: unknown): error is ApiErrorResponse =>
    error !== null &&
    typeof error === 'object' &&
    'errors' in error &&
    'status' in error &&
    'title' in error &&
    'type' in error;

export function mapApiErrorsToForm(errorResponse: AxiosError, formErrors: Ref<Record<string, string>>) {
    const errorData = errorResponse.response?.data;
    if (isDoraApiErrorResponse(errorData)) {
        Object.keys(formErrors).forEach((key) => {
            formErrors.value[key] = '';
        });

        Object.entries(errorData.errors).forEach(([key, message]) => {
            if (key in formErrors.value) {
                formErrors.value[key] = message.join(' ');
            } else {
                formErrors.value.noKey = message.join(' ');
            }
        });
    } else {
        throw errorResponse;
    }
}
