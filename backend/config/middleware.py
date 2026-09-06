
import uuid
import logging

logger = logging.getLogger("app.http")

class CorrelationIdMiddleware:
   

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Antes de ejecutar el view
        correlation_id = str(request.headers.get("X-Correlation-ID") or str(uuid.uuid4()))
        request.correlation_id = correlation_id


        logger.info("request_received", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, })

        # Despues de ejecutar el view
        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id
        logger.info("request_completed", extra={"correlation_id": request.correlation_id, "method": request.method, "path": request.path, })
        return response