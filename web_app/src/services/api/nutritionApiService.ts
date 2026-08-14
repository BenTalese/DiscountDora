import AxiosHttpClient from './axiosHttpClient';

/** Where a food's numbers came from. Every lookup result carries one so the
 *  picker can badge it — three catalogues can disagree about a banana, and
 *  hiding which one answered would be dishonest (P3). */
export type NutritionSourceKind = 'dataset' | 'api' | 'web';

export interface NutritionSourceStatus {
    id: string;
    label: string;
    kind: NutritionSourceKind;
    /** Can this source answer a lookup right now? Derived server-side from
     *  installed reality (rows present / key set / network allowed), never
     *  from a stored flag. */
    available: boolean;
    food_count: number;
    /** Dataset sources only — transient import progress. */
    phase?: 'idle' | 'downloading' | 'parsing' | 'saving' | 'done' | 'error';
    error?: string | null;
    default_url?: string;
}

export interface NutritionSourcesResponse {
    mode: 'off' | 'simple' | 'complex';
    sources: NutritionSourceStatus[];
    any_available: boolean;
}

/** One candidate from the unified lookup. `id` is set only for foods already
 *  held locally; live suggestions carry null until the user confirms one and
 *  `resolveFoodAsync` persists it. */
export interface NutritionFoodResult {
    id: string | null;
    source: string;
    source_label: string;
    source_ref: string;
    name: string;
    brand: string | null;
    barcode: string | null;
    kcal_per_100g: number | null;
    protein_g_per_100g: number | null;
    carbs_g_per_100g: number | null;
    fat_g_per_100g: number | null;
    portions: { amount: number; measure: string; gram_weight: number }[];
    /** `barcode` when a typed EAN matched exactly, `name` otherwise. */
    match: 'barcode' | 'name';
    exact: boolean;
}

export interface NutritionLookupResponse {
    query: string;
    is_barcode: boolean;
    results: NutritionFoodResult[];
    sources_queried: string[];
    /** Sources that were asked but didn't answer. Surfaced rather than
     *  swallowed — "no results" and "one source is down" are different
     *  situations and the user deserves to know which they're in. */
    sources_failed: { source: string; error: string }[];
}

export default class NutritionApiService {
    private httpClient = new AxiosHttpClient();

    getSourcesAsync = async (): Promise<NutritionSourcesResponse> =>
        await this.httpClient.get<NutritionSourcesResponse>('/nutrition/sources');

    lookupAsync = async (query: string): Promise<NutritionLookupResponse> =>
        await this.httpClient.get<NutritionLookupResponse>(
            `/nutrition/lookup?q=${encodeURIComponent(query)}`,
        );

    /** Persist a picked live suggestion and get back the saved food. Only
     *  (source, source_ref) travels — the server re-fetches the values, so the
     *  client can't write arbitrary nutrition numbers. */
    resolveFoodAsync = async (
        source: string,
        sourceRef: string,
    ): Promise<{ id: string; name: string; source_label: string }> =>
        await this.httpClient.post<{ id: string; name: string; source_label: string }>(
            '/nutrition/foods/resolve',
            { source, source_ref: sourceRef },
        );

    /** Kick off a bulk dataset import. `url` overrides the built-in USDA
     *  release URL — needed when a release is superseded (the filename carries
     *  its date) or on an air-gapped install pointing at a local mirror. */
    startDatasetImportAsync = async (
        source: string,
        url?: string,
    ): Promise<NutritionSourcesResponse> =>
        await this.httpClient.post<NutritionSourcesResponse>(
            '/nutrition/datasets/import',
            url ? { source, url } : { source },
        );
}
