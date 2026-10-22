import { useState } from "react";
import { logout } from "../../lib/auth";
import { useSession } from "../../lib/useSession";

export default function SessionControls() {
  const { status, error: restoreError, retry } = useSession();
  const [error, setError] = useState("");

  async function handleLogout() {
    setError("");
    try {
      await logout();
      window.location.assign("/login/");
    } catch (error) {
      setError(error instanceof Error ? error.message : "No se pudo cerrar la sesión.");
    }
  }

  return (
    <div className="session-controls">
      <nav className="session-nav" aria-label="Navegación de sesión">
        <a href="/">Actividades</a>
        {status === "authenticated" ? (
          <>
            <a href="/enrollments/">Mis inscripciones</a>
            <button className="button button-secondary" type="button" onClick={handleLogout}>
              Cerrar sesión
            </button>
          </>
        ) : status === "anonymous" ? (
          <a className="button button-primary" href="/login/">Ingresar</a>
        ) : (
          <span role="status">
            {status === "signing-out" ? "Cerrando sesión…"
              : status === "signing-in" ? "Ingresando…"
              : restoreError ? "Sesión sin comprobar" : "Comprobando sesión…"}
          </span>
        )}
      </nav>
      {(error || restoreError) && (
        <div className="session-error">
          <span role="alert">{error || restoreError}</span>
          {restoreError && <button type="button" onClick={retry}>Reintentar</button>}
        </div>
      )}
    </div>
  );
}
