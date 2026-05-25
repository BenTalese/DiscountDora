import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export interface AuditEvent {
    audit_event_id: string;
    occurred_at: string;
    source: 'dapi' | 'mapi' | 'emailer' | 'web' | 'system';
    severity: 'debug' | 'info' | 'warn' | 'error' | 'audit';
    action: string;
    actor_user_id: string | null;
    actor_username: string | null;
    actor_ip: string | null;
    entity_type: string | null;
    entity_id: string | null;
    request_id: string | null;
    payload: unknown;
}

export interface AuditFilters {
    source?: string;
    severity?: string;       // comma-separated for multi-select
    actor_user_id?: string;
    action?: string;
    entity_type?: string;
    entity_id?: string;
    request_id?: string;
    occurred_from?: string;  // ISO
    occurred_to?: string;    // ISO
    page?: number;
    size?: number;
}

export default class AuditApiService {
    private httpClient = new AxiosHttpClient();

    listAsync = async (filters: AuditFilters): Promise<Page<AuditEvent>> => {
        const params = new URLSearchParams();
        for (const [key, value] of Object.entries(filters)) {
            if (value === undefined || value === null || value === '') continue;
            params.set(key, String(value));
        }
        const qs = params.toString();
        return await this.httpClient.get<Page<AuditEvent>>(
            `/audit/events${qs ? `?${qs}` : ''}`,
        );
    };

    getAsync = async (eventId: string): Promise<AuditEvent> =>
        await this.httpClient.get<AuditEvent>(`/audit/events/${encodeURIComponent(eventId)}`);
}
