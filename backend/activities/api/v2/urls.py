from django.urls import path

from . import views


app_name = "activities"

urlpatterns = [
    
    path("activities/", views.ActivityListView.as_view(), name="api-activities-list")
    ,
    path("activities/<uuid:activity_id>/", views.ActivityDetailView.as_view(), name="api-activities-detail")
    ,
    path("me/enrollments/", views.EnrollmentListView.as_view(), name="api-enrollment-list")
    ,
    path("me/enrollments/<uuid:enrollment_id>/", views.EnrollmentDetailView.as_view(), name="api-enrollment-detail")
    ,
    path("me/enrollments/create/<uuid:activity_id>/", views.EnrollmentCreateView.as_view(), name="api-enrollment-create")
        ,
]