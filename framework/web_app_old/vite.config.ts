import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
    ],
    server: {
        port: 5174,
    },
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./app', import.meta.url))
        }
    }
});
