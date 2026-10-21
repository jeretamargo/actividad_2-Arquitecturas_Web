from datetime import datetime
from uuid import UUID

from django.test import TestCase
from django.utils import timezone

from .models import Activity


class ActivityListTests(TestCase):
    def test_lists_every_activity_field(self):
        activity = Activity.objects.create(
            id=UUID("1b470ddf-3e84-4b77-9aae-091d21e52bd6"),
            title="Diseño de una API",
            starts_at=timezone.make_aware(datetime(2026, 3, 23, 18, 0)),
            capacity=30,
        )

        response = self.client.get("/api/v2/activities/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": str(activity.id),
            "title": activity.title,
            "starts_at": "2026-03-23T18:00:00-03:00",
            "capacity": 30,
            "availability": {"capacity": 30, "available_slots": 30},
        }])

    def test_rejects_non_get_requests(self):
        response = self.client.post("/api/v2/activities/")

        self.assertEqual(response.status_code, 405)
