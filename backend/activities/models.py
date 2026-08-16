import uuid

from django.db import models


class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=160)
    starts_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()

    class Meta:
        ordering = ("starts_at",)
        verbose_name_plural = "activities"

    def __str__(self):
        return self.title

class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    class Meta:
        ordering = ("name",)
        verbose_name_plural = "participants"

    def __str__(self):
        return self.name

class Enrollment (models.Model):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
   activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
   participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
   enrolled_at = models.DateTimeField(auto_now=True)

   class Meta:
       constraints = [
           models.UniqueConstraint(
               fields=["activity", "participant"],
               name="unique_enrollment_activity_participant",
           )
       ]
   
   