/** FU-189 — user-curated retail Store. */
export type Store = {
    store_id: string;
    name: string;
    has_image: boolean;
    /** `#rrggbb` majority colour of the uploaded logo, derived server-side at
     *  upload time. Null when there's no logo or it has no usable hue. */
    brand_colour: string | null;
};
