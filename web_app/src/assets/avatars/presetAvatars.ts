/**
 * Pre-made profile pictures — generic food art a user can pick instead of
 * uploading a photo (owner ask 2026-10-17: onboarding's welcome step and
 * Settings → Account both offer them).
 *
 * The art is Microsoft's Fluent Emoji (3D set), MIT-licensed — the licence
 * text ships beside the PNGs (`LICENSE-fluentui-emoji.txt`) and the credit is
 * shown in Settings → About. Keep both if the set changes.
 *
 * Each preset carries a soft backdrop colour. The PNGs are transparent, and a
 * profile picture is stored as an encoded image (not a preset key), so the
 * backdrop is baked into the picture when it's picked — see
 * `renderPresetAvatar`. These hexes are image content, not UI chrome, which is
 * why they don't come from the theme tokens (R-002 carve-out: a stored picture
 * can't follow a theme switch, so it mustn't be painted from one).
 */

export type PresetAvatar = {
    key: string;
    label: string;
    src: string;
    backdrop: string;
};

const FILES = import.meta.glob<string>('./*.png', {
    eager: true,
    query: '?url',
    import: 'default',
});

function src(key: string): string {
    return FILES[`./${key}.png`] ?? '';
}

const DEFS: readonly { key: string; label: string; backdrop: string }[] = [
    { key: 'avocado', label: 'Avocado', backdrop: '#e3f1d4' },
    { key: 'red_apple', label: 'Apple', backdrop: '#fbe0dc' },
    { key: 'lemon', label: 'Lemon', backdrop: '#fdf3c4' },
    { key: 'strawberry', label: 'Strawberry', backdrop: '#fde1e6' },
    { key: 'watermelon', label: 'Watermelon', backdrop: '#dff3e2' },
    { key: 'carrot', label: 'Carrot', backdrop: '#fde7d2' },
    { key: 'broccoli', label: 'Broccoli', backdrop: '#dcefd9' },
    { key: 'hot_pepper', label: 'Chilli', backdrop: '#fde0d8' },
    { key: 'cheese_wedge', label: 'Cheese', backdrop: '#fdf0c8' },
    { key: 'croissant', label: 'Croissant', backdrop: '#f8e8d2' },
    { key: 'pancakes', label: 'Pancakes', backdrop: '#f9ead6' },
    { key: 'doughnut', label: 'Doughnut', backdrop: '#fbe1ec' },
    { key: 'cupcake', label: 'Cupcake', backdrop: '#ece3f8' },
    { key: 'pizza', label: 'Pizza', backdrop: '#fde8d0' },
    { key: 'taco', label: 'Taco', backdrop: '#fcefd0' },
    { key: 'sushi', label: 'Sushi', backdrop: '#e0eef4' },
    { key: 'steaming_bowl', label: 'Noodles', backdrop: '#e6edf8' },
    { key: 'cooking', label: 'Fried egg', backdrop: '#e4e9ee' },
];

export const PRESET_AVATARS: readonly PresetAvatar[] = DEFS
    .map((d) => ({ ...d, src: src(d.key) }))
    .filter((p) => p.src !== '');

/** Size of the encoded picture. Matches what an uploaded avatar is shrunk to
 *  in practice; the art itself is 256px, so 256 keeps it crisp. */
const RENDER_PX = 256;

function loadImage(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('Could not load that picture.'));
        img.src = url;
    });
}

/**
 * Bake a preset into a profile-picture data URL: the backdrop as a full
 * square (every avatar surface crops to a circle), the art centred at ~70%
 * so it sits inside the crop. Returned as a PNG data URL — the same shape
 * `processImageFile` hands the upload paths, so it saves through the
 * existing `image` field with no server change.
 */
export async function renderPresetAvatar(preset: PresetAvatar): Promise<string> {
    const img = await loadImage(preset.src);
    const canvas = document.createElement('canvas');
    canvas.width = RENDER_PX;
    canvas.height = RENDER_PX;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not draw that picture (canvas unavailable).');
    ctx.fillStyle = preset.backdrop;
    ctx.fillRect(0, 0, RENDER_PX, RENDER_PX);
    const art = Math.round(RENDER_PX * 0.7);
    const offset = Math.round((RENDER_PX - art) / 2);
    ctx.drawImage(img, offset, offset, art, art);
    return canvas.toDataURL('image/png');
}
