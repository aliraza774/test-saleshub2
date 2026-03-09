"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from accounts.views import (
    AgeBandCreateView,
    AgeBandDeleteView,
    AuthPageView,
    CompaniesPageView,
    CompanyDeleteView,
    CompanyEditView,
    CompanySaveView,
    DashboardPageView,
    PlanCreateView,
    PlanDeleteView,
    ProductDeleteView,
    ProductDescriptionView,
    ProductEditView,
    ProductImportUploadView,
    ProductPriceListView,
    ProductPriceSaveView,
    ProductSaveView,
    ProductsPageView,
    QuoteDeleteView,
    QuoteEditView,
    QuoteRatesAPIView,
    QuoteSaveView,
    QuotesPageView,
    SettingsPageView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls', namespace='accounts')),
    path('', AuthPageView.as_view(), name='auth-page'),
    path('dashboard/', DashboardPageView.as_view(), name='dashboard'),
    path('companies/', CompaniesPageView.as_view(), name='companies'),
    path('products/', ProductsPageView.as_view(), name='products'),
    path('products/<uuid:pk>/', ProductDescriptionView.as_view(), name='product_description'),
    path('quotes/', QuotesPageView.as_view(), name='quotes'),
    path('quotes/rates/', QuoteRatesAPIView.as_view(), name='quote_rates'),
    path('settings/', SettingsPageView.as_view(), name='settings'),

    path('companies/save/', CompanySaveView.as_view(), name='company_save'),
    path('products/save/', ProductSaveView.as_view(), name='product_save'),
    path('quotes/save/', QuoteSaveView.as_view(), name='quote_save'),

    path('companies/<uuid:pk>/edit/', CompanyEditView.as_view(), name='company_edit'),
    path('companies/<uuid:pk>/delete/', CompanyDeleteView.as_view(), name='company_delete'),
    path('products/<uuid:pk>/edit/', ProductEditView.as_view(), name='product_edit'),
    path('products/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('products/prices/save/', ProductPriceSaveView.as_view(), name='product_price_save'),
    path('products/import/upload/', ProductImportUploadView.as_view(), name='product_import_upload'),
    path('products/<uuid:product_id>/prices/', ProductPriceListView.as_view(), name='product_price_list'),
    path('products/age-bands/create/', AgeBandCreateView.as_view(), name='age_band_create'),
    path('products/age-bands/<int:age_band_id>/delete/', AgeBandDeleteView.as_view(), name='age_band_delete'),
    path('products/plans/create/', PlanCreateView.as_view(), name='plan_create'),
    path('products/plans/<int:plan_id>/delete/', PlanDeleteView.as_view(), name='plan_delete'),
    path('quotes/<uuid:pk>/edit/', QuoteEditView.as_view(), name='quote_edit'),
    path('quotes/<uuid:pk>/delete/', QuoteDeleteView.as_view(), name='quote_delete'),
]
