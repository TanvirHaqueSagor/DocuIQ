from django.urls import re_path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, MeView, LogoutView, OrgEmployeeCreateView

urlpatterns = [
    re_path(r'^register/?$', RegisterView.as_view(), name='register'),
    re_path(r'^login/?$',    LoginView.as_view(),    name='login'),
    re_path(r'^refresh/?$',  TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r'^me/?$',       MeView.as_view(),       name='me'),
    re_path(r'^logout/?$',   LogoutView.as_view(),   name='logout'),
    re_path(r'^org/employees/?$', OrgEmployeeCreateView.as_view(), name='org_employee_create'),
]
