// Password-policy constants shared by every surface that lets someone set a
// password (Account → Change password, Admin → Users → Add / Change password).
//
// R-003 note: the *authority* is the server — `auth_helpers.validate_password`
// checks length **and** a common-password blocklist, and is the only thing that
// can reject a save. These constants exist purely so the form can say "at least
// 8 characters" before the round-trip. Keeping them in one module means the
// number lives once on this side of the wire instead of once per form; the
// remaining cross-language duplication is tracked as FU-656 (publish the rule
// from `/auth/capabilities` and delete the literal).
export const MIN_PASSWORD_LENGTH = 8;

export const PASSWORD_HINT = `At least ${MIN_PASSWORD_LENGTH} characters`;

/** Client-side pre-check only — a `true` here still has to pass the server. */
export function passwordLongEnough(value: string): boolean {
    return value.length >= MIN_PASSWORD_LENGTH;
}
