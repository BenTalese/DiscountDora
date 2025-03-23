import type { Axios } from 'axios';
import axios from 'axios';

export type CreatedResponse = {
    id: string;
};

export type HttpClientResponse<TResponse> = TResponse;

export interface HttpClient {
    get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>;
    post<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    patch<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>;
    delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>;
}

export default class AxiosHttpClient implements HttpClient {
    private axios: Axios;

    constructor(port: number) {
        this.axios = axios.create({
            baseURL: `http://0.0.0.0:${port}/api`,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    async delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        return (await this.axios.delete<TResponse>(path)).data;
    }

    async get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        return (await this.axios.get<TResponse>(path)).data;
    }

    async patch<TResponse = unknown, TBody = unknown>(
        path: string,
        body: TBody
    ): Promise<HttpClientResponse<TResponse>> {
        return (await this.axios.patch<TResponse>(path, body)).data;
    }

    async post<TResponse = unknown, TBody = unknown>(
        path: string,
        body: TBody
    ): Promise<HttpClientResponse<TResponse>> {
        return (await this.axios.post<TResponse>(path, body)).data;
    }

    async put<TResponse = unknown, TBody = unknown>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        return (await this.axios.put<TResponse>(path, body)).data;
    }
}
