// Why the camera is (or isn't) usable on this device — one authority, so the
// scan overlay and the admin toggle that turns scanning on can't tell the user
// two different stories (R-003).
//
// The rule browsers enforce: `navigator.mediaDevices` is only exposed in a
// **secure context** — HTTPS, or a localhost origin. A self-hosted Dora reached
// at `http://192.168.1.20:5174` is neither, so the property is simply absent and
// any camera call throws "can't access property getUserMedia". That reads as a
// camera fault and isn't one, which is what the 2026-08-15 bug report was.
//
// The native app is NOT affected: Capacitor serves the bundled SPA from
// `https://localhost` (`androidScheme: "https"` in capacitor.config.json), which
// IS a secure context, and `allowMixedContent` lets it keep talking to a plain
// http backend. So on Android the camera works against any instance — which is
// the most useful thing we can tell someone stuck on the web version.

import { isNativePlatform } from 'src/services/api/backendUrl';

export type CameraAvailability =
    /** `navigator.mediaDevices` is present — go ahead and open the camera. */
    | { kind: 'available' }
    /** Non-secure origin. Fixable by the operator (HTTPS) or sidestepped (app). */
    | { kind: 'insecure-context'; message: string }
    /** Secure context, but the browser still exposes no camera API at all. */
    | { kind: 'unsupported'; message: string };

const INSECURE_MESSAGE =
    'Your browser only allows camera access over a secure connection, and this '
    + 'instance is being served over plain http. Two ways round it: use the '
    + 'Dashy Dora Android app, which can scan against any instance, or serve '
    + 'Dora over HTTPS. Typing a barcode below works either way.';

const UNSUPPORTED_MESSAGE =
    'This browser does not support camera access. Type a barcode below instead.';

export function getCameraAvailability(): CameraAvailability {
    if (navigator.mediaDevices?.getUserMedia !== undefined) {
        return { kind: 'available' };
    }
    // Native never lands here (its origin is secure), but if it somehow did,
    // "serve over HTTPS" would be nonsense advice — so route it to the plain
    // unsupported message.
    if (window.isSecureContext || isNativePlatform()) {
        return { kind: 'unsupported', message: UNSUPPORTED_MESSAGE };
    }
    return { kind: 'insecure-context', message: INSECURE_MESSAGE };
}

/** True when this install will refuse camera scanning for context reasons.
 *  Used by the admin toggle to warn at the point scanning is switched on,
 *  rather than letting the household discover it at the viewfinder. */
export function cameraBlockedByInsecureContext(): boolean {
    return getCameraAvailability().kind === 'insecure-context';
}
