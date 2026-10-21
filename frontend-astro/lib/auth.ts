export type SessionStatus = "unknown" | "authenticated" | "anonymous" | "signing-in" | "signing-out";

export class AuthenticationRequiredError extends Error {}
export class SessionChangedError extends Error {}

let accessToken: string | null = null;
let sessionStatus: SessionStatus = "unknown";
let sessionVersion = 0;
let csrfPromise: Promise<string> | null = null;
let loginPromise: Promise<void> | null = null;
let refreshPromise: Promise<string> | null = null;
let logoutPromise: Promise<void> | null = null;
const listeners = new Set<() => void>();

function requireBrowser(): void {
  if (typeof window === "undefined") {
    throw new Error("La autenticación debe ejecutarse en el navegador.");
  }
}

function updateSession(token: string | null, status: SessionStatus): void {
  accessToken = token;
  if (sessionStatus !== status) {
    sessionStatus = status;
    listeners.forEach((listener) => listener());
  }
}

function assertCurrentSession(version: number): void {
  if (version !== sessionVersion) {
    throw new SessionChangedError("La sesión cambió. Volvé a intentarlo.");
  }
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getSessionStatus(): SessionStatus {
  return sessionStatus;
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

function getCsrfToken(): Promise<string> {
  if (!csrfPromise) {
    csrfPromise = (async () => {
      const response = await fetch("/api/v2/auth/csrf/", {
        credentials: "same-origin", cache: "no-store",
      });
      const data = await response.json().catch(() => null);
      if (!response.ok || typeof data?.csrf_token !== "string" || !data.csrf_token) {
        throw new Error("No se pudo preparar la solicitud. Intentá nuevamente.");
      }
      return data.csrf_token as string;
    })().finally(() => { csrfPromise = null; });
  }
  return csrfPromise;
}

async function authRequest(
  action: "login" | "refresh" | "logout",
  version: number,
  body?: { username: string; password: string },
): Promise<Response> {
  const csrf = await getCsrfToken();
  assertCurrentSession(version);
  const headers = new Headers({ "X-CSRFToken": csrf });
  if (body) headers.set("Content-Type", "application/json");
  return fetch(`/api/v2/auth/${action}/`, {
    method: "POST", credentials: "same-origin", cache: "no-store", headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

function readAccessToken(data: unknown): string {
  if (
    !data || typeof data !== "object" || !("access_token" in data) ||
    typeof data.access_token !== "string" || !data.access_token
  ) {
    throw new Error("No se pudo recuperar la sesión. Intentá nuevamente.");
  }
  return data.access_token;
}

export function login(username: string, password: string): Promise<void> {
  requireBrowser();
  if (sessionStatus === "signing-out" || loginPromise) {
    return Promise.reject(new Error("Esperá a que termine la operación de sesión."));
  }
  const previousRefresh = refreshPromise;
  const version = ++sessionVersion;
  updateSession(null, "signing-in");
  loginPromise = (async () => {
    try {
      await previousRefresh?.catch(() => undefined);
      const response = await authRequest("login", version, { username, password });
      const data = await response.json().catch(() => null);
      assertCurrentSession(version);
      if (!response.ok) throw new Error(data?.message ?? "No se pudo iniciar sesión.");
      updateSession(readAccessToken(data), "authenticated");
    } catch (error) {
      if (version === sessionVersion) updateSession(null, "anonymous");
      throw error;
    }
  })().finally(() => { loginPromise = null; });
  return loginPromise;
}

export function refreshAccessToken(): Promise<string> {
  requireBrowser();
  if (sessionStatus === "signing-out" || sessionStatus === "anonymous") {
    return Promise.reject(new AuthenticationRequiredError("Iniciá sesión para continuar."));
  }
  if (loginPromise) {
    return loginPromise.then(() => {
      if (!accessToken) throw new AuthenticationRequiredError("Iniciá sesión para continuar.");
      return accessToken;
    });
  }
  if (!refreshPromise) {
    const version = sessionVersion;
    refreshPromise = (async () => {
      const response = await authRequest("refresh", version);
      const data = await response.json().catch(() => null);
      assertCurrentSession(version);
      if (response.status === 401 || response.status === 403) {
        updateSession(null, "anonymous");
        throw new AuthenticationRequiredError("Iniciá sesión para continuar.");
      }
      if (!response.ok) throw new Error("No se pudo renovar la sesión. Intentá nuevamente.");
      const token = readAccessToken(data);
      updateSession(token, "authenticated");
      return token;
    })().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

export async function restoreSession(): Promise<void> {
  requireBrowser();
  if (sessionStatus !== "unknown") return;
  try {
    await refreshAccessToken();
  } catch (error) {
    if (!(error instanceof AuthenticationRequiredError)) throw error;
  }
}

export async function authenticatedFetch(
  path: string, options: RequestInit = {},
): Promise<Response> {
  requireBrowser();
  if (loginPromise) await loginPromise;
  const version = sessionVersion;
  let token = accessToken ?? await refreshAccessToken();
  const url = `/api/v2/${path.replace(/^\/+/, "")}`;
  async function send(currentToken: string): Promise<Response> {
    assertCurrentSession(version);
    const headers = new Headers(options.headers);
    headers.set("Authorization", `Bearer ${currentToken}`);
    const response = await fetch(url, {
      ...options, headers, credentials: "same-origin", cache: "no-store",
    });
    assertCurrentSession(version);
    return response;
  }
  let response = await send(token);
  if (response.status === 401) {
    token = accessToken && accessToken !== token ? accessToken : await refreshAccessToken();
    response = await send(token);
  }
  if (response.status === 401) {
    updateSession(null, "anonymous");
    throw new AuthenticationRequiredError("Iniciá sesión nuevamente para continuar.");
  }
  return response;
}

export function logout(): Promise<void> {
  requireBrowser();
  if (logoutPromise) return logoutPromise;
  const pending = [loginPromise, refreshPromise];
  const version = ++sessionVersion;
  updateSession(null, "signing-out");
  logoutPromise = (async () => {
    let completed = false;
    try {
      // Esperamos los Set-Cookie anteriores antes de revocar el refresh.
      await Promise.allSettled(pending);
      const response = await authRequest("logout", version);
      assertCurrentSession(version);
      if (!response.ok) throw new Error("No se pudo cerrar la sesión. Intentá nuevamente.");
      completed = true;
    } finally {
      if (version === sessionVersion) {
        updateSession(null, completed ? "anonymous" : "unknown");
      }
    }
  })().finally(() => { logoutPromise = null; });
  return logoutPromise;
}
