export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const AUTH_COOKIE = "auth_session";
const ACTIVE_COMPANY_KEY = "active_company_id";

/**
 * Normaliza cualquier error capturado a un mensaje legible.
 */
export function errorMessage(error: unknown, fallback = "Error"): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

/**
 * Comprueba si existe la sesión mediante una cookie marcador no sensible.
 * El JWT real vive en una cookie HttpOnly que JavaScript no puede leer.
 */
export function isAuthenticated(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .map((part) => part.trim())
    .some((part) => part === `${AUTH_COOKIE}=1`);
}

/**
 * Cierra la sesión en el backend (borra la cookie HttpOnly) y elimina el marcador.
 */
export async function clearSession(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
      keepalive: true,
    });
  } catch {
    // Si falla la red, al menos se elimina el marcador local.
  } finally {
    if (typeof document !== "undefined") {
      const cookieDomain = process.env.COOKIE_DOMAIN;
      const domainPart = cookieDomain ? ` Domain=${cookieDomain}` : "";
      document.cookie = `${AUTH_COOKIE}=; Max-Age=0; path=/; SameSite=Lax${domainPart}`;
    }
  }
}

export function getActiveCompanyId(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(ACTIVE_COMPANY_KEY);
}

export function setActiveCompanyId(id: number | string | null): void {
  if (typeof window === "undefined") return;
  if (id === null || id === undefined) {
    sessionStorage.removeItem(ACTIVE_COMPANY_KEY);
  } else {
    sessionStorage.setItem(ACTIVE_COMPANY_KEY, String(id));
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type ApiOptions = {
  /** Un 401 redirige a /login salvo que se desactive (p. ej. en el propio login). */
  redirectOnUnauthorized?: boolean;
};

async function parseApiError(
  res: Response,
  redirectOnUnauthorized: boolean
): Promise<ApiError> {
  const text = await res.text();
  let detail: unknown;
  let isJson = false;
  try {
    const body = JSON.parse(text) as { detail?: unknown } | null;
    isJson = true;
    detail = body?.detail;
  } catch {
    // El cuerpo del error no es JSON.
  }

  let message = "";
  if (typeof detail === "string") {
    message = detail;
  } else if (Array.isArray(detail)) {
    const messages = detail
      .map((item: unknown) =>
        typeof item === "string" ? item : (item as { msg?: unknown })?.msg
      )
      .filter((msg): msg is string => typeof msg === "string");
    if (messages.length > 0) {
      message = messages.join("; ");
    }
  } else if (
    typeof detail === "object" &&
    detail !== null &&
    typeof (detail as { message?: unknown }).message === "string"
  ) {
    message = (detail as { message: string }).message;
  }

  if (!message) {
    message =
      (isJson ? "" : text.trim()) || res.statusText || `Error ${res.status}`;
  }

  if (
    res.status === 401 &&
    redirectOnUnauthorized &&
    typeof window !== "undefined"
  ) {
    const cookieDomain = process.env.COOKIE_DOMAIN;
    document.cookie = `${AUTH_COOKIE}=; Max-Age=0; path=/; SameSite=Lax${cookieDomain ? ` Domain=${cookieDomain}` : ""}`;
    // El lector vive fuera de React y no puede usar el router de Next.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
  }
  return new ApiError(message, res.status, detail);
}

export async function fetchApi(
  path: string,
  init: RequestInit = {},
  options: ApiOptions = {}
): Promise<Response> {
  const { redirectOnUnauthorized = true } = options;
  const activeCompanyId = getActiveCompanyId();
  const headers: Record<string, string> = {};
  if (activeCompanyId) {
    headers["X-Company-Id"] = activeCompanyId;
  }
  if (init.body && typeof init.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { ...headers, ...(init.headers as Record<string, string>) },
      credentials: "include",
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor", 0);
  }
  if (!res.ok) {
    throw await parseApiError(res, redirectOnUnauthorized);
  }
  return res;
}

export async function api(
  path: string,
  init: RequestInit = {},
  options: ApiOptions = {}
) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  const activeCompanyId = getActiveCompanyId();
  if (activeCompanyId) {
    headers["X-Company-Id"] = activeCompanyId;
  }
  const res = await fetchApi(path, { ...init, headers }, options);
  if (res.status === 204) return null;
  return res.json();
}
