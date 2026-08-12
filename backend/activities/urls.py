from django.urls import path

from . import views


app_name = "activities"

urlpatterns = [
    path("", views.activity_list, name="list"),
    path("api/v1/activities/", views.activity_api_list, name="api-list"),
    path("api/v1/me/enrollments/<str:activity_id>", views.activity_enrollment_api_put, name="enrollment-api-put"),
]
