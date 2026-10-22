from io import StringIO

from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase

from activities.management.commands.seed_users import DEMO_USERS
from activities.models import Activity, Enrollment, Participant


class SeedUsersTests(TestCase):
    def seed(self, command):
        call_command(command, stdout=StringIO())

    def test_clean_bootstrap_allows_login_and_uses_authenticated_participant(self):
        self.seed("seed_activities")
        self.seed("seed_users")
        self.assertEqual(Activity.objects.count(), 4)
        self.assertEqual(Participant.objects.count(), 5)
        self.assertEqual(Enrollment.objects.count(), 8)
        self.assertEqual(get_user_model().objects.count(), 2)

        for demo, expected_count in zip(DEMO_USERS, (2, 1)):
            with self.subTest(username=demo["username"]):
                client = Client(enforce_csrf_checks=True)
                csrf = client.get("/api/v2/auth/csrf/").json()["csrf_token"]
                response = client.post(
                    "/api/v2/auth/login/",
                    {"username": demo["username"], "password": demo["password"]},
                    content_type="application/json",
                    HTTP_X_CSRFTOKEN=csrf,
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.cookies["refresh_token"]["httponly"])
                response = client.get(
                    "/api/v2/me/enrollments/",
                    HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}",
                    # Un identificador enviado por el cliente no cambia la identidad.
                    HTTP_X_PARTICIPANT_ID="5123326d-077c-41d2-902f-1d37bb0f5931",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json()), expected_count)
                self.assertTrue(all(
                    row["participant"]["participant_id"] == str(demo["participant_id"])
                    for row in response.json()
                ))

    def test_repeating_seed_preserves_users_password_hashes_and_enrollments(self):
        self.seed("seed_activities")
        self.seed("seed_users")
        User = get_user_model()
        original = dict(User.objects.values_list("username", "pk"))
        hashes = dict(User.objects.values_list("username", "password"))
        enrollment_ids = set(Enrollment.objects.values_list("pk", flat=True))
        extra = Enrollment.objects.create(
            activity_id="81c19727-4da2-5f0a-848c-851fa44f1f50",
            participant_id=DEMO_USERS[0]["participant_id"],
        )

        self.seed("seed_users")

        self.assertEqual(dict(User.objects.values_list("username", "pk")), original)
        self.assertEqual(dict(User.objects.values_list("username", "password")), hashes)
        self.assertEqual(Participant.objects.count(), 5)
        self.assertEqual(
            set(Enrollment.objects.values_list("pk", flat=True)),
            enrollment_ids | {extra.pk},
        )

    def test_seed_restores_demo_credentials_and_can_run_without_activity_seed(self):
        self.seed("seed_users")
        User = get_user_model()
        user = User.objects.get(username="maria")
        user.set_password("changed-for-test")
        user.is_active = False
        user.save()

        self.seed("seed_users")

        for demo in DEMO_USERS:
            user = authenticate(username=demo["username"], password=demo["password"])
            self.assertIsNotNone(user)
            self.assertEqual(user.participant.pk, demo["participant_id"])
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
        self.assertIsNone(authenticate(username="maria", password="incorrecta"))
        self.assertEqual(Activity.objects.count(), 0)

    def test_conflict_rolls_back_all_changes_instead_of_reassigning_identity(self):
        User = get_user_model()
        owner = User.objects.create_user(username="another-user", password="test-only")
        participant = Participant.objects.create(
            id=DEMO_USERS[1]["participant_id"], name="Otro titular", user=owner
        )

        with self.assertRaisesMessage(CommandError, "conflicto"):
            self.seed("seed_users")

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Participant.objects.count(), 1)
        participant.refresh_from_db()
        self.assertEqual(participant.user_id, owner.pk)
