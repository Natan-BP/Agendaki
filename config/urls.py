from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('signup/', core_views.signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),

    path('meetings/create/', core_views.create_meeting_view, name='create_meeting'),
    path('meetings/<uuid:meeting_id>/', core_views.meeting_detail_view, name='meeting_detail'),
    path('meetings/<uuid:meeting_id>/slots/', core_views.manage_timeslots_view, name='manage_timeslots'),
    path('meetings/<uuid:meeting_id>/vote/', core_views.vote_view, name='vote_meeting'),

    path('', core_views.home_view, name='home'),
    path('meetings/<uuid:meeting_id>/confirm/<int:slot_id>/',
     core_views.confirm_slot_view, name='confirm_slot'),
    path('calendar/', core_views.calendar_view, name='calendar'),
    path('meetings/<uuid:meeting_id>/reopen/', core_views.reopen_meeting_view, name='reopen_meeting'),
    path('invite/<uuid:token>/', core_views.meeting_invite_view, name='meeting_invite'),
    path('meetings/<uuid:meeting_id>/slots/generate/', core_views.generate_slots_view, name='generate_slots'),
    path('logout/', LogoutView.as_view(template_name='logged_out.html'), name='logout'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
]
