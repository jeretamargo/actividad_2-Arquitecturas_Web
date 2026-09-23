export const backendUrl = (process.env.BACKEND_URL
	?? import.meta.env.BACKEND_URL
	?? 'http://127.0.0.1:8000').replace(/\/$/, '');

export const participantId = import.meta.env.VITE_PARTICIPANT_ID
	?? 'e939e6dd-6180-449e-9347-853e6437be31';
