#GET /activities
#GET /activities/<id>
#GET /enrollments
#GET /enrollments/<id>
#PUT /enrollments/<id>
#DELETE /enrollments/<id>

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.aggregates import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from . serializers import ActivityOutSerializer
from activities.models import Activity

ACTIVITY_NOT_FOUND = {
    "code": "activity_not_found",
    "message": "La actividad no existe.",
}
INVALID_IDENTITY = {
    "code": "invalid_participant",
    "message": "Falta el header X-Participant-ID o no identifica a un participante.",
}
CAPACITY_EXHAUSTED = {
    "code": "capacity_exhausted",
    "message": "No hay cupos disponibles.",
}
INVALID_REQUEST = {
    "code": "invalid_request",
    "message": "PUT no recibe un body en esta versión.",
}
REQUEST_NOT_VALID = {
    "code": "invalid_request",
    "message": "Los parámetros del request no son válidos.",
}

ACTIVITY_ID_PARAMETER = OpenApiParameter(
    name="activity_id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    required=True,
    description="Identificador único de la actividad.",
)
PARTICIPANT_HEADER = OpenApiParameter(
    name="X-Participant-ID",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description=(
        "UUID del participante de demostración. El comando seed_activities crea "
        "a3d8c92e-4f1a-4e5b-8c7d-9e0f1a2b3c4d."
    ),
)

METHOD_NOT_ALLOWED = OpenApiResponse(description="Método no permitido.")
NO_CONTENT = OpenApiResponse(description="Inscripción cancelada.")


class ActivityListView(APIView):
    @extend_schema(
        operation_id="listActivities",
        summary="Listar actividades",
        description="Devuelve todas las actividades ordenadas por fecha de inicio.",
        tags=["Activities"],
        responses={
            200: ActivityOutSerializer(many=True),
            405: METHOD_NOT_ALLOWED,
        },
    )
    def get(self, request):
        activities = Activity.objects.annotate(
            enrolled_count=Count("enrollment")
        ).order_by("starts_at")
        serializer = ActivityOutSerializer(activities, many=True)
        return Response({"data":serializer.data})
