import { ICONS } from 'src/style/icons';
import { Notify } from 'quasar';

// See possible options: https://quasar.dev/quasar-plugins/notify/

Notify.setDefaults({});

// Visual defaults only — callers always supply their own `message` (and
// optional `caption`) at the call site. Setting message/caption defaults
// here makes them silent fallbacks for any miswired call, which is how
// "I'm a notification!" reached production (B7).
// D-002 / B7 — `info` used to declare `color: 'blue'` + `iconColor: 'amber'`.
// Those are Quasar *Material palette literals* (#2196f3 / #ffc107), not Dora
// tokens, so this was the one toast in the app that ignored the theme
// entirely: `themeService` re-points `--q-info`/`--q-positive`/`--q-negative`
// at the active palette on every theme change, and `bg-blue` never consults
// it. The result was a saturated library-default banner with a bullhorn on it,
// firing from 24 call sites as ordinary as "Swap undone."
//
// No `color`/`textColor`/`iconColor` here on purpose — B7 says info is the
// *neutral* kind (success and error carry the semantic fill; info doesn't
// earn one). Those props would each emit a `bg-*`/`text-*` palette class, so
// the styling lives in `.dora-toast--info` (app.scss) where it can read the
// surface/text tokens and follow the theme like every other surface.
Notify.registerType('info', {
    icon: ICONS.info_outline,
    iconSize: '24px',
    progress: true,
    classes: 'dora-toast--info'
});

// `negative` is a Quasar palette *key*, not a literal — `themeService` maps it
// to `--semantic-negative`, so this one already follows the theme. `white` is
// the on-negative colour Quasar itself uses for the message text; there is no
// `--text-on-negative` token to point at, so it stays a literal by necessity.
Notify.registerType('oopsie', {
    color: 'negative',
    message: 'Oops, something went wrong...',
    icon: ICONS.error,
    iconColor: 'white',
    iconSize: '30px',
    progress: true,
    timeout: 3000
});
