from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Doctor, AppointmentSlot, Appointment


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'specialization',
            'phone', 'email', 'bio', 'active'
        ]


class AppointmentSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(
        source='doctor.name',
        read_only=True
    )

    class Meta:
        model = AppointmentSlot
        fields = [
            'id', 'doctor', 'doctor_name',
            'date', 'start_time', 'end_time',
            'is_available'
        ]

    def validate(self, attrs):
        start = attrs.get(
            'start_time',
            getattr(self.instance, 'start_time', None)
        )
        end = attrs.get(
            'end_time',
            getattr(self.instance, 'end_time', None)
        )

        if start and end and end <= start:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })

        return attrs


class AppointmentSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(
        source='patient.username',
        read_only=True
    )
    doctor_name = serializers.CharField(
        source='slot.doctor.name',
        read_only=True
    )
    date = serializers.DateField(
        source='slot.date',
        read_only=True
    )
    start_time = serializers.TimeField(
        source='slot.start_time',
        read_only=True
    )
    end_time = serializers.TimeField(
        source='slot.end_time',
        read_only=True
    )

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_username',
            'slot', 'doctor_name', 'date',
            'start_time', 'end_time',
            'reason', 'status'
        ]
        read_only_fields = ['patient']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_active'
        ]
        read_only_fields = ['id', 'username']