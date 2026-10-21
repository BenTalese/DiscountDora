/** Discount percentage (0–100) when on special, else null. Accepts anything
 *  with `price_now`/`price_was` (a saved Product, a historic offer, etc) so
 *  the one rule serves every surface.
 *
 *  Survives the Phase D decommission as the only piece of the old
 *  scraped-offer logic still used (by DashboardPage's best-deals card). The
 *  filename is retained to keep the import path stable; once a clearer home
 *  is picked we can rename without churn here.
 */
export function discountPercent(offer: { price_now: number; price_was: number }): number | null {
    if (offer.price_was <= 0 || offer.price_now <= 0 || offer.price_now >= offer.price_was) {
        return null;
    }
    return Math.round(((offer.price_was - offer.price_now) / offer.price_was) * 100);
}
