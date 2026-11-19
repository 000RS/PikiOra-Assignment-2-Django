from django.urls import path
from . import views, api_views

urlpatterns = [
    # Original Django pages
    path('', views.home, name='home'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('slots/', views.available_slots, name='available_slots'),
    path('book/<int:slot_id>/', views.book_appointment, name='book_appointment'),

    path('my_appointments/', views.my_appointments, name='my_appointments'),
    path('my-appointments/<int:appointment_id>/edit/',
         views.edit_appointment, name='edit_appointment'),
    path('my-appointments/<int:appointment_id>/cancel/',
         views.cancel_appointment, name='cancel_appointment'),

    # Original staff pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/doctors/add',
         views.doctor_create, name='doctor_create'),
    path('dashboard/doctors/<int:doctor_id>/edit/',
         views.doctor_edit, name='doctor_edit'),
    path('dashboard/doctors/<int:doctor_id>/delete/',
         views.doctor_delete, name='doctor_delete'),

    path('dashboard/slots/add/',
         views.slot_create, name='slot_create'),
    path('dashboard/slots/<int:slot_id>/edit/',
         views.slot_edit, name='slot_edit'),
    path('dashboard/slots/<int:slot_id>/delete/',
         views.slot_delete, name='slot_delete'),

    path('dashboard/appointments/<int:appointment_id>/edit/',
         views.staff_appointment_edit, name='staff_appointment_edit'),
    path('dashboard/appointments/<int:appointment_id>/cancel/',
         views.staff_appointment_cancel, name='staff_appointment_cancel'),

    path('dashboard/patients/',
         views.patient_list, name='patient_list'),
    path('dashboard/patients/<int:patient_id>/toggle-active/',
         views.patient_toggle_active, name='patient_toggle_active'),

    # Assignment 2 REST APIs
    path('api/register/', api_views.register_api),
    path('api/login/', api_views.login_api),
    path('api/logout/', api_views.logout_api),
    path('api/me/', api_views.me_api),

    path('api/doctors/', api_views.doctors_api),
    path('api/doctors/<int:pk>/', api_views.doctor_detail_api),

    path('api/slots/', api_views.slots_api),
    path('api/slots/<int:pk>/', api_views.slot_detail_api),

    path('api/appointments/', api_views.appointments_api),
    path('api/appointments/<int:pk>/',
         api_views.appointment_detail_api),

    path('api/patients/', api_views.patients_api),
    path('api/patients/<int:pk>/', api_views.patient_detail_api),
]