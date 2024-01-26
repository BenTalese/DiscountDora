import axios, { Axios } from 'axios'

export type HttpClientResponse<T> = T

export type CreatedResponse = {
    id: string;
}

export interface HttpClient {
    get<T = unknown>(path: string): Promise<HttpClientResponse<T>>
    post<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>>
    put<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>>
    patch<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>>
    delete<T = unknown>(path: string): Promise<HttpClientResponse<T>>
}

// TODO: Error logs
export default class AxiosHttpClient implements HttpClient {
    private axios: Axios

    constructor() {
        this.axios = axios.create({
            baseURL: "http://127.0.0.1:5170/api",
            headers: { 'Content-Type': 'application/json' }
        })
    }

    async get<T = unknown>(path: string): Promise<HttpClientResponse<T>> {
        try {
            const { data } = await this.axios.get<T>(path)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async post<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>> {
        try {
            const { data } = await this.axios.post<T>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error // TODO: Handle errors...
        }
    }

    async put<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>> {
        try {
            const { data } = await this.axios.put<T>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async patch<T = unknown>(path: string, body: any): Promise<HttpClientResponse<T>> {
        try {
            const { data } = await this.axios.patch<T>(path, body)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }

    async delete<T = unknown>(path: string): Promise<HttpClientResponse<T>> {
        try {
            const { data } = await this.axios.delete<T>(path)
            return data
        } catch (error) {
            console.error(error)
            throw error
        }
    }
}
