import assert from "node:assert/strict";
import { afterEach, beforeEach, test } from "node:test";

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
let moduleId = 0;
const freshAuth = () => import(new URL(`../lib/auth.ts?case=${moduleId++}`, import.meta.url));
const json = (data, status = 200) => Response.json(data, { status });
const tick = () => new Promise((resolve) => setImmediate(resolve));
function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
async function until(predicate) {
  for (let i = 0; i < 100 && !predicate(); i++) await tick();
  assert.ok(predicate(), "La petición esperada no se ejecutó.");
}
beforeEach(() => {
  globalThis.window = {};
  globalThis.fetch = async () => { throw new Error("Petición sin simular"); };
});
afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalWindow === undefined) delete globalThis.window;
  else globalThis.window = originalWindow;
});

test("no autentica en el servidor", async () => {
  const auth = await freshAuth();
  delete globalThis.window;
  assert.throws(() => auth.login("maria", "local"), /navegador/);
  assert.throws(() => auth.logout(), /navegador/);
  await assert.rejects(auth.authenticatedFetch("me/enrollments/"), /navegador/);
});

test("restauración anónima y login con CSRF notifican el estado compartido", async () => {
  const auth = await freshAuth();
  const changes = [];
  const unsubscribe = auth.subscribeSession(() => changes.push(auth.getSessionStatus()));
  globalThis.fetch = async (url, options) => {
    assert.equal(options.credentials, "same-origin");
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    assert.equal(new Headers(options.headers).get("X-CSRFToken"), "csrf-test");
    if (url.endsWith("/refresh/")) return json({}, 401);
    assert.deepEqual(JSON.parse(options.body), { username: "maria", password: "local" });
    return json({ access_token: "access-maria" });
  };
  await auth.restoreSession();
  await auth.login("maria", "local");
  assert.equal(auth.getAccessToken(), "access-maria");
  assert.deepEqual(changes, ["anonymous", "signing-in", "authenticated"]);
  unsubscribe();
});

test("credenciales incorrectas no dejan access en memoria", async () => {
  const auth = await freshAuth();
  globalThis.fetch = async (url) => url.endsWith("/csrf/")
    ? json({ csrf_token: "csrf-test" }) : json({ message: "Credenciales incorrectas" }, 401);
  await assert.rejects(auth.login("maria", "incorrecta"), /Credenciales incorrectas/);
  assert.equal(auth.getAccessToken(), null);
  assert.equal(auth.getSessionStatus(), "anonymous");
});

test("peticiones paralelas comparten refresh y conservan headers y método", async () => {
  const auth = await freshAuth();
  let refreshes = 0;
  let csrf = 0;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith("/csrf/")) { csrf++; return json({ csrf_token: "csrf-test" }); }
    if (url.endsWith("/refresh/")) { refreshes++; return json({ access_token: "access-shared" }); }
    const headers = new Headers(options.headers);
    assert.equal(headers.get("Authorization"), "Bearer access-shared");
    assert.equal(headers.get("X-Test"), "preserved");
    assert.equal(headers.get("X-Participant-ID"), null);
    assert.equal(options.method, "PUT");
    return json({}, 201);
  };
  await Promise.all([1, 2].map(() => auth.authenticatedFetch("me/enrollments/create/activity/", {
    method: "PUT", headers: { "X-Test": "preserved" },
  })));
  assert.equal(refreshes, 1);
  assert.equal(csrf, 1);
});

test("un 401 renueva y reintenta una sola vez", async () => {
  const auth = await freshAuth();
  let refreshes = 0;
  let requests = 0;
  globalThis.fetch = async (url) => {
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    if (url.endsWith("/refresh/")) return json({ access_token: `access-${++refreshes}` });
    requests++;
    return json({}, 401);
  };
  await assert.rejects(auth.authenticatedFetch("me/enrollments/"), auth.AuthenticationRequiredError);
  assert.equal(refreshes, 2);
  assert.equal(requests, 2);
  assert.equal(auth.getSessionStatus(), "anonymous");
  assert.equal(auth.getAccessToken(), null);
});

test("403 y cupo agotado 409 no provocan renovación ni reintentos", async () => {
  const auth = await freshAuth();
  let refreshes = 0;
  let deniedStatus = 409;
  globalThis.fetch = async (url) => {
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    if (url.endsWith("/refresh/")) { refreshes++; return json({ access_token: "access" }); }
    return json({ message: "No hay cupos disponibles." }, deniedStatus);
  };
  assert.equal((await auth.authenticatedFetch("me/enrollments/create/activity/", { method: "PUT" })).status, 409);
  deniedStatus = 403;
  assert.equal((await auth.authenticatedFetch("me/enrollments/")).status, 403);
  assert.equal(refreshes, 1);
});

test("logout usa CSRF, limpia memoria y bloquea consultas posteriores", async () => {
  const auth = await freshAuth();
  let calls = 0;
  globalThis.fetch = async (url, options) => {
    calls++;
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    if (url.endsWith("/refresh/")) return json({ access_token: "access" });
    assert.ok(url.endsWith("/logout/"));
    assert.equal(new Headers(options.headers).get("Authorization"), null);
    assert.equal(new Headers(options.headers).get("X-CSRFToken"), "csrf-test");
    return new Response(null, { status: 204 });
  };
  await auth.restoreSession();
  const closing = auth.logout();
  assert.equal(auth.getAccessToken(), null);
  assert.equal(auth.getSessionStatus(), "signing-out");
  assert.equal(auth.logout(), closing);
  await closing;
  assert.equal(auth.getSessionStatus(), "anonymous");
  const previousCalls = calls;
  await assert.rejects(auth.authenticatedFetch("me/enrollments/"), auth.AuthenticationRequiredError);
  assert.equal(calls, previousCalls);
});

for (const action of ["refresh", "login"]) {
  test(`logout espera un ${action} en vuelo y descarta su access tardío`, async () => {
    const auth = await freshAuth();
    const lateResponse = deferred();
    const order = [];
    globalThis.fetch = async (url) => {
      if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
      if (url.endsWith(`/${action}/`)) { order.push(action); return lateResponse.promise; }
      order.push("logout");
      return new Response(null, { status: 204 });
    };
    const signingIn = action === "refresh" ? auth.refreshAccessToken() : auth.login("maria", "local");
    const rejected = assert.rejects(signingIn, auth.SessionChangedError);
    await until(() => order.includes(action));
    const closing = auth.logout();
    await assert.rejects(auth.refreshAccessToken(), auth.AuthenticationRequiredError);
    assert.deepEqual(order, [action]);
    lateResponse.resolve(json({ access_token: "late-access" }));
    await Promise.all([closing, rejected]);
    assert.deepEqual(order, [action, "logout"]);
    assert.equal(auth.getAccessToken(), null);
    assert.equal(auth.getSessionStatus(), "anonymous");
  });
}

test("una respuesta privada anterior al logout queda descartada", async () => {
  const auth = await freshAuth();
  const privateResponse = deferred();
  let requested = false;
  globalThis.fetch = async (url) => {
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    if (url.endsWith("/refresh/")) return json({ access_token: "access" });
    if (url.endsWith("/logout/")) return new Response(null, { status: 204 });
    requested = true;
    return privateResponse.promise;
  };
  await auth.restoreSession();
  const rejected = assert.rejects(auth.authenticatedFetch("me/enrollments/"), auth.SessionChangedError);
  await until(() => requested);
  await auth.logout();
  privateResponse.resolve(json([{ activity_id: "private-data" }]));
  await rejected;
});

test("un error de logout se informa y permite recuperar la sesión", async () => {
  const auth = await freshAuth();
  globalThis.fetch = async (url) => {
    if (url.endsWith("/csrf/")) return json({ csrf_token: "csrf-test" });
    if (url.endsWith("/refresh/")) return json({ access_token: "still-valid" });
    return json({}, 500);
  };
  await auth.restoreSession();
  await assert.rejects(auth.logout(), /No se pudo cerrar/);
  assert.equal(auth.getAccessToken(), null);
  assert.equal(auth.getSessionStatus(), "unknown");
  await auth.restoreSession();
  assert.equal(auth.getSessionStatus(), "authenticated");
});
