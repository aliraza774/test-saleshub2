"""
Schema: User → Companies; Product ↔ Companies (M2M); Price by Plan + AgeBand per Company.

- Each user can register multiple companies.
- Each company has many products (and each product can be linked to multiple companies).
- Each product has price ranges per company: by plan and by age group (and optionally gender).
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models


class Company(models.Model):
    """Company registered by a user (broker/agent)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PROSPECT = "prospect", "Prospect"
        INACTIVE = "inactive", "Inactive"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="companies",
    )
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    # TPA / broker context (from rate charts)
    tpa_name = models.CharField(max_length=120, blank=True)
    broker_commission_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Broker commission % (e.g. 15.5)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product (e.g. insurance product). Can be linked to multiple companies."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        LIMITED = "limited", "Limited"
        OUT = "out", "Out of Stock"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Many-to-many: product can be offered by multiple companies
    companies = models.ManyToManyField(
        Company,
        related_name="products",
        through="CompanyProduct",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CompanyProduct(models.Model):
    """Explicit link between a company and a product (for future metadata)."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="company_products")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["company", "product"]]
        verbose_name = "Company–Product link"
        verbose_name_plural = "Company–Product links"

    def __str__(self):
        return f"{self.company.name} — {self.product.name}"


class Plan(models.Model):
    """Network/plan type (e.g. GOLD, SILVER PREMIUM). Plans are the same for male and female;
    rate charts have separate MALE/FEMALE columns per plan, not separate plans."""

    code = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self):
        return self.name or self.code


class AgeBand(models.Model):
    """Age band for pricing (e.g. [000-001], [002-005])."""

    code = models.CharField(max_length=20, unique=True)
    label = models.CharField(max_length=80)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self):
        return self.label or self.code


class CompanyProductPlan(models.Model):
    """Scope a plan to a specific company+product pair."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_product_plans")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="company_product_plans")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="company_product_plans")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["company", "product", "plan"]]
        ordering = ["company", "product", "plan"]


class CompanyProductAgeBand(models.Model):
    """Scope an age band to a specific company+product pair."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_product_age_bands")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="company_product_age_bands")
    age_band = models.ForeignKey(AgeBand, on_delete=models.CASCADE, related_name="company_product_age_bands")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["company", "product", "age_band"]]
        ordering = ["company", "product", "age_band"]


class ProductPrice(models.Model):
    """Price for a product at a company, by plan and age band, with separate male/female rates in one row."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="product_prices")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_prices")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="product_prices")
    age_band = models.ForeignKey(AgeBand, on_delete=models.CASCADE, related_name="product_prices")
    male_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    female_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [["company", "product", "plan", "age_band"]]
        ordering = ["company", "product", "plan", "age_band"]

    def __str__(self):
        return f"{self.product.name} @ {self.company.name} | {self.plan.code} | {self.age_band.code} | M:{self.male_rate} F:{self.female_rate}"
