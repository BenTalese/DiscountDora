// Body/UI faces for the user's font preference (themeService FONT_FAMILY_CSS).
import '@fontsource-variable/nunito';
import '@fontsource-variable/nunito/wght-italic.css';
import '@fontsource-variable/urbanist';
import '@fontsource-variable/urbanist/wght-italic.css';
import '@fontsource-variable/inter';
import '@fontsource-variable/inter/opsz-italic.css';
import '@fontsource-variable/lexend';
import '@fontsource-variable/plus-jakarta-sans';
import '@fontsource-variable/plus-jakarta-sans/wght-italic.css';

// Fraunces — display face only (recipe titles + section labels on the
// redesigned recipe page). Deliberately NOT added to the font picker: the
// picker chooses the *body* face and this is never body text, so offering it
// there would let a user set every paragraph in a high-contrast display serif.
// `wght` only — the opsz/SOFT/WONK axes aren't used, so the extra files aren't
// downloaded.
import '@fontsource-variable/fraunces/wght.css';
