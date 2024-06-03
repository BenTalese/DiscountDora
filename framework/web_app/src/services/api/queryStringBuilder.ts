export enum FilterOperator {
    EQUAL = 'eq',
    LESS_THAN = 'lt',
    GREATER_THAN = 'gt',
    LESS_THAN_OR_EQUAL = 'le',
    GREATER_THAN_OR_EQUAL = 'ge',
    NOT_EQUAL = 'ne'
}

export enum SortOrder {
    ASCENDING = 'asc',
    DESCENDING = 'desc'
}

interface FilterOperation {
    field: string;
    operator: FilterOperator;
    value: any;
}

interface SortOperation {
    field: string;
    order?: SortOrder;
}

interface PaginationOperation {
    page: number;
    limit: number;
}

function createFilterString(filters: FilterOperation[]): string {
    return filters.map(filter => `filter=${filter.field}:${filter.operator}:${filter.value}`).join('&');
}

function createSortString(sort: SortOperation): string {
    return `sort=${sort.field}${sort.order ? `:${sort.order}` : ':asc'}`;
}

function createPaginationString(pagination: PaginationOperation): string {
    return `page=${pagination.page}&limit=${pagination.limit}`;
}

/**
 * Generates a complete query string with filters, sorting, and pagination.
 * @param filters An optional array of `FilterOperation` objects.
 * @param sort An optional `SortOperation` object.
 * @param pagination An optional `PaginationOperation` object.
 * @returns A query string combining filters, sorting, and pagination parameters.
 * @example
 * const filters: FilterOperation[] = [
 *     { field: 'stock_item_id', operator: FilterOperator.EQUAL, value: 12345 },
 *     { field: 'age', operator: FilterOperator.GREATER_THAN, value: 18 }
 * ];
 * const sort: SortOperation = { field: 'age_or_something', order: SortOrder.ASCENDING };
 * const pagination: PaginationOperation = { page: 1, limit: 10 };
 * const queryString = createQueryString(filters, sort, pagination);
 *
 * Output: "filter=stock_item_id:eq:12345&filter=age:gt:18&sort=age_or_something:asc&page=1&limit=10"
 */
export function createQueryString(
    filters?: FilterOperation[],
    sort?: SortOperation,
    pagination?: PaginationOperation
): string {
    const _Parts: string[] = [];

    if (filters && filters.length > 0) {
        _Parts.push(createFilterString(filters));
    }

    if (sort) {
        _Parts.push(createSortString(sort));
    }

    if (pagination) {
        _Parts.push(createPaginationString(pagination));
    }

    return _Parts.join('&');
}
