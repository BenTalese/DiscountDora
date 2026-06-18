declare namespace NodeJS {
    interface ProcessEnv {
        NODE_ENV: string;
        VUE_ROUTER_MODE: 'hash' | 'history' | 'abstract' | undefined;
        VUE_ROUTER_BASE: string | undefined;
    }
}

interface ImportMetaEnv {
    /** Base URL for the main Dora API (dora_api). Defaults to `<hostname>:5170/api`. */
    readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
