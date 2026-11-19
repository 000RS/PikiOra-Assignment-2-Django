from django import forms
from .models import Appointment, Doctor, AppointmentSlot
from django.utils import timezone

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['reason']

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['reason',]
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, "placeholder":"Enter reason for appointment"})

        }

class StaffAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['reason', 'status']

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'email', 'phone', 'bio', 'active']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, })
        }

class AppointmentSlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot
        fields = [
            'doctor',
            'is_available',
            'date',
            'start_time',
            'end_time'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'})
        }

    def clean(self):
        cleaned_data = super().clean()

        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date and date < timezone.localdate():
            self.add_error(
                'date',
                'Appointment slots cannot be created in the past.'
            )

        if start_time and end_time and end_time <= start_time:
            self.add_error(
                'end_time',
                'End time must be after start time.'
            )

        if doctor and date and start_time:
            existing_slots = AppointmentSlot.objects.filter(
                doctor=doctor,
                date=date,
                start_time=start_time
            )

            if self.instance.pk:
                existing_slots = existing_slots.exclude(
                    pk=self.instance.pk
                )

            if existing_slots.exists():
                self.add_error(
                    'start_time',
                    'This doctor already has a slot at this time.'
                )

        return cleaned_data




