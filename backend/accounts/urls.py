from django.urls import path

from .views import CompanySignupView, CustomerSignupView, LandingView, LoginView, LogoutView, ProfileUpdateView


app_name = "accounts"

urlpatterns = [
    path("auth/signup/customer/", CustomerSignupView.as_view(), name="signup-customer"),
    path("auth/signup/company/", CompanySignupView.as_view(), name="signup-company"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("landing/", LandingView.as_view(), name="landing"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
]

