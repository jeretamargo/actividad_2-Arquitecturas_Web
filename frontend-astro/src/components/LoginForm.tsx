import { useState, type FormEvent } from "react";
import { login } from "../../lib/auth";
import { useSession } from "../../lib/useSession";

export default function LoginForm() {
  const { status, error: sessionError, retry } = useSession();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    setError("");
    setPending(true);

    try {
      await login(username, password);
      setPassword("");
    } catch (error) {
      setError(
        error instanceof Error ? error.message : "No se pudo iniciar sesión.",
      );
    } finally {
      setPending(false);
    }
  }

  if (status === "unknown") {
    return (
      <div>
        <p role={sessionError ? "alert" : "status"}>{sessionError || "Comprobando sesión…"}</p>
        {sessionError && <button type="button" className="button button-secondary" onClick={retry}>Reintentar</button>}
      </div>
    );
  }

  if (status === "signing-out") return <p role="status">Cerrando sesión…</p>;

  if (status === "authenticated") {
    return (
      <div role="status">
        <p>Sesión iniciada correctamente.</p>
        <a className="button button-primary" href="/enrollments/">
          Ver mis inscripciones
        </a>
      </div>
    );
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <label htmlFor="login-username">
        Usuario
        <input
          id="login-username"
          name="username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          disabled={pending}
          required
        />
      </label>

      <label htmlFor="login-password">
        Contraseña
        <input
          id="login-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={pending}
          required
        />
      </label>

      {error && <p role="alert">{error}</p>}

      <button
        className="button button-primary"
        type="submit"
        disabled={pending}
      >
        {pending ? "Ingresando…" : "Ingresar"}
      </button>
    </form>
  );
}
