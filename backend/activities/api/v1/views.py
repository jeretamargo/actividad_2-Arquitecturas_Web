
from uuid import UUID

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from ...models import Activity, Enrollment, Participant
from ...representations import (
    serialize_activities,
    serialize_activity,
    serialize_enrollment,
    serialize_enrollments,
)





DEMO_PARTICIPANT_ID = "e939e6dd-6180-449e-9347-853e6437be31"

def response_error(status, code, message):
    response = JsonResponse({"error": message, "code": code}, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    return response


def activity_list(request):
    activities = Activity.objects.all()
    return render(
        request,
        "activities/activity_list.html",
        {"activities": activities},
    )


@require_GET
def activity_api_list(request):
    activities = Activity.objects.all()
    payload = serialize_activities(activities)
    # payload = [serialize_activity(activity) for activity in activities]
    return JsonResponse({"data": payload})

@require_GET
def activity_api(request, activity_id):
    activitie = get_object_or_404(Activity, id=activity_id)
    payload = serialize_activity(activitie)
    return JsonResponse({"data": payload})




@require_GET
def enrolment_api_list(request):
    enrollments = Enrollment.objects.filter(participant_id=DEMO_PARTICIPANT_ID);
    payload = serialize_enrollments(enrollments);
    response = JsonResponse({"data": payload})
    response["Access-Control-Allow-Origin"] = "*"
    return response

@require_http_methods(["OPTIONS", "PUT"])
@csrf_exempt
def create_enrollment(request, activity_id):
    if request.method == "OPTIONS":
        response = JsonResponse({}, status=204)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "PUT, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "PUT":
        return response_error(400, "invalid_request", "Invalid request method")
    
    activity = get_object_or_404(Activity, id=activity_id)
    if(activity.capacity <= Enrollment.objects.filter(activity=activity).count()):
        return response_error(409, "activity_full", "La actividad alcanzo la capacidad maxima de cupos")
    if(Enrollment.objects.filter(activity=activity, participant_id=DEMO_PARTICIPANT_ID).exists()):
        return response_error(409, "already_enrolled", "El participante ya posee una inscripcion en esta actividad")
    enrollment = Enrollment.objects.create(activity=activity, participant_id=DEMO_PARTICIPANT_ID)
    payload = serialize_enrollment(enrollment)
    response = JsonResponse({"data": payload})
    response["Access-Control-Allow-Origin"] = "*"
    return response

@require_http_methods(["DELETE"])
@csrf_exempt
def delete_enrollment(request, activity_id):
     if request.method != "DELETE":
            return response_error(400, "invalid_request", "Invalid request method")
     activity = get_object_or_404(Activity, id=activity_id)
     participant = get_object_or_404(Participant, id= DEMO_PARTICIPANT_ID)
     enrollment = get_object_or_404(Enrollment, activity = activity, participant = participant )
     enrollment.delete()
     return JsonResponse({},status=204)

@require_http_methods(["PUT"])
@csrf_exempt
def activity_enrollment_api_put(request, activity_id):
    if True:
        return response_error(400, "invalid_request", "Invalid request method")
    
    return JsonResponse({"data": []})
