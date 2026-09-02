

#DELETE /enrollments/<id>

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.aggregates import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from . serializers import ActivityOutSerializer, EnrollmentOutSerializer
from activities.models import Activity
from activities.models import Enrollment

ACTIVITY_NOT_FOUND = {
    "code": "activity_not_found",
    "message": "La actividad no existe.",
}
ENROLLMENT_NOT_FOUND = {
    "code": "enrollment_not_found",
    "message": "La inscripción no existe.",
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
PARTICIPANT_ALREADY_ENROLLED = {
    "code": "invalid_request",
    "message": "El participante ya se encuentra inscripto en el curso",
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

DEMO_PARTICIPANT_ID = "e939e6dd-6180-449e-9347-853e6437be31"

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

class ActivityDetailView(APIView):
    @extend_schema(
        operation_id="getActivity",
        summary="Obtener actividad",
        description="Devuelve la actividad con el id especificado.",
        tags=["Activities"],
        parameters=[ACTIVITY_ID_PARAMETER],
        responses={
            200: ActivityOutSerializer,
            404: OpenApiResponse(
                description=ACTIVITY_NOT_FOUND["message"],
                response=ACTIVITY_NOT_FOUND,
            ),
            405: METHOD_NOT_ALLOWED,
        },
    )
    def get(self, request, activity_id):
        try:
            activity = Activity.objects.annotate(
                enrolled_count=Count("enrollment")
            ).get(id=activity_id)
        except Activity.DoesNotExist:
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = ActivityOutSerializer(activity)
        return Response({"data":serializer.data})

class EnrollmentListView(APIView):
    @extend_schema(
            operation_id="getEnrollments",
            summary="Obtener inscripciones",
            description="Devuelve las inscirpciones del participante ",
            tags=["Enrollments"],
            responses={
                200: EnrollmentOutSerializer,
                405: METHOD_NOT_ALLOWED,
            },
        )
    def get(self, request):
        enrollments = Enrollment.objects.filter(participant_id=DEMO_PARTICIPANT_ID);
        serializer = EnrollmentOutSerializer(enrollments, many=True)
        return Response({"data": serializer.data})

class EnrollmentDetailView(APIView):
    def get(self, request, enrollment_id):
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
                return Response(ENROLLMENT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = EnrollmentOutSerializer(enrollment)
        return Response({"data":serializer.data})

class EnrollmentCreateView(APIView):
    @extend_schema(
        operation_id="createEnrollment",
        summary="Inscribirse en actividad",
        description="Crea una inscripción para el participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER, PARTICIPANT_HEADER],
        responses={
            200: EnrollmentOutSerializer,
            404: OpenApiResponse(
                description=ACTIVITY_NOT_FOUND["message"],
                response=ACTIVITY_NOT_FOUND,
            ),
            409: OpenApiResponse(
                description=CAPACITY_EXHAUSTED["message"],
                response=CAPACITY_EXHAUSTED,
            ),
            409: OpenApiResponse(
                description=PARTICIPANT_ALREADY_ENROLLED["message"],
                response=PARTICIPANT_ALREADY_ENROLLED,
            ),
            405: METHOD_NOT_ALLOWED,
        },
    )
    def put(self, request, activity_id):
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        if(activity.capacity <= Enrollment.objects.filter(activity=activity).count()):
           return Response(CAPACITY_EXHAUSTED, status=status.HTTP_409_CONFLICT)
        if(Enrollment.objects.filter(activity=activity, participant_id=DEMO_PARTICIPANT_ID).exists()):
            return Response(PARTICIPANT_ALREADY_ENROLLED, status=status.HTTP_409_CONFLICT)
        enrollment = Enrollment.objects.create(activity=activity, participant_id=DEMO_PARTICIPANT_ID)
        serializer = EnrollmentOutSerializer(enrollment)
        return Response({"data":serializer.data})

class EnrollmentDeleteView(APIView):
    @extend_schema(
        operation_id="deleteEnrollment",
        summary="Cancelar inscripción",
        description="Cancela la inscripción del participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER, PARTICIPANT_HEADER],
        responses={
            204: NO_CONTENT,
            404: OpenApiResponse(
                description=ENROLLMENT_NOT_FOUND["message"],
                response=ENROLLMENT_NOT_FOUND,
            ),
            405: METHOD_NOT_ALLOWED,
        },
    )
    def delete(self, request, activity_id):
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        try:
            enrollment = Enrollment.objects.get(activity=activity, participant_id=DEMO_PARTICIPANT_ID)
        except Enrollment.DoesNotExist:
            return Response(ENROLLMENT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

