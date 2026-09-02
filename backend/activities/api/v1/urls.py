from django.urls import path

from . import views


app_name = "activities"

urlpatterns = [
    path("", views.activity_list, name="list"),
    path("activities/", views.activity_api_list, name="api-activities-list"),
    path("me/enrollments/", views.enrolment_api_list, name="api-enrollments-list"),
    path("me/enrollments/create/<uuid:activity_id>", views.create_enrollment, name="enrollment-api-put"),
    path("me/enrollments/delete/<uuid:activity_id>", views.delete_enrollment, name="enrollment-api-delete"),
    path("activities/<uuid:activity_id>", views.activity_api, name = "api_activity_by_id" )   
    ]