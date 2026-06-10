import { Screen } from 'quasar';

// Activates Quasar's Screen plugin. Without this call, $q.screen.width is 0
// and every breakpoint flag (gt.sm, lt.md, …) returns false regardless of
// the actual viewport — which silently breaks any component that branches
// on viewport size. Calling setDebounce attaches the resize listener and
// triggers an initial measurement.
Screen.setDebounce(100);
