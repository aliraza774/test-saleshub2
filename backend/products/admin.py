from django.contrib import admin
from .models import Company, Product, CompanyProduct, Plan, AgeBand, ProductPrice


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "industry", "status", "created_at")
    list_filter = ("status", "industry")
    search_fields = ("name", "contact_name", "contact_email")


class CompanyProductInline(admin.TabularInline):
    model = CompanyProduct
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "description")
    inlines = [CompanyProductInline]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort_order")


@admin.register(AgeBand)
class AgeBandAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "min_age", "max_age", "sort_order")


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ("product", "company", "plan", "age_band", "male_rate", "female_rate")
    list_filter = ("company", "plan")
