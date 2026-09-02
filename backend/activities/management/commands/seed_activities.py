from datetime import datetime
from uuid import UUID

from django.core.management.base import BaseCommand
from django.utils import timezone

from activities.models import Activity, Enrollment, Participant


ACTIVITIES = [
    {
        "id": UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
        "title": "Introducción a APIs web",
        "starts_at": timezone.make_aware(datetime(2026, 3, 23, 18, 0)),
        "capacity": 30,
    },
    {
        "id": UUID("6ccaf64f-d37e-4e6c-ae03-f3d6547bb297"),
        "title": "Contratos HTTP observables",
        "starts_at": timezone.make_aware(datetime(2026, 3, 25, 18, 0)),
        "capacity": 24,
    },
    {
        "id": UUID("80c08526-3da1-4f0a-845c-740fa33f1f50"),
        "title": "Taller de integración",
        "starts_at": timezone.make_aware(datetime(2026, 3, 27, 17, 0)),
        "capacity": 20,
    },
    {
        "id": UUID("81c19727-4da2-5f0a-848c-851fa44f1f50"),
        "title": "Taller de de prueba",
        "starts_at": timezone.make_aware(datetime(2026, 3, 28, 17, 0)),
        "capacity": 2,
    },
]

PARTICIPANTS = [
    {
        "id": UUID("e939e6dd-6180-449e-9347-853e6437be31"),
        "name": "María López",
    },
    {
        "id": UUID("4f1a640a-5ca7-4bb1-8aee-88bd443bf71e"),
        "name": "Jorge Fernández",
    },
    {
        "id": UUID("5123326d-077c-41d2-902f-1d37bb0f5931"),
        "name": "Ana Sosa",
    },
    {
        "id": UUID("a6e09de5-50c1-4176-a559-1bdbfdf061eb"),
        "name": "Lucas Pérez",
    },
    {
        "id": UUID("874a734c-87e5-4692-aacc-88fb79025304"),
        "name": "Carla Díaz",
    },
]

ENROLLMENTS = [
    {
        "activity_id": UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
        "participant_id": UUID("e939e6dd-6180-449e-9347-853e6437be31"),
    },
    {
        "activity_id": UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
        "participant_id": UUID("4f1a640a-5ca7-4bb1-8aee-88bd443bf71e"),
    },
    {
        "activity_id": UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
        "participant_id": UUID("5123326d-077c-41d2-902f-1d37bb0f5931"),
    },
    {
        "activity_id": UUID("6ccaf64f-d37e-4e6c-ae03-f3d6547bb297"),
        "participant_id": UUID("e939e6dd-6180-449e-9347-853e6437be31"),
    },
    {
        "activity_id": UUID("6ccaf64f-d37e-4e6c-ae03-f3d6547bb297"),
        "participant_id": UUID("a6e09de5-50c1-4176-a559-1bdbfdf061eb"),
    },
    {
        "activity_id": UUID("80c08526-3da1-4f0a-845c-740fa33f1f50"),
        "participant_id": UUID("874a734c-87e5-4692-aacc-88fb79025304"),
    },
    {
        "activity_id": UUID("80c08526-3da1-4f0a-845c-740fa33f1f50"),
        "participant_id": UUID("a6e09de5-50c1-4176-a559-1bdbfdf061eb"),
    },
    {
        "activity_id": UUID("80c08526-3da1-4f0a-845c-740fa33f1f50"),
        "participant_id": UUID("5123326d-077c-41d2-902f-1d37bb0f5931"),
    },
]


class Command(BaseCommand):
    help = (
        "Restaura las actividades, participantes e inscripciones de muestra "
        "sin crear duplicados."
    )

    def handle(self, *args, **options):
        expected_activity_ids = [activity["id"] for activity in ACTIVITIES]
        expected_participant_ids = [participant["id"] for participant in PARTICIPANTS]
        expected_pairs = {
            (enrollment["activity_id"], enrollment["participant_id"])
            for enrollment in ENROLLMENTS
        }

        for enrollment in Enrollment.objects.all():
            pair = (enrollment.activity_id, enrollment.participant_id)
            if pair not in expected_pairs:
                enrollment.delete()

        Participant.objects.exclude(id__in=expected_participant_ids).delete()
        Activity.objects.exclude(id__in=expected_activity_ids).delete()

        for activity in ACTIVITIES:
            activity_id = activity["id"]
            defaults = {key: value for key, value in activity.items() if key != "id"}
            Activity.objects.update_or_create(id=activity_id, defaults=defaults)

        for participant in PARTICIPANTS:
            participant_id = participant["id"]
            defaults = {key: value for key, value in participant.items() if key != "id"}
            Participant.objects.update_or_create(id=participant_id, defaults=defaults)

        for enrollment in ENROLLMENTS:
            Enrollment.objects.update_or_create(
                activity_id=enrollment["activity_id"],
                participant_id=enrollment["participant_id"],
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Datos restaurados: "
                f"{len(ACTIVITIES)} actividades, "
                f"{len(PARTICIPANTS)} participantes y "
                f"{len(ENROLLMENTS)} inscripciones."
            )
        )
