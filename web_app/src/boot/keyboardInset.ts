// Keeps dialogs above the on-screen keyboard (owner, 2026-09-27: *"the dialogs
// that pop up from below look good however on mobile the keyboard always hides
// them"*).
//
// Two platforms, two mechanisms:
// - Android Chrome honours `interactive-widget=resizes-content` in the viewport
//   meta (index.html): the layout viewport shrinks with the keyboard, so a
//   fixed-position dialog already ends above it and both insets below read 0.
// - iOS Safari ignores that key. The keyboard shrinks only the *visual*
//   viewport, and a `position: fixed` dialog stays pinned to the layout
//   viewport's bottom edge, behind the keyboard. The gap between the two is
//   published here as `--vv-inset-top` / `--vv-inset-bottom`, and `app.scss`
//   pads `.q-dialog__inner` by them so every dialog (bottom sheet or centred,
//   `BaseDialog` or a raw `q-dialog`) lays out inside what is actually visible.
//
// One listener for the whole app rather than one per dialog: the fact is about
// the viewport, not about any dialog.
export default () => {
    const vv = window.visualViewport;
    if (!vv) return;
    const root = document.documentElement.style;
    let frame = 0;
    const update = () => {
        frame = 0;
        const top = Math.max(0, vv.offsetTop);
        const bottom = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
        root.setProperty('--vv-inset-top', `${Math.round(top)}px`);
        root.setProperty('--vv-inset-bottom', `${Math.round(bottom)}px`);
    };
    const schedule = () => {
        if (!frame) frame = requestAnimationFrame(update);
    };
    vv.addEventListener('resize', schedule);
    vv.addEventListener('scroll', schedule);
    update();
};
