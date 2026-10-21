from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from activities.models import Participant


# Cuentas públicas de evaluación local; no utilizar en un despliegue real.
DEMO_USERS = (
    {
        "username": "maria",
        "password": "MariaTP2026!",
        "participant_id": UUID("e939e6dd-6180-449e-9347-853e6437be31"),
        "name": "María López",
    },
    {
        "username": "jorge",
        "password": "JorgeTP2026!",
        "participant_id": UUID("4f1a640a-5ca7-4bb1-8aee-88bd443bf71e"),
        "name": "Jorge Fernández",
    },
)


class Command(BaseCommand):
    help = (
        "Crea o restaura las dos cuentas de evaluación local y las vincula "
        "con sus participantes, sin modificar actividades ni inscripciones."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        for demo in DEMO_USERS:
            user, _ = User.objects.get_or_create(username=demo["username"])
            if user.is_staff or user.is_superuser:
                raise CommandError(
                    f"La cuenta {user.username} tiene privilegios administrativos; "
                    "no se modificó ninguna cuenta."
                )

            participant, _ = Participant.objects.get_or_create(
                id=demo["participant_id"],
                defaults={"name": demo["name"]},
            )
            if participant.user_id not in (None, user.pk) or (
                Participant.objects.filter(user=user)
                .exclude(pk=participant.pk)
                .exists()
            ):
                raise CommandError(
                    f"La vinculación de {user.username} entra en conflicto con "
                    "un participante existente; no se modificó ninguna cuenta."
                )

            # Evita recalcular el hash cuando la contraseña ya es la esperada.
            if not user.check_password(demo["password"]):
                user.set_password(demo["password"])
                user.save(update_fields=["password"])
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])
            if participant.user_id is None:
                participant.user = user
                participant.save(update_fields=["user"])

        self.stdout.write(
            self.style.SUCCESS(
                "Usuarios locales preparados: maria y jorge. "
                "Credenciales de evaluación en README.md."
            )
        )
