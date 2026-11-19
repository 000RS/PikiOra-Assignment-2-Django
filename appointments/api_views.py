from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import Doctor, AppointmentSlot, Appointment
from .serializers import (
    DoctorSerializer,
    AppointmentSlotSerializer,
    AppointmentSerializer,
    PatientSerializer,
)

User = get_user_model()


def error(message, code=status.HTTP_400_BAD_REQUEST):
    return Response({'error': message}, status=code)


def user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
    }


# Authentication APIs

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    username = str(request.data.get('username', '')).strip()
    password = str(request.data.get('password', ''))
    email = str(request.data.get('email', '')).strip()

    if not username or not password:
        return error('Username and password are required.')

    if User.objects.filter(username__iexact=username).exists():
        return error('Username already exists.')

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response(
            {'password': exc.messages},
            status=400
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=str(request.data.get('first_name', '')).strip(),
        last_name=str(request.data.get('last_name', '')).strip()
    )

    token = Token.objects.create(user=user)

    return Response({
        'token': token.key,
        'user': user_payload(user)
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    user = authenticate(
        request,
        username=request.data.get('username'),
        password=request.data.get('password')
    )

    if user is None:
        return error(
            'Invalid username or password.',
            status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': user_payload(user)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_api(request):
    return Response(user_payload(request.user))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    Token.objects.filter(user=request.user).delete()
    return Response({'message': 'Logged out.'})


# Doctor APIs

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def doctors_api(request):
    if request.method == 'GET':
        if request.user.is_authenticated and request.user.is_staff:
            doctors = Doctor.objects.all()
        else:
            doctors = Doctor.objects.filter(active=True)

        serializer = DoctorSerializer(
            doctors.order_by('name'),
            many=True
        )
        return Response(serializer.data)

    if not request.user.is_staff:
        return error('Administrator access required.', 403)

    serializer = DoctorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def doctor_detail_api(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == 'GET':
        if not doctor.active and not (
            request.user.is_authenticated and request.user.is_staff
        ):
            return error('Not found.', 404)

        return Response(DoctorSerializer(doctor).data)

    if not request.user.is_staff:
        return error('Administrator access required.', 403)

    if request.method == 'DELETE':
        if Appointment.objects.filter(slot__doctor=doctor).exists():
            return error(
                'Doctor has appointments. Deactivate instead of deleting.'
            )

        doctor.delete()
        return Response(status=204)

    serializer = DoctorSerializer(
        doctor,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


# Appointment Slot APIs

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def slots_api(request):
    if request.method == 'GET':
        slots = AppointmentSlot.objects.select_related(
            'doctor'
        ).order_by('date', 'start_time')

        if not (
            request.user.is_authenticated and request.user.is_staff
        ):
            slots = slots.filter(
                is_available=True,
                appointment__isnull=True,
                doctor__active=True,
                date__gte=timezone.localdate()
            )

        doctor_id = request.query_params.get('doctor')
        if doctor_id:
            slots = slots.filter(doctor_id=doctor_id)

        return Response(
            AppointmentSlotSerializer(slots, many=True).data
        )

    if not request.user.is_staff:
        return error('Administrator access required.', 403)

    serializer = AppointmentSlotSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdminUser])
def slot_detail_api(request, pk):
    slot = get_object_or_404(AppointmentSlot, pk=pk)

    if request.method == 'GET':
        return Response(AppointmentSlotSerializer(slot).data)

    if request.method == 'DELETE':
        if Appointment.objects.filter(slot=slot).exists():
            return error('Cannot delete a booked slot.')

        slot.delete()
        return Response(status=204)

    serializer = AppointmentSlotSerializer(
        slot,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)

    if (
        Appointment.objects.filter(slot=slot).exists()
        and request.data.get('is_available') is True
    ):
        return error('A booked slot cannot be marked available.')

    serializer.save()
    return Response(serializer.data)


# Appointment APIs

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointments_api(request):
    if request.method == 'GET':
        appointments = Appointment.objects.select_related(
            'slot__doctor',
            'patient'
        ).order_by('slot__date', 'slot__start_time')

        if not request.user.is_staff:
            appointments = appointments.filter(
                patient=request.user
            )

        serializer = AppointmentSerializer(
            appointments,
            many=True
        )
        return Response(serializer.data)

    slot_id = request.data.get('slot')

    if not slot_id:
        return error('Select a slot.')

    with transaction.atomic():
        slot = get_object_or_404(
            AppointmentSlot.objects.select_for_update(),
            pk=slot_id
        )

        if (
            not slot.doctor.active
            or slot.date < timezone.localdate()
            or not slot.is_available
            or Appointment.objects.filter(slot=slot).exists()
        ):
            return error(
                'This appointment slot is no longer available.'
            )

        try:
            with transaction.atomic():
                appointment = Appointment.objects.create(
                    patient=request.user,
                    slot=slot,
                    reason=request.data.get('reason', ''),
                    status='pending'
                )

                slot.is_available = False
                slot.save(update_fields=['is_available'])

        except IntegrityError:
            return error(
                'This appointment slot has already been booked.'
            )

    return Response(
        AppointmentSerializer(appointment).data,
        status=201
    )


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def appointment_detail_api(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'slot__doctor', 'patient'
        ),
        pk=pk
    )

    if (
        not request.user.is_staff
        and appointment.patient_id != request.user.id
    ):
        return error(
            'You may only manage your own appointments.',
            403
        )

    if request.method == 'GET':
        return Response(
            AppointmentSerializer(appointment).data
        )

    if request.method == 'DELETE':
        with transaction.atomic():
            slot = AppointmentSlot.objects.select_for_update().get(
                pk=appointment.slot_id
            )

            appointment.delete()
            slot.is_available = True
            slot.save(update_fields=['is_available'])

        return Response(status=204)

    if request.user.is_staff:
        allowed = {'reason', 'status'}
    else:
        allowed = {'reason'}

    if not set(request.data.keys()).issubset(allowed):
        return error(
            'Only ' + ', '.join(sorted(allowed)) +
            ' may be updated.'
        )

    serializer = AppointmentSerializer(
        appointment,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)

    if request.data.get('status') == 'cancelled':
        with transaction.atomic():
            slot = AppointmentSlot.objects.select_for_update().get(
                pk=appointment.slot_id
            )
            appointment.delete()
            slot.is_available = True
            slot.save(update_fields=['is_available'])

        return Response({
            'message': 'Appointment cancelled and slot released.'
        })

    serializer.save()
    return Response(serializer.data)


# Patient Administration APIs

@api_view(['GET'])
@permission_classes([IsAdminUser])
def patients_api(request):
    patients = User.objects.filter(
        is_staff=False
    ).order_by('username')

    return Response(
        PatientSerializer(patients, many=True).data
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def patient_detail_api(request, pk):
    patient = get_object_or_404(
        User,
        pk=pk,
        is_staff=False
    )

    serializer = PatientSerializer(
        patient,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    if not patient.is_active:
        Token.objects.filter(user=patient).delete()

    return Response(serializer.data)