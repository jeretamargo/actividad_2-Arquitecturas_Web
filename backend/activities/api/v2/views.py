from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.aggregates import Count
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from . serializers import ActivityOutSerializer, EnrollmentOutSerializer, ErrorSerializer
from activities.models import Activity
from activities.models import Enrollment
import logging
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from uuid import uuid4
from django.contrib.auth import authenticate
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from rest_framework.permissions import AllowAny

from activities.models import Participant
from .serializers import LoginInSerializer
from activities.authentication import AccessTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed

from activities.models import RevokedToken


logger = logging.getLogger("app.activities")

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


METHOD_NOT_ALLOWED = OpenApiResponse(description="Método no permitido.")
NO_CONTENT = OpenApiResponse(description="Inscripción cancelada.")



def get_participant_id(request):
    try:
        return request.user.participant.id
    except Participant.DoesNotExist:
        raise PermissionDenied(
            "El usuario no tiene un participante asociado.",
            code="participant_required",
        )

class ParticipantAPIView(APIView):
    authentication_classes = [AccessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        response = super().handle_exception(exc)

        if response.status_code in (401, 403) and "detail" in response.data:
            detail = response.data["detail"]
            response.data = {
                "code": getattr(detail, "code", "authentication_error"),
                "message": str(detail),
            }

        return response
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
        logger.info("list_activities", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "list_activities", "result": "success"})
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
            logger.info("invalid_request", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "get_activity", "result": "not_found"})
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = ActivityOutSerializer(activity)
        logger.info("get_activity", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "get_activity", "result": "success"})
        return Response(serializer.data)

class EnrollmentListView(ParticipantAPIView):
    @extend_schema(
            operation_id="getEnrollments",
            summary="Obtener inscripciones",
            description="Devuelve las inscirpciones del participante ",
            tags=["Enrollments"],
            parameters=[ACTIVITY_ID_PARAMETER,],
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
            logger.info("invalid_request", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "get_enrollments", "result": "invalid_participant"})
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        enrollments = Enrollment.objects.filter(participant_id=participant_id);
        serializer = EnrollmentOutSerializer(enrollments, many=True)
        logger.info("get_enrollments", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "get_enrollments", "result": "success"})
        return Response(serializer.data)


class EnrollmentCreateView(ParticipantAPIView):
    @extend_schema(
        operation_id="createEnrollment",
        summary="Inscribirse en actividad",
        description="Crea una inscripción para el participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER],
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
            logger.info("enrollment_rejected", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "create_enrollment", "result": "invalid_participant"})
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
            logger.info("enrollment_rejected", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "create_enrollment", "result": "activity_not_found"})
            return Response(ACTIVITY_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        if(Enrollment.objects.filter(activity=activity, participant_id=participant_id).exists()):
            enrollment = Enrollment.objects.get(activity=activity, participant_id=participant_id)
            serializer = EnrollmentOutSerializer(enrollment)
            logger.info("enrollment_reused", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "create_enrollment", "result": "already_exists"})
            return Response(serializer.data,status=status.HTTP_200_OK)
        if(activity.capacity <= Enrollment.objects.filter(activity=activity).count()):
                   logger.info("enrollment_rejected", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "create_enrollment", "result": "capacity_exhausted"})
                   return Response(CAPACITY_EXHAUSTED, status=status.HTTP_409_CONFLICT)
        enrollment = Enrollment.objects.create(activity=activity, participant_id=participant_id)
        serializer = EnrollmentOutSerializer(enrollment)
        logger.info("enrollment_created", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "create_enrollment", "result": "success"})
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class EnrollmentDeleteView(ParticipantAPIView):
    @extend_schema(
        operation_id="deleteEnrollment",
        summary="Cancelar inscripción",
        description="Cancela la inscripción del participante en la actividad especificada.",
        tags=["Enrollments"],
        parameters=[ACTIVITY_ID_PARAMETER],
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
            logger.info("enrollment_rejected", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "delete_enrollment", "result": "invalid_participant"})
            return Response(
                INVALID_IDENTITY,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist:
             logger.info("enrollment_rejected", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "delete_enrollment", "result": "activity_not_found"})
             return Response(
                ACTIVITY_NOT_FOUND,     
                status=status.HTTP_404_NOT_FOUND,
                )

        try:
            enrollment = Enrollment.objects.get(activity=activity, participant_id=participant_id)
        except Enrollment.DoesNotExist:
            logger.info("enrollment_reused", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "delete_enrollment", "result": "enrollment_not_found"})

            return Response(status=status.HTTP_204_NO_CONTENT)
        enrollment.delete()
        logger.info("enrollment_deleted", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, "event": "delete_enrollment", "result": "success"})
        return Response(status=status.HTTP_204_NO_CONTENT)

def generate_access_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "username": user.username,
        "type": "access",
        "iat": now,
        "exp": now + settings.ACCESS_TOKEN_LIFETIME,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

def generate_refresh_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + settings.REFRESH_TOKEN_LIFETIME,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

class CsrfTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response({
            "csrf_token": get_token(request),
        })
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {
                    "code": "invalid_credentials",
                    "message": "Usuario o contraseña incorrectos.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not Participant.objects.filter(user=user).exists():
            return Response(
                {
                    "code": "participant_required",
                    "message": "El usuario no tiene un participante asociado.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        response = Response({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": int(
                settings.ACCESS_TOKEN_LIFETIME.total_seconds()
            ),
        })

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=int(
                settings.REFRESH_TOKEN_LIFETIME.total_seconds()
            ),
            httponly=True,
            secure=settings.REFRESH_COOKIE_SECURE,
            samesite="Lax",
            path="/api/v2/auth/",
        )
        response["Cache-Control"] = "no-store"

        return response
    
@method_decorator(csrf_protect, name="dispatch")
class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = AccessTokenAuthentication().decode_refresh_token(
                request.COOKIES.get("refresh_token")
            )

            if RevokedToken.objects.filter(jti=payload["jti"]).exists():
                raise AuthenticationFailed(
                    "El refresh token fue revocado.",
                    code="refresh_revoked",
                )

            User = get_user_model()

            try:
                user = User.objects.get(
                    pk=payload["sub"],
                    is_active=True,
                )
            except (
                User.DoesNotExist,
                ValueError,
                TypeError,
                OverflowError,
                ValidationError,
            ):
                raise AuthenticationFailed(
                    "El usuario no existe o está inactivo.",
                    code="invalid_user",
                )

            if not Participant.objects.filter(user=user).exists():
                raise PermissionDenied(
                    "El usuario no tiene un participante asociado.",
                    code="participant_required",
                )

            response = Response({
                "access_token": generate_access_token(user),
                "token_type": "Bearer",
                "expires_in": int(
                    settings.ACCESS_TOKEN_LIFETIME.total_seconds()
                ),
            })

        except (AuthenticationFailed, PermissionDenied) as exc:
            response = Response(
                {
                    "code": exc.get_codes(),
                    "message": str(exc.detail),
                },
                status=exc.status_code,
            )

        response["Cache-Control"] = "no-store"
        return response

@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.COOKIES.get("refresh_token")

        if token:
            try:
                payload = AccessTokenAuthentication().decode_refresh_token(
                    token
                )
            except AuthenticationFailed:
                pass
            else:
                RevokedToken.objects.get_or_create(
                    jti=payload["jti"]
                )

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            key="refresh_token",
            path="/api/v2/auth/",
            samesite="Lax",
        )
        response["Cache-Control"] = "no-store"
        return response