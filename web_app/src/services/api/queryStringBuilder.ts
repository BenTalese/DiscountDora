export enum FilterOperator {
    EQUAL = 'eq',
    NOT_EQUAL = 'ne',
    LESS_THAN = 'lt',
    GREATER_THAN = 'gt',
    LESS_THAN_OR_EQUAL = 'le',
    GREATER_THAN_OR_EQUAL = 'ge',
    CONTAINS = 'ct'
}

export enum SortOrder {
    ASCENDING = 'asc',
    DESCENDING = 'desc'
}

export interface FilterOperation {
    field: string;
    operator: FilterOperator;
    value: string | number | boolean;
}

export interface SortOperation {
    field: string;
    order?: SortOrder;
}

export interface PaginationOperation {
    page: number;
    limit: number;
}

export interface Page<T> {
    items: T[];
    total: number;
    page: number;
    limit: number;
}

/**
 * Builds a `?filter=...&filter=...&sort=field:asc&page=1&limit=50` query
 * string against list endpoints. Returns the leading "?" or an empty string.
 */
export function createQueryString(
    filters?: FilterOperation[],
    sort?: SortOperation,
    pagination?: PaginationOperation
): string {
    const params = new URLSearchParams();

    if (filters) {
        for (const f of filters) {
            params.append('filter', `${f.field}:${f.operator}:${f.value}`);
        }
    }
    if (sort) {
        params.set('sort', `${sort.field}:${sort.order ?? SortOrder.ASCENDING}`);
    }
    if (pagination) {
        params.set('page', String(pagination.page));
        params.set('limit', String(pagination.limit));
    }

    const qs = params.toString();
    return qs.length > 0 ? `?${qs}` : '';
}
