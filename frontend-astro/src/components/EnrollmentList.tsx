import { useEffect, useState } from "react";
import { authenticatedFetch } from "../../lib/auth";
import { useSession } from "../../lib/useSession";

interface Enrollment {
  id: string;
  activity_id: string;
  participant: {
    participant_id: string;
    enrolled_at: string;
  };
}

export default function EnrollmentList() {
  const { status, error: sessionError, retry } = useSession();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setEnrollments([]);
    setError("");
    if (status !== "authenticated") {
      setLoading(false);
      return;
    }
    setLoading(true);

    async function load() {
      try {
        const response = await authenticatedFetch("me/enrollments/");
        const data = await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            data?.message ?? "No pudimos cargar tus inscripciones.",
          );
        }

        if (!Array.isArray(data)) {
          throw new Error("La respuesta de inscripciones no es válida.");
        }

        if (!cancelled) setEnrollments(data);
      } catch (error) {
        if (!cancelled) {
          setError(
            error instanceof Error
              ? error.message
              : "No pudimos cargar tus inscripciones.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [status]);

  return (
    <section
      className="content"
      aria-labelledby="enrollments-title"
      aria-busy={loading}
    >
      <div className="page-heading">
        <p className="eyebrow">Seguimiento</p>
        <h1 id="enrollments-title">Mis inscripciones</h1>
        <p className="lead">
          Revisá las actividades en las que estás inscripto.
        </p>
      </div>

      <p>
        <a href="/">Volver a actividades</a>
      </p>

      {status === "unknown" ? (
        <div>
          <p role={sessionError ? "alert" : "status"}>{sessionError || "Comprobando sesión…"}</p>
          {sessionError && <button type="button" className="button button-secondary" onClick={retry}>Reintentar</button>}
        </div>
      ) : status === "anonymous" ? (
        <p><a href="/login/">Iniciá sesión</a> para consultar tus inscripciones.</p>
      ) : status !== "authenticated" ? (
        <p role="status">{status === "signing-out" ? "Cerrando sesión…" : "Ingresando…"}</p>
      ) : loading ? (
        <p role="status">Cargando inscripciones…</p>
      ) : error ? (
        <div className="empty-state">
          <p role="alert">{error}</p>
          <a href="/login/">Ir a iniciar sesión</a>
        </div>
      ) : enrollments.length === 0 ? (
        <p>No tenés inscripciones por el momento.</p>
      ) : (
        <div className="activities-grid">
          {enrollments.map((enrollment) => (
            <article className="activity-card" key={enrollment.id}>
              <h2>Actividad</h2>
              <p className="stat-value--small">{enrollment.activity_id}</p>
              <p>
                Inscripción:{" "}
                {new Date(enrollment.participant.enrolled_at).toLocaleString(
                  "es-AR",
                  {
                    dateStyle: "medium",
                    timeStyle: "short",
                  },
                )}
              </p>
              <a href={`/activities/${enrollment.activity_id}/`}>
                Ver actividad
              </a>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
