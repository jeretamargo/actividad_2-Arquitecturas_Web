import { useEffect, useRef, useState } from "react";
import { authenticatedFetch } from "../../lib/auth";
import { useSession } from "../../lib/useSession";

interface Props {
  activityId: string;
}

interface Enrollment {
  activity_id: string;
  participant: { enrolled_at: string };
}

export default function EnrollmentStatus({ activityId }: Props) {
  const { status: session, error: sessionError, retry: retrySession } = useSession();
  const [enrolled, setEnrolled] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<"enroll" | "cancel" | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const requestGeneration = useRef(0);
  const operationInProgress = useRef(false);

  useEffect(() => {
    const generation = ++requestGeneration.current;
    setEnrolled(null);
    setError("");
    setMessage("");
    setPending(null);
    if (session !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);
    void (async () => {
      try {
        const response = await authenticatedFetch("me/enrollments/");
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.message ?? "No pudimos consultar tu inscripción.");
        if (!Array.isArray(data)) throw new Error("No pudimos consultar tu inscripción.");
        const enrollment = (data as Enrollment[]).find((item) => item.activity_id === activityId);
        if (generation === requestGeneration.current) {
          setEnrolled(Boolean(enrollment));
          setMessage(enrollment ? "Ya estás inscripto en esta actividad." : "Todavía no estás inscripto en esta actividad.");
        }
      } catch (error) {
        if (generation === requestGeneration.current) {
          setError(error instanceof Error ? error.message : "No pudimos consultar tu inscripción.");
        }
      } finally {
        if (generation === requestGeneration.current) setLoading(false);
      }
    })();
    return () => { requestGeneration.current += 1; };
  }, [activityId, session, attempt]);

  async function updateAvailableSlots() {
    const response = await fetch(`/api/v2/activities/${activityId}/`, {
      credentials: "same-origin", cache: "no-store",
    });
    if (!response.ok) throw new Error("No se pudieron actualizar los cupos.");
    const data = await response.json();
    const target = document.querySelector<HTMLElement>("[data-activity-availability]");
    // Este nodo pertenece al HTML de Astro, fuera del árbol de React.
    if (
      target?.dataset.activityAvailability === activityId &&
      typeof data?.availability?.available_slots === "number"
    ) {
      target.textContent = String(data.availability.available_slots);
    }
  }

  async function handleAction() {
    if (session !== "authenticated" || enrolled === null || operationInProgress.current) return;
    operationInProgress.current = true;
    const generation = requestGeneration.current;
    const wasEnrolled = enrolled;
    setPending(wasEnrolled ? "cancel" : "enroll");
    setError("");
    try {
      const response = await authenticatedFetch(
        `me/enrollments/${wasEnrolled ? "delete" : "create"}/${activityId}/`,
        { method: wasEnrolled ? "DELETE" : "PUT" },
      );
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.message ?? "No se pudo completar la operación.");
      }
      if (generation !== requestGeneration.current) return;
      setEnrolled(!wasEnrolled);
      setMessage(wasEnrolled ? "Cancelaste tu inscripción." : "Te inscribiste correctamente.");
      try {
        await updateAvailableSlots();
      } catch {
        if (generation === requestGeneration.current) {
          setMessage(`${wasEnrolled ? "Inscripción cancelada." : "Inscripción confirmada."} Recargá la página para actualizar los cupos.`);
        }
      }
    } catch (error) {
      if (generation === requestGeneration.current) {
        setError(error instanceof Error ? error.message : "No se pudo completar la operación.");
      }
    } finally {
      operationInProgress.current = false;
      if (generation === requestGeneration.current) setPending(null);
    }
  }

  const state = session === "unknown" || loading ? "loading"
    : pending ? "submitting" : error ? "error" : enrolled ? "enrolled" : "available";

  return (
    <section className="enrollment-status" data-state={state} aria-live="polite" aria-busy={loading || Boolean(pending)} aria-labelledby="enrollment-status-title">
      <div className="enrollment-status__header">
        <div>
          <p className="detail-label">Estado de inscripción</p>
          <h2 id="enrollment-status-title">Tu inscripción</h2>
        </div>
        <span className="status-indicator" aria-hidden="true" />
      </div>
      {session === "unknown" ? (
        <div className="enrollment-status__message">
          <p role={sessionError ? "alert" : "status"}>{sessionError || "Comprobando sesión…"}</p>
          {sessionError && <button type="button" className="button button-secondary" onClick={retrySession}>Reintentar</button>}
        </div>
      ) : session === "anonymous" ? (
        <p className="enrollment-status__message"><a href="/login/">Iniciá sesión</a> para gestionar tu inscripción.</p>
      ) : session !== "authenticated" ? (
        <p className="enrollment-status__message" role="status">{session === "signing-out" ? "Cerrando sesión…" : "Ingresando…"}</p>
      ) : loading ? (
        <p className="enrollment-status__message" role="status">Consultando tu inscripción…</p>
      ) : (
        <div className="enrollment-status__message">
          {message && <p>{message}</p>}
          {error && <p role="alert">{error}</p>}
          {enrolled === null ? (
            <button type="button" className="button button-secondary" onClick={() => setAttempt((value) => value + 1)}>Reintentar consulta</button>
          ) : (
            <button type="button" className={`button ${enrolled ? "button-secondary" : "button-primary"}`} disabled={Boolean(pending)} onClick={handleAction}>
              {pending === "enroll" ? "Inscribiendo…" : pending === "cancel" ? "Cancelando…" : enrolled ? "Cancelar inscripción" : "Inscribirme en esta actividad"}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
