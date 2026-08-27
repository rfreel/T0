export type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });

export const err = <E>(error: E): Result<never, E> => ({ ok: false, error });

export const mapResult = <T, U, E>(
  input: Result<T, E>,
  mapper: (value: T) => U,
): Result<U, E> => (input.ok ? ok(mapper(input.value)) : input);
