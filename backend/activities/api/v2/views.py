from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.aggregates import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from . serializers import ActivityOutSerializer, EnrollmentOutSerializer, ErrorSerializer
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


def get_participant_id(request):
    participant_id = request.headers.get("X-Participant-ID")

    if participant_id != DEMO_PARTICIPANT_ID:
        return None

    return participant_id



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
        return Response(serializer.data)

class ActivityDetailView(APIView):
    @extend_schema(
        operation_id="getActivity",
        summary="Obtener actividad",
        description="Devuelve la actividad con el id especificado.",
        tags=["Activities"],
        
        responses={
            200: ActivityOutSerializer,
            404: OpenApiResponse(
                response=ErrorSerializer,
                description=ACTIVITY_NOT_FOUND["message"],
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
        return Response(serializer.data)

class EnrollmentListView(APIView):
    @extend_schema(
            operation_id="getEnrollments",
            summary="Obtener inscripciones",
            description="Devuelve las inscirpciones del participante ",
            tags=["Enrollments"],
            parameters=[ACTIVITY_ID_PARAMETER, PARTICIPANT_HEADER],
            responses={
                200: EnrollmentOutSerializer,
                401:  OpenApiResponse(
                                response=ErrorSerializer,
                                description=INVALID_IDENTITY["message"],
                            ),
                405: METHOD_NOT_ALLOWED,
            },
        )
    def get(self, request):
        participant_id = get_participant_id(request)

        if not participant_id:
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        enrollments = Enrollment.objects.filter(participant_id=participant_id);
        serializer = EnrollmentOutSerializer(enrollments, many=True)
        return Response(serializer.data)


class EnrollmentCreateView(APIView):
    @extend_schema(
        operation_id="createEnrollment",
        summary="Inscribirse en actividad",
        description="Crea una inscripción para el participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER, PARTICIPANT_HEADER],
        responses={
            200: EnrollmentOutSerializer,
            201: EnrollmentOutSerializer,
            401:  OpenApiResponse(
                            response=ErrorSerializer,
                            description=INVALID_IDENTITY["message"],
                        ),
            404: OpenApiResponse(
                response=ErrorSerializer,
                description=ACTIVITY_NOT_FOUND["message"],
            ),
            409: OpenApiResponse(
                response=ErrorSerializer,
                description=CAPACITY_EXHAUSTED["message"],
            ),
           
            405: METHOD_NOT_ALLOWED,
        },
    )
    def put(self, request, activity_id):
        participant_id = get_participant_id(request)

        if not participant_id:
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        if(Enrollment.objects.filter(activity=activity, participant_id=participant_id).exists()):
            enrollment = Enrollment.objects.get(activity=activity, participant_id=participant_id)
            serializer = EnrollmentOutSerializer(enrollment)
            return Response(serializer.data,status=status.HTTP_200_OK)
        if(activity.capacity <= Enrollment.objects.filter(activity=activity).count()):
                   return Response(CAPACITY_EXHAUSTED, status=status.HTTP_409_CONFLICT)
        enrollment = Enrollment.objects.create(activity=activity, participant_id=participant_id)
        serializer = EnrollmentOutSerializer(enrollment)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EnrollmentDeleteView(APIView):
    @extend_schema(
        operation_id="deleteEnrollment",
        summary="Cancelar inscripción",
        description="Cancela la inscripción del participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER, PARTICIPANT_HEADER],
        responses={
            401:  OpenApiResponse(
                response=ErrorSerializer,
                description=INVALID_IDENTITY["message"],
            ),
            204: NO_CONTENT,
           
            405: METHOD_NOT_ALLOWED,
        },
    )
    def delete(self, request, activity_id):
        participant_id = get_participant_id(request)

        if not participant_id:
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
             return Response(
                ACTIVITY_NOT_FOUND,     
                status=status.HTTP_404_NOT_FOUND,
                )

        try:
            enrollment = Enrollment.objects.get(activity=activity, participant_id=participant_id)
        except Enrollment.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

