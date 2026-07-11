/**
 * Auth token bridge — Clerk (or other providers) register a getter;
 * apiFetch attaches Bearer when present.
 */

type TokenGetter = () => Promise<string | null>;

let tokenGetter: TokenGetter | null = null;

export function setAuthTokenGetter(getter: TokenGetter | null): void {
  tokenGetter = getter;
}

export async function getAuthToken(): Promise<string | null> {
  if (!tokenGetter) return null;
  try {
    return await tokenGetter();
  } catch {
    return null;
  }
}
