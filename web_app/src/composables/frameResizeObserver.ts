/** A ResizeObserver whose callback runs on the next animation frame.
 *
 *  Every caller in the app measures an element and then writes layout from
 *  the result (an indicator's width, a chart's width). Writing layout inside
 *  the observer's own callback is what makes the browser report "ResizeObserver
 *  loop completed with undelivered notifications". Deferring the callback to
 *  the next frame lets the observation round finish first, and coalesces a
 *  burst of resizes into one measure.
 */
export interface FrameResizeObserver {
    observe(el: Element): void;
    disconnect(): void;
}

export function createFrameResizeObserver(callback: () => void): FrameResizeObserver {
    let frame: number | null = null;
    const observer = new ResizeObserver(() => {
        if (frame !== null) return;
        frame = requestAnimationFrame(() => {
            frame = null;
            callback();
        });
    });
    return {
        observe(el) {
            observer.observe(el);
        },
        disconnect() {
            observer.disconnect();
            if (frame !== null) {
                cancelAnimationFrame(frame);
                frame = null;
            }
        },
    };
}
