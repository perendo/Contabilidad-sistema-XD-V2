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
      document.cookie = `${AUTH_COOKIE}=; Max-Age=0; path=/; SameSite=Lax`;
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

export async function api(path: string, init: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  const activeCompanyId = getActiveCompanyId();
  if (activeCompanyId) {
    headers["X-Company-Id"] = activeCompanyId;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}
