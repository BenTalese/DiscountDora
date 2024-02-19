/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { Axios } from 'axios'

export type HttpClientResponse<TResponse> = TResponse

export type CreatedResponse = {
    id: string;
}

export interface HttpClient {
    get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>
    post<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    put<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    patch<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>>
    delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>>
}

// TODO: Error logs
export default class AxiosHttpClient implements HttpClient {
    private axios: Axios

    constructor(port: number) {
        this.axios = axios.create({
            baseURL: `http://127.0.0.1:${port}/api`,
            headers: { 'Content-Type': 'application/json' }
        })
    }

    async get<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            const { data } = await this.axios.get<TResponse>(path)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async post<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            const { data } = await this.axios.post<TResponse>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error // TODO: Handle errors...
        }
    }

    async put<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            const { data } = await this.axios.put<TResponse>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async patch<TResponse = unknown, TBody = any>(path: string, body: TBody): Promise<HttpClientResponse<TResponse>> {
        try {
            const { data } = await this.axios.patch<TResponse>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async delete<TResponse = unknown>(path: string): Promise<HttpClientResponse<TResponse>> {
        try {
            const { data } = await this.axios.delete<TResponse>(path)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }
}
