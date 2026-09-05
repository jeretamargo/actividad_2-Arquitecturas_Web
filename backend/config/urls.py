from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView





urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("activities.api.v1.urls")),  
    path("api/v2/", include("activities.api.v2.urls")),
    path(
        "api/v2/schema/",
        SpectacularAPIView.as_view(),
        name="schema-v2",
    ),

    path(
        "api/v2/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema-v2"
        ),
        name="swagger-ui-v2",
    ),
]
