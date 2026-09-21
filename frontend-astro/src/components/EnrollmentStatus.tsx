import { useEffect, useState } from 'react';

interface Props {
	activityId: string;
	apiUrl: string;
	participantId: string;
}

interface Enrollment {
	activity_id: string;
	participant: {
		enrolled_at: string;
	};
}

type Status = 'loading' | 'available' | 'submitting' | 'enrolled' | 'error';

export default function EnrollmentStatus({ activityId, apiUrl, participantId }: Props) {
	const [status, setStatus] = useState<Status>('loading');
	const [message, setMessage] = useState('Consultando tus inscripciones...');
	const [canEnroll, setCanEnroll] = useState(false);

	useEffect(() => {
		let cancelled = false;

		async function getEnrollmentStatus() {
			setCanEnroll(false);
			try {
				const response = await fetch(`${apiUrl}/api/v2/me/enrollments/`, {
					headers: { 'X-Participant-ID': participantId },
				});
				if (!response.ok) throw new Error(`Request failed: ${response.status}`);

				const enrollments: Enrollment[] = await response.json();
				const enrollment = enrollments.find((item) => item.activity_id === activityId);
				if (cancelled) return;

				if (enrollment) {
					const enrolledDate = enrollment.participant.enrolled_at
						? new Date(enrollment.participant.enrolled_at).toLocaleDateString('es-AR', { dateStyle: 'medium' })
						: null;
					setStatus('enrolled');
					setMessage(enrolledDate
						? `Ya estás inscripto en esta actividad desde el ${enrolledDate}.`
						: 'Ya estás inscripto en esta actividad.');
				} else {
					setStatus('available');
					setMessage('Todavía no estás inscripto en esta actividad.');
					setCanEnroll(true);
				}
			} catch {
				if (!cancelled) {
					setStatus('error');
					setMessage('No pudimos consultar tu estado de inscripción. Intentá nuevamente más tarde.');
				}
			}
		}

		getEnrollmentStatus();
		return () => { cancelled = true; };
	}, [activityId, apiUrl, participantId]);

	async function enroll() {
		setStatus('submitting');
		setMessage('Enviando inscripción...');
		setCanEnroll(false);

		try {
			const response = await fetch(`${apiUrl}/api/v2/me/enrollments/create/${activityId}/`, {
				method: 'PUT',
				headers: { 'X-Participant-ID': participantId },
			});
			if (!response.ok) {
				const errorPayload = await response.json().catch(() => null);
				throw new Error(errorPayload?.message ?? 'No se pudo completar la inscripción.');
			}

			setStatus('enrolled');
			setMessage('Te inscribiste correctamente en esta actividad.');
		} catch (error) {
			setStatus('error');
			setMessage(error instanceof Error ? error.message : 'No se pudo completar la inscripción.');
			setCanEnroll(true);
		}
	}

	return (
		<section className="enrollment-status" data-state={status} aria-live="polite" aria-labelledby="enrollment-status-title">
			<div className="enrollment-status__header">
				<div>
					<p className="detail-label">Estado de inscripción</p>
					<h2 id="enrollment-status-title">Inscripción del participante</h2>
				</div>
				<span className="status-indicator" aria-hidden="true" />
			</div>
			<p className="content-origin content-origin--client">Consulta client-side</p>
			<p className="enrollment-status__message">{message}</p>
			{canEnroll && (
				<form className="enrollment-form" onSubmit={(event) => { event.preventDefault(); enroll(); }}>
					<button className="button button-primary" type="submit">Inscribirme en esta actividad</button>
				</form>
			)}
		</section>
	);
}
