from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Doctor, AppointmentSlot, Appointment
from .forms import AppointmentForm, DoctorForm, AppointmentUpdateForm, AppointmentSlotForm, StaffAppointmentForm

# Views

def home(request):
    return render(request, 'appointments/home.html')

def doctor_list(request):
    doctors = Doctor.objects.filter(active=True)
    return render(request, 'appointments/doctor_list.html', {'doctors': doctors})

def available_slots(request):
    slots = AppointmentSlot.objects.filter(
        is_available=True,
        appointment__isnull=True).order_by('date','start_time')

    return render(request, 'appointments/available_slots.html',
       {"slots":slots})

@login_required
def book_appointment(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id,
    is_available=True)

    if Appointment.objects.filter(slot=slot).exists():
        return redirect("available_slots")

    if request.method == 'POST':
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.slot = slot
            appointment.save()

            slot.is_available = False
            slot.save()
            return redirect("available_slots")

    else:
            form = AppointmentForm()


    return render(
        request,
        'appointments/book_appointment.html',
        {'form': form, 'slot': slot}
    )


@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(patient=request.user).order_by('slot__date', 'slot__start_time')
    return render(request, 'appointments/my_appointments.html',
                 {'appointments': appointments})

@login_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully')
            return redirect('my_appointments')

    else:
        form = AppointmentUpdateForm(instance=appointment)
    return render(request, 'appointments/edit_appointment.html',
                     {'form': form, 'appointment': appointment})

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user)
    if request.method == 'POST':
        slot = appointment.slot
        appointment.delete()
        slot.is_available = True
        slot.save()

        messages.success(request, 'Appointment cancelled successfully')
        return redirect('my_appointments')

    return render(request, 'appointments/cancel_appointment.html',
                 {'appointment': appointment})

# STAFF CHECK

def staff_check(user):
    return user.is_authenticated and user.is_staff

# STAFF DASHBOARD
@user_passes_test(staff_check)
def dashboard(request):
    doctors = Doctor.objects.all()
    appointments = Appointment.objects.all().order_by('slot__date', 'slot__start_time')
    slots = AppointmentSlot.objects.all().order_by('date', 'start_time')
    patients = User.objects.filter(is_staff=False).order_by('username')

    context = {
        'doctors': doctors,
        'appointments': appointments,
        'slots': slots,
        'patients': patients
    }
    return render(request, 'appointments/dashboard.html', context)

# STAFF DOCTOR MANAGEMENT
@user_passes_test(staff_check)
def doctor_create(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor created successfully')
            return redirect('dashboard')

    else:
        form = DoctorForm()

    return render(request, 'appointments/doctor_form.html', {'form': form,'title': 'Create Doctor'})

@user_passes_test(staff_check)
def doctor_edit(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doctor updated successfully')
            return redirect('dashboard')

    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'appointments/doctor_form.html', {'form': form,
                                                             'title': 'Edit Doctor'})

@user_passes_test(staff_check)
def doctor_delete(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        doctor.delete()
        messages.success(request, 'Doctor deleted successfully')
        return redirect('dashboard')

    return render(request, 'appointments/doctor_delete.html', {'doctor': doctor})

# Appointment SLOT MANAGEMENT

@user_passes_test(staff_check)
def slot_create(request):
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment slot created successfully')
            return redirect('dashboard')

    else:
        form = AppointmentSlotForm()
    return render(request, 'appointments/slot_form.html', {'form': form,
                                                         'title': 'Create Appointment Slot'})

@user_passes_test(staff_check)
def slot_edit(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request_method =='POST':
        form = AppointmentSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment slot updated successfully')
            return redirect('dashboard')

    else:
        form = AppointmentSlotForm(instance=slot)
    return render(request, 'appointments/slot_form.html', {'form': form,
                                                         'title': 'Edit Appointment Slot'})


@user_passes_test(staff_check)
def slot_delete(request,slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Appointment slot deleted successfully')
        return redirect('dashboard')

    return render(request, 'appointments/slot_delete.html', {'slot': slot})

# STAFF APPOINTMENT MANAGEMENT

@user_passes_test(staff_check)
def staff_appointment_edit(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        form = StaffAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully')
            return redirect('dashboard')

    else:
        form = StaffAppointmentForm(instance=appointment)
    return render(request, 'appointments/staff_appointment_form.html', {'form': form,
                                                                'appointment': appointment })

@user_passes_test(staff_check)
def staff_appointment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        slot = appointment.slot
        slot.is_available = True
        slot.save()
        appointment.delete()
        messages.success(request, 'Appointment cancelled successfully')
        return redirect('dashboard')

    return render(request, 'appointments/staff_appointment_cancel.html', {'appointment': appointment})

# PATIENT ACCOUNT MANAGEMENT

@user_passes_test(staff_check)
def patient_list(request):
    patients = User.objects.filter(is_staff=False).order_by('username')
    return render(request, 'appointments/patient_list.html', {'patients': patients})



@user_passes_test(staff_check)
def patient_toggle_active(request, patient_id):
    patient = get_object_or_404(
        User,
        id=patient_id,
        is_staff=False
    )

    if request.method == 'POST':
        patient.is_active = not patient.is_active
        patient.save()

        if patient.is_active:
            messages.success(
                request,
                'Patient account activated.'
            )
        else:
            messages.success(
                request,
                'Patient account disabled.'
            )

    return redirect('patient_list')