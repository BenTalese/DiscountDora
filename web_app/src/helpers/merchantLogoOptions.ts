import AldiLogo from 'src/components/AldiLogo.vue';
import ColesLogo from 'src/components/ColesLogo.vue';
import IgaLogo from 'src/components/IgaLogo.vue';
import WoolworthsLogo from 'src/components/WoolworthsLogo.vue';
import type { Component } from 'vue';

/** Backwards-compatible registry used by older callers of the product-search
 *  card footer. New code should use the `<MerchantLogo>` component, which
 *  handles case-insensitive lookup and an unknown-merchant fallback. */
const merchantLogoOptions: { [key: string]: Component } = {
    ALDI: AldiLogo,
    Aldi: AldiLogo,
    Coles: ColesLogo,
    IGA: IgaLogo,
    Iga: IgaLogo,
    Woolworths: WoolworthsLogo
};

export default merchantLogoOptions;
