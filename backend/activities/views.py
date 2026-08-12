from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .representations import serialize_activity, serialize_activities

from .models import Activity

def response_error(status, code, message):
    return JsonResponse({"error": message, "code": code}, status=status)

@require_GET
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

@require_http_methods(["PUT"])
@csrf_exempt
def activity_enrollment_api_put(request, activity_id):
    if True:
        return response_error(400, "invalid_request", "Invalid request method")
    
    return JsonResponse({"data": []})
