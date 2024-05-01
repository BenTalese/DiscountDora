import axios, { Axios, AxiosError } from 'axios';
import { Notify } from 'quasar';

class ApiErrorResponse extends Error {
    detail!: string;
    status!: number;
    errors!: Map<string, string>;
    title!: string;
    type!: string;
}

export type CreatedResponse = {
    id: string;
}

export type HttpClientResponse<TResponse> = TResponse

export interface HttpClient {
    get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>
    post<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    patch<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>
}

export default class AxiosHttpClient implements HttpClient {
    private axios: Axios

    constructor(port: number) {
        this.axios = axios.create({
            baseURL: `http://127.0.0.1:${port}/api`,
            headers: { 'Content-Type': 'application/json' }
        })
    }

    async delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.delete<TResponse>(path)).data
        } catch (error) {
            this.handleError(error as AxiosError)
        }
    }

    async get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.get<TResponse>(path)).data
        } catch (error) {
            this.handleError(error as AxiosError)
        }
    }

    private handleError(error: AxiosError): never {
        const apiError = error.response?.data as ApiErrorResponse;
        if (apiError) {
            console.error(`API ERROR :: STATUS CODE ${apiError.status} :: ${apiError.title} :: ${Object.values(apiError.errors).join(', ')}`);
        }
        else {
            console.error(`API ERROR :: ${error.name} :: ${error.message} :: ${error.config?.url}`);
        }
        Notify.create('Oops, something went wrong...') // TODO: Make specific responses for UI (also styling) (this may not be the place for that)
        throw error
    }

    async patch<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.patch<TResponse>(path, body)).data
        } catch (error) {
            this.handleError(error as AxiosError)
        }
    }

    async post<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.post<TResponse>(path, body)).data
        } catch (error) {
            this.handleError(error as AxiosError)
        }
    }

    async put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            return (await this.axios.put<TResponse>(path, body)).data
        } catch (error) {
            this.handleError(error as AxiosError)
        }
    }
}
