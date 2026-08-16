from django.utils import timezone

from activities.models import Enrollment

def serialize_activity(activity):
   
    return {
        "id": activity.id,
        "title": activity.title,
        "starts_at":  timezone.localtime(activity.starts_at).isoformat(),
        "capacity": activity.capacity,
        "available_slots": activity.capacity - Enrollment.objects.filter(activity=activity).count(),
    }

def serialize_enrollment(enrollment):
   
    return {
        "id": enrollment.id,
        "activity_id": enrollment.activity.id,
        "participant_id": enrollment.participant.id,
        "enrolled_at":  timezone.localtime(enrollment.enrolled_at).isoformat(),
        
    }


def serialize_activities(activities):
    return [serialize_activity(activity) for activity in activities]

def serialize_enrollments(enrollments):
    return [serialize_enrollment(enrollment) for enrollment in enrollments]