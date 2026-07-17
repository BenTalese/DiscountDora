import { expect, type Page, type APIResponse } from '@playwright/test';

/** Read the double-submit CSRF cookie (FU-197) from the page's context.
 *  Mutating API calls made via `page.request` bypass the SPA's axios
 *  interceptor, so specs must attach the header themselves — exactly the
 *  contract FU-571 pinned for the app's own raw-fetch callers. */
export async function csrfHeader(page: Page): Promise<Record<string, string>> {
    const cookies = await page.context().cookies();
    const token = cookies.find((c) => c.name === 'dora_csrf')?.value;
    return token ? { 'X-CSRF-Token': token } : {};
}

/** Authenticated JSON mutation through the page's cookie jar + CSRF header.
 *  For engineering test state the UI can't create directly (list lines,
 *  level resets) — assertions should still go through the UI. */
export async function apiMutate(
    page: Page,
    method: 'post' | 'patch' | 'delete',
    path: string,
    body?: unknown,
): Promise<APIResponse> {
    const headers = {
        'Content-Type': 'application/json',
        ...(await csrfHeader(page)),
    };
    const res = await page.request[method](`/api${path}`, {
        headers,
        ...(body === undefined ? {} : { data: body }),
    });
    expect(
        res.ok(),
        `${method.toUpperCase()} /api${path} → ${res.status()}`,
    ).toBe(true);
    return res;
}

/** Authenticated GET returning parsed JSON. */
export async function apiGet<T = unknown>(page: Page, path: string): Promise<T> {
    const res = await page.request.get(`/api${path}`);
    expect(res.ok(), `GET /api${path} → ${res.status()}`).toBe(true);
    return (await res.json()) as T;
}

/** The bottom-right Quasar toast containing `text`. */
export function toast(page: Page, text: string | RegExp) {
    return page.locator('.q-notification').filter({ hasText: text });
}
