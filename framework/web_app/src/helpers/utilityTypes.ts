/**
 * Makes all properties on T required, excluding K.
 * Example: PartialWithRequired<Test, 'bar' | 'foo'>
 * Reference: https://github.com/Microsoft/TypeScript/issues/25760#issuecomment-1250630403
 */
export type PartialWithRequired<T, K extends keyof T> = Pick<T, K> & Partial<T>;
