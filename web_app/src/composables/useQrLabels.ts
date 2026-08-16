// Dora's own per-item QR labels — the single place the SPA talks to the
// `/stock-items/*/qr` endpoints.
//
// Why this exists: the QR image and the print sheet used to be reached by a
// bare `<img src="…/qr">` and `window.open("…/qr/sheet")`. Both bypass the
// axios client, so neither carried the session the rest of the app uses —
// they relied on the browser volunteering the `dora_session` cookie on an
// unauthenticated subresource / top-level navigation, which it will not do
// once the SPA and the API are on different sites (and cannot do at all in
// the Capacitor shell, where the SPA origin is not the API origin). The
// result on the detail page was an empty QR dialog and a dead "Print one".
//
// Fetching through `AxiosHttpClient` and handing the browser a blob URL keeps
// exactly one auth path in the app. The sheet's QR images are inlined by the
// server as data: URIs (see `barcodes.py`) so the blob page is self-contained.
import AxiosHttpClient from 'src/services/api/axiosHttpClient';

const http = new AxiosHttpClient();

/** Blob URLs are revoked on a timer rather than immediately: the consumer is
 *  a just-opened window / an <img> that hasn't decoded yet. A minute is long
 *  past both, and short enough that a print session doesn't leak the pages. */
const BLOB_TTL_MS = 60_000;

function objectUrlFor(blob: Blob): string {
    const url = URL.createObjectURL(blob);
    setTimeout(() => URL.revokeObjectURL(url), BLOB_TTL_MS);
    return url;
}

/** PNG of one item's `dora://` label QR, as an object URL for `<img :src>`. */
export async function fetchQrImageUrlAsync(
    stockItemId: string,
    size = 512,
): Promise<string> {
    const blob = await http.getBlob(
        `/stock-items/${encodeURIComponent(stockItemId)}/qr?size=${size}`,
    );
    return objectUrlFor(blob);
}

/** Open the printable label sheet in a new tab.
 *  Omit `ids` to print every stock item (the server's "print all" shortcut). */
export async function openQrSheetAsync(options: {
    ids?: string[];
    layout?: string;
} = {}): Promise<void> {
    const params = new URLSearchParams();
    if (options.layout) params.set('layout', options.layout);
    if (options.ids && options.ids.length > 0) params.set('ids', options.ids.join(','));
    const query = params.toString();
    const html = await http.get<string>(
        `/stock-items/qr/sheet${query ? `?${query}` : ''}`,
    );
    const url = objectUrlFor(new Blob([html], { type: 'text/html' }));
    window.open(url, '_blank', 'noopener');
}
