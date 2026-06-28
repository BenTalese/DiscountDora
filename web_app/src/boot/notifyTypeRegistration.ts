import { ICONS } from 'src/style/icons';
import { Notify } from 'quasar';

// See possible options: https://quasar.dev/quasar-plugins/notify/

Notify.setDefaults({});

// Visual defaults only — callers always supply their own `message` (and
// optional `caption`) at the call site. Setting message/caption defaults
// here makes them silent fallbacks for any miswired call, which is how
// "I'm a notification!" reached production (B7).
Notify.registerType('info', {
    color: 'blue',
    textColor: 'white',
    icon: ICONS.announcement,
    iconColor: 'amber',
    iconSize: '30px',
    progress: true,
    classes: 'flat'
});

Notify.registerType('oopsie', {
    color: 'negative',
    message: 'Oops, something went wrong...',
    icon: ICONS.error,
    iconColor: 'white',
    iconSize: '30px',
    progress: true,
    timeout: 3000
});
