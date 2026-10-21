import { useEffect, useState, useSyncExternalStore } from "react";
import { getSessionStatus, restoreSession, subscribeSession, type SessionStatus } from "./auth";

const getServerStatus = (): SessionStatus => "unknown";

export function useSession() {
  const status = useSyncExternalStore(subscribeSession, getSessionStatus, getServerStatus);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (status !== "unknown") return;
    let cancelled = false;
    void restoreSession().catch((error: unknown) => {
      if (!cancelled) {
        setError(error instanceof Error ? error.message : "No se pudo comprobar la sesión.");
      }
    });
    return () => { cancelled = true; };
  }, [status, attempt]);

  function retry() {
    setError("");
    setAttempt((value) => value + 1);
  }

  return { status, error: status === "unknown" ? error : "", retry };
}
