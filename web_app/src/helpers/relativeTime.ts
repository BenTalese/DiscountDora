// Short "Nm ago / Nh ago / Nd ago / Nw ago / Nmo ago / Ny ago" relative-time
// formatter. Same shape used across stock-item detail, the observation list,
// and (FU-227 chunk 3) the YourPricesWidget — pulled out so the three call
// sites don't drift.
export function relativeTime(iso: string): string {
    if (!iso) return '';
    const diffMs = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diffMs / 60_000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    const weeks = Math.floor(days / 7);
    if (weeks < 5) return `${weeks}w ago`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months}mo ago`;
    return `${Math.floor(days / 365)}y ago`;
}
