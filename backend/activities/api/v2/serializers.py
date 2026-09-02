from rest_framework import serializers

class AvailabilitySerializer(serializers.Serializer):
    capacity = serializers.IntegerField()
    available_slots = serializers.SerializerMethodField()

    def get_available_slots(self, activity):
        enrolled_count = getattr(activity, "enrolled_count", None)

        if enrolled_count is None:
            enrolled_count = activity.enrollments.count()

        return max(activity.capacity - enrolled_count, 0)
    
class ActivityOutSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Identificador único de la actividad.")
    title = serializers.CharField(help_text="Nombre visible de la actividad.")
    starts_at = serializers.DateTimeField(
        help_text="Fecha y hora de inicio en formato ISO 8601."
    )

    capacity = serializers.IntegerField(
        min_value=0,
        help_text="Cantidad máxima de participantes.",
    )
    availability = AvailabilitySerializer(source="*", read_only=True) # * en el atributo source le pasa al serializer la instancia de Activity