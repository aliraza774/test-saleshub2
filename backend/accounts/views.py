import json
import uuid as uuid_module

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import login, logout
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Min, Max
from decimal import Decimal
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .models import User
from .serializers import LoginSerializer, SignupSerializer, ProfileSerializer

# Products app: companies and products (user-scoped)
from products.models import (
    Company,
    Product,
    CompanyProduct,
    Plan,
    AgeBand,
    CompanyProductPlan,
    CompanyProductAgeBand,
    ProductPrice,
)


def _parse_uuid(value):
    """Return UUID if value is a valid UUID string, else None."""
    if not value:
        return None
    try:
        return uuid_module.UUID(str(value).strip())
    except (ValueError, TypeError):
        return None


def _parse_int(value):
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


class CustomerSignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(
            data=request.data,
            context={"role": User.Role.CUSTOMER},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )


class CompanySignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SignupSerializer(
            data=request.data,
            context={"role": User.Role.COMPANY},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)
        return Response(
            {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class LandingView(APIView):
    """
    Simple landing endpoint for authenticated users.
    The React frontend can call this after login to fetch basic context.
    """

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {
                "message": "Welcome to Natroxia",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )


class LogoutView(APIView):
    """
    Log the user out of their Django session.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthPageView(TemplateView):
    template_name = "accounts/auth.html"

    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated, send them to dashboard
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class NeverCacheLoginRequiredMixin(LoginRequiredMixin):
    """LoginRequiredMixin + no-cache headers to prevent back-button bypass."""

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_complete"] = self.request.user.profile_complete
        return context



def _user_companies(request):
    """Companies belonging to the current user."""
    return Company.objects.filter(user=request.user)


def _user_products(request):
    """Products linked to at least one of the user's companies."""
    return Product.objects.filter(companies__user=request.user).distinct()


class DashboardPageView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = _user_companies(self.request)
        products = _user_products(self.request)
        context.update(
            {
                "companies_count": companies.count(),
                "products_count": products.count(),
                "quotes_count": 0,
                "pipeline_value": 0,
                "recent_companies": list(companies.order_by("-created_at")[:5]),
                "recent_quotes": [],
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class CompaniesPageView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/companies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = _user_companies(self.request).order_by("name")
        context.update({"companies": companies})
        return context


@method_decorator(never_cache, name="dispatch")
class ProductsPageView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = (
            _user_products(self.request)
            .prefetch_related("companies")
            .annotate(
                price_count=Count("product_prices"),
                min_rate=Min("product_prices__male_rate"),
                max_rate=Max("product_prices__female_rate"),
            )
            .order_by("name")
        )
        user_companies = _user_companies(self.request).order_by("name")
        context.update(
            {
                "products": products,
                "user_companies": user_companies,
                "user_companies_list": [{"id": c.id, "name": c.name} for c in user_companies],
                "products_for_import": [
                    {"id": p.id, "name": p.name, "company_ids": list(p.companies.values_list("id", flat=True))}
                    for p in products
                ],
                "plans": [],
                "age_bands": [],
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class ProductDescriptionView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/product_description.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        product = get_object_or_404(
            _user_products(self.request)
            .prefetch_related("companies")
            .distinct(),
            pk=pk,
        )
        linked_companies = product.companies.filter(user=self.request.user).order_by("name")
        context.update(
            {
                "product": product,
                "linked_companies": linked_companies,
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class QuotesPageView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/quotes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = _user_companies(self.request).order_by("name")
        plans = Plan.objects.all().order_by("sort_order")
        products = _user_products(self.request)
        categories = list(
            products.values_list("category", flat=True).distinct()
        )
        categories = [c for c in categories if c]
        context.update(
            {
                "quotes": [],
                "companies": companies,
                "plans": plans,
                "categories": sorted(categories),
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class SettingsPageView(NeverCacheLoginRequiredMixin, TemplateView):
    template_name = "accounts/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update({
            "gender_choices": User.Gender.choices,
        })
        return context


class ProfileUpdateView(APIView):
    """Update the authenticated user's age and gender."""

    def post(self, request, *args, **kwargs):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = request.user
        return Response({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "age": user.age,
            "gender": user.gender,
            "profile_complete": user.profile_complete,
        })


class QuoteRatesAPIView(LoginRequiredMixin, View):
    """GET quotation: rates for all products/plans based on DOB. Filters: plan_ids, company_id, category, gender."""

    def get(self, request):
        from products.utils import age_from_dob, get_age_band_for_age

        dob = request.GET.get("dob", "").strip()
        if not dob:
            return JsonResponse({"ok": False, "error": "Date of birth (dob) is required."}, status=400)
        age = age_from_dob(dob)
        if age is None:
            return JsonResponse({"ok": False, "error": "Invalid date of birth. Use YYYY-MM-DD."}, status=400)
        age_band = get_age_band_for_age(age)
        if not age_band:
            return JsonResponse({"ok": False, "error": f"No age band found for age {age}."}, status=400)
        plan_ids = request.GET.getlist("plan_ids") or request.GET.get("plan_ids", "").split(",")
        plan_ids = [x.strip() for x in plan_ids if x.strip()]
        company_id = request.GET.get("company_id", "").strip()
        category = request.GET.get("category", "").strip()
        gender = (request.GET.get("gender", "B") or "B").strip().upper()
        if gender not in ("M", "F", "B"):
            gender = "B"

        # Gender filter: B = only Both; M = Male (prefer M, fallback B); F = Female (prefer F, fallback B)
        qs = ProductPrice.objects.filter(
            company__user=request.user,
            age_band=age_band,
        ).select_related("product", "company", "plan")

        if plan_ids:
            qs = qs.filter(plan_id__in=plan_ids)
        company_pk = _parse_uuid(company_id)
        if company_pk:
            qs = qs.filter(company_id=company_pk)
        if category:
            qs = qs.filter(product__category=category)

        rows = list(qs.order_by("product__name", "company__name", "plan__sort_order"))

        out = []
        for p in rows:
            if gender == "F":
                rate_value = p.female_rate
            else:
                rate_value = p.male_rate
            if rate_value is None:
                continue
            out.append({
                "product_id": p.product_id,
                "product_name": p.product.name,
                "category": p.product.category or "",
                "company_id": p.company_id,
                "company_name": p.company.name,
                "plan_id": p.plan_id,
                "plan_code": p.plan.code,
                "plan_name": p.plan.name,
                "rate": str(rate_value),
                "gender": gender,
            })
        return JsonResponse({
            "ok": True,
            "age": age,
            "age_band": {"code": age_band.code, "label": age_band.label},
            "gender": gender,
            "results": out,
        })


class CompanySaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        from decimal import Decimal
        pk = request.POST.get("id", "").strip()
        name = (request.POST.get("name") or "").strip()
        if not name:
            return redirect("companies")
        industry = (request.POST.get("industry") or "").strip()
        contact_name = (request.POST.get("contact_name") or "").strip()
        contact_email = (request.POST.get("contact_email") or "").strip()
        status = request.POST.get("status") or Company.Status.ACTIVE
        broker_pct = request.POST.get("broker_commission_pct") or "0"
        tpa_name = (request.POST.get("tpa_name") or "").strip()
        try:
            broker_pct = Decimal(broker_pct)
        except Exception:
            broker_pct = Decimal("0")
        co_pk = _parse_uuid(pk)
        if co_pk:
            co = get_object_or_404(Company, pk=co_pk, user=request.user)
            co.name = name
            co.industry = industry
            co.contact_name = contact_name
            co.contact_email = contact_email
            co.status = status
            co.tpa_name = tpa_name
            co.broker_commission_pct = broker_pct
            co.save()
        else:
            Company.objects.create(
                user=request.user,
                name=name,
                industry=industry,
                contact_name=contact_name,
                contact_email=contact_email,
                status=status,
                tpa_name=tpa_name,
                broker_commission_pct=broker_pct,
            )
        return redirect("companies")


class ProductSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = request.POST.get("id", "").strip()
        name = (request.POST.get("name") or "").strip()
        if not name:
            return redirect("products")
        description = (request.POST.get("description") or "").strip()
        category = (request.POST.get("category") or "").strip()
        status = request.POST.get("status") or Product.Status.AVAILABLE
        company_ids = request.POST.getlist("companies")  # list of company IDs to link
        user_company_ids = set(
            _user_companies(request).values_list("id", flat=True)
        )
        product_pk = _parse_uuid(pk)
        if product_pk:
            product = get_object_or_404(Product, pk=product_pk)
            if not product.companies.filter(user=request.user).exists():
                return HttpResponseForbidden("Product not linked to your companies")
            product.name = name
            product.description = description
            product.category = category
            product.status = status
            product.save()
            # Update company links: only allow user's companies
            to_link = [
                _parse_uuid(x) for x in company_ids
                if _parse_uuid(x) is not None and _parse_uuid(x) in user_company_ids
            ]
            CompanyProduct.objects.filter(product=product).exclude(company_id__in=to_link).delete()
            for cid in to_link:
                CompanyProduct.objects.get_or_create(company_id=cid, product=product)
        else:
            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                status=status,
            )
            for cid in company_ids:
                cid_uuid = _parse_uuid(cid)
                if cid_uuid is not None and cid_uuid in user_company_ids:
                    CompanyProduct.objects.get_or_create(company_id=cid_uuid, product=product)
        return redirect("products")


class QuoteSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        return redirect("quotes")


class CompanyEditView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/companies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        companies = _user_companies(self.request).order_by("name")
        context["companies"] = companies
        context["company_edit"] = get_object_or_404(Company, pk=pk, user=self.request.user) if pk else None
        return context


class CompanyDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        company = get_object_or_404(Company, pk=pk, user=request.user)
        company.delete()
        return redirect("companies")


class ProductEditView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        products = (
            _user_products(self.request)
            .prefetch_related("companies")
            .annotate(
                price_count=Count("product_prices"),
                min_rate=Min("product_prices__male_rate"),
                max_rate=Max("product_prices__female_rate"),
            )
            .order_by("name")
        )
        context["products"] = products
        user_companies = _user_companies(self.request).order_by("name")
        context["user_companies"] = user_companies
        context["user_companies_list"] = [{"id": c.id, "name": c.name} for c in user_companies]
        context["products_for_import"] = [
            {"id": p.id, "name": p.name, "company_ids": list(p.companies.values_list("id", flat=True))}
            for p in products
        ]
        context["plans"] = []
        context["age_bands"] = []
        context["product_edit"] = None
        if pk:
            product = Product.objects.filter(
                companies__user=self.request.user
            ).filter(pk=pk).distinct().first()
            if product:
                context["product_edit"] = product
        return context


class ProductDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        product = get_object_or_404(
            Product,
            pk=pk,
            companies__user=request.user,
        )
        product.delete()
        return redirect("products")


class ProductPriceSaveView(LoginRequiredMixin, View):
    """Save price matrix for a product at a company (plan × age_band × gender)."""

    def post(self, request, *args, **kwargs):
        from decimal import Decimal, InvalidOperation
        product_id = request.POST.get("product_id")
        company_id = request.POST.get("company_id")
        if not product_id or not company_id:
            return redirect("products")
        product_pk = _parse_uuid(product_id)
        company_pk = _parse_uuid(company_id)
        if not product_pk or not company_pk:
            return redirect("products")
        product = get_object_or_404(Product, pk=product_pk)
        company = get_object_or_404(Company, pk=company_pk, user=request.user)
        if not product.companies.filter(pk=company_pk).exists():
            return HttpResponseForbidden("Product not linked to this company")
        # Keys like rate_<plan_id>_<age_band_id>_<gender> (e.g. rate_1_3_M)
        cells = {}
        for key, value in request.POST.items():
            if not key.startswith("rate_"):
                continue
            parts = key.replace("rate_", "").split("_")
            if len(parts) != 3:
                continue
            plan_id, age_band_id, gender = parts
            if gender not in ("M", "F"):
                continue
            cell_key = (plan_id, age_band_id)
            if cell_key not in cells:
                cells[cell_key] = {"M": None, "F": None}
            raw_value = (value or "").strip()
            if not raw_value:
                cells[cell_key][gender] = None
                continue
            try:
                cells[cell_key][gender] = Decimal(raw_value)
            except (InvalidOperation, ValueError):
                cells[cell_key][gender] = None

        for (plan_id, age_band_id), rates in cells.items():
            plan = Plan.objects.filter(pk=plan_id).first()
            age_band = AgeBand.objects.filter(pk=age_band_id).first()
            if not plan or not age_band:
                continue

            male_rate = rates.get("M")
            female_rate = rates.get("F")

            if male_rate is None and female_rate is None:
                ProductPrice.objects.filter(
                    company=company,
                    product=product,
                    plan=plan,
                    age_band=age_band,
                ).delete()
                continue

            CompanyProductPlan.objects.get_or_create(company=company, product=product, plan=plan)
            CompanyProductAgeBand.objects.get_or_create(company=company, product=product, age_band=age_band)
            ProductPrice.objects.update_or_create(
                company=company,
                product=product,
                plan=plan,
                age_band=age_band,
                defaults={"male_rate": male_rate, "female_rate": female_rate},
            )

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        return redirect("products")


class AgeBandCreateView(LoginRequiredMixin, View):
    """Create a new global AgeBand used by the price matrix. Auto-generates label from min/max."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = request.POST

        product_id = data.get("product_id")
        company_id = data.get("company_id")
        if not product_id or not company_id:
            return JsonResponse({"ok": False, "error": "Product and company are required."}, status=400)
        product_pk = _parse_uuid(product_id)
        company_pk = _parse_uuid(company_id)
        if not product_pk or not company_pk:
            return JsonResponse({"ok": False, "error": "Invalid product or company."}, status=400)
        product = Product.objects.filter(pk=product_pk, companies__user=request.user).first()
        company = Company.objects.filter(pk=company_pk, user=request.user).first()
        if not product or not company or not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({"ok": False, "error": "Invalid product/company selection."}, status=400)

        min_age_raw = (data.get("min_age") or "").strip()
        max_age_raw = (data.get("max_age") or "").strip()

        if not max_age_raw:
            return JsonResponse(
                {"ok": False, "error": "Max age is required."},
                status=400,
            )

        def _to_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        max_age = _to_int(max_age_raw)
        if max_age is None:
            return JsonResponse(
                {"ok": False, "error": "Max age must be a number."},
                status=400,
            )

        min_age = _to_int(min_age_raw)
        if min_age is None:
            min_age = max_age

        if min_age > max_age:
            min_age, max_age = max_age, min_age

        # Auto-generate label
        if min_age == max_age:
            label = f"{min_age}"
            base_code = f"{min_age:03d}"
        else:
            label = f"{min_age}-{max_age}"
            base_code = f"{min_age:03d}-{max_age:03d}"

        code = base_code
        suffix = 1
        while AgeBand.objects.filter(code=code).exists():
            suffix += 1
            code = f"{base_code}_{suffix}"

        max_sort = AgeBand.objects.aggregate(Max("sort_order")).get("sort_order__max") or 0
        age_band = AgeBand.objects.create(
            code=code,
            label=label,
            min_age=min_age,
            max_age=max_age,
            sort_order=max_sort + 1,
        )

        CompanyProductAgeBand.objects.get_or_create(
            company=company,
            product=product,
            age_band=age_band,
        )

        return JsonResponse(
            {
                "ok": True,
                "age_band": {
                    "id": str(age_band.id),
                    "code": age_band.code,
                    "label": age_band.label,
                    "min_age": age_band.min_age,
                    "max_age": age_band.max_age,
                },
            }
        )


class PlanCreateView(LoginRequiredMixin, View):
    """Create a new global Plan used by the price matrix."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = request.POST

        product_id = data.get("product_id")
        company_id = data.get("company_id")
        if not product_id or not company_id:
            return JsonResponse({"ok": False, "error": "Product and company are required."}, status=400)
        product_pk = _parse_uuid(product_id)
        company_pk = _parse_uuid(company_id)
        if not product_pk or not company_pk:
            return JsonResponse({"ok": False, "error": "Invalid product or company."}, status=400)
        product = Product.objects.filter(pk=product_pk, companies__user=request.user).first()
        company = Company.objects.filter(pk=company_pk, user=request.user).first()
        if not product or not company or not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({"ok": False, "error": "Invalid product/company selection."}, status=400)

        raw_code = (data.get("code") or "").strip()
        name = (data.get("name") or "").strip()

        if not raw_code:
            return JsonResponse(
                {"ok": False, "error": "Plan code is required."},
                status=400,
            )

        code = raw_code.upper().replace(" ", "_")
        if not name:
            name = code

        max_sort = Plan.objects.aggregate(Max("sort_order")).get("sort_order__max") or 0
        plan, created = Plan.objects.get_or_create(
            code=code,
            defaults={"name": name, "sort_order": max_sort + 1},
        )
        if not created and name and plan.name != name:
            plan.name = name
            plan.save(update_fields=["name"])

        CompanyProductPlan.objects.get_or_create(
            company=company,
            product=product,
            plan=plan,
        )

        return JsonResponse(
            {
                "ok": True,
                "plan": {
                    "id": str(plan.id),
                    "code": plan.code,
                    "name": plan.name,
                },
            }
        )


class AgeBandDeleteView(LoginRequiredMixin, View):
    """Delete an age band. Check if it's used in ProductPrice."""

    def post(self, request, age_band_id, *args, **kwargs):
        age_band_pk = _parse_int(age_band_id)
        if not age_band_pk:
            return JsonResponse({"ok": False, "error": "Invalid age band ID."}, status=400)

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = request.POST
        product_pk = _parse_uuid(data.get("product_id"))
        company_pk = _parse_uuid(data.get("company_id"))
        if not product_pk or not company_pk:
            return JsonResponse({"ok": False, "error": "Product and company are required."}, status=400)
        product = Product.objects.filter(pk=product_pk, companies__user=request.user).first()
        company = Company.objects.filter(pk=company_pk, user=request.user).first()
        if not product or not company or not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({"ok": False, "error": "Invalid product/company selection."}, status=400)

        age_band = AgeBand.objects.filter(pk=age_band_pk).first()
        if not age_band:
            return JsonResponse({"ok": False, "error": "Age band not found."}, status=404)

        ProductPrice.objects.filter(
            company=company,
            product=product,
            age_band=age_band,
        ).delete()
        CompanyProductAgeBand.objects.filter(
            company=company,
            product=product,
            age_band=age_band,
        ).delete()

        if not ProductPrice.objects.filter(age_band=age_band).exists() and not CompanyProductAgeBand.objects.filter(age_band=age_band).exists():
            age_band.delete()
        return JsonResponse({"ok": True})


class PlanDeleteView(LoginRequiredMixin, View):
    """Delete a plan. Check if it's used in ProductPrice."""

    def post(self, request, plan_id, *args, **kwargs):
        plan_pk = _parse_int(plan_id)
        if not plan_pk:
            return JsonResponse({"ok": False, "error": "Invalid plan ID."}, status=400)

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            data = request.POST
        product_pk = _parse_uuid(data.get("product_id"))
        company_pk = _parse_uuid(data.get("company_id"))
        if not product_pk or not company_pk:
            return JsonResponse({"ok": False, "error": "Product and company are required."}, status=400)
        product = Product.objects.filter(pk=product_pk, companies__user=request.user).first()
        company = Company.objects.filter(pk=company_pk, user=request.user).first()
        if not product or not company or not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({"ok": False, "error": "Invalid product/company selection."}, status=400)

        plan = Plan.objects.filter(pk=plan_pk).first()
        if not plan:
            return JsonResponse({"ok": False, "error": "Plan not found."}, status=404)

        ProductPrice.objects.filter(
            company=company,
            product=product,
            plan=plan,
        ).delete()
        CompanyProductPlan.objects.filter(
            company=company,
            product=product,
            plan=plan,
        ).delete()

        if not ProductPrice.objects.filter(plan=plan).exists() and not CompanyProductPlan.objects.filter(plan=plan).exists():
            plan.delete()
        return JsonResponse({"ok": True})


class ProductPriceListView(LoginRequiredMixin, View):
    """JSON: list prices for a product at a company (for loading into price matrix)."""

    def get(self, request, product_id):
        company_id = request.GET.get("company_id")
        if not company_id:
            return JsonResponse({"prices": []})
        company_pk = _parse_uuid(company_id)
        if not company_pk:
            return JsonResponse({"prices": []})
        product = Product.objects.filter(
            pk=product_id,
            companies__user=request.user,
        ).first()
        company = Company.objects.filter(pk=company_pk, user=request.user).first()
        if not product or not company or not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({"prices": []})
        prices = ProductPrice.objects.filter(
            product=product,
            company=company,
        ).select_related("plan", "age_band")
        scoped_plans = Plan.objects.filter(
            company_product_plans__company=company,
            company_product_plans__product=product,
        ).distinct().order_by("sort_order", "code")
        scoped_age_bands = AgeBand.objects.filter(
            company_product_age_bands__company=company,
            company_product_age_bands__product=product,
        ).distinct().order_by("sort_order", "code")

        if not scoped_plans.exists():
            scoped_plans = Plan.objects.filter(product_prices__company=company, product_prices__product=product).distinct().order_by("sort_order", "code")
        if not scoped_age_bands.exists():
            scoped_age_bands = AgeBand.objects.filter(product_prices__company=company, product_prices__product=product).distinct().order_by("sort_order", "code")
        out = [
            {
                "plan_id": p.plan_id,
                "age_band_id": p.age_band_id,
                "male_rate": str(p.male_rate) if p.male_rate is not None else "",
                "female_rate": str(p.female_rate) if p.female_rate is not None else "",
            }
            for p in prices
        ]
        return JsonResponse({
            "prices": out,
            "plans": [{"id": p.id, "name": p.name, "code": p.code} for p in scoped_plans],
            "age_bands": [
                {"id": ab.id, "label": ab.label, "code": ab.code, "min_age": ab.min_age, "max_age": ab.max_age}
                for ab in scoped_age_bands
            ],
        })


class ProductImportUploadView(LoginRequiredMixin, View):
    """Upload PDF/Excel/CSV to import rates for a product at a company. Optional broker_commission updates company."""

    def post(self, request):
        company_id = request.POST.get("company_id")
        product_id = request.POST.get("product_id")
        broker_commission = request.POST.get("broker_commission", "").strip()
        upload = request.FILES.get("file")
        if not company_id or not product_id:
            return JsonResponse({"ok": False, "error": "Company and product are required."}, status=400)
        company_pk = _parse_uuid(company_id)
        product_pk = _parse_uuid(product_id)
        if not company_pk or not product_pk:
            return JsonResponse({"ok": False, "error": "Invalid company or product."}, status=400)
        company = get_object_or_404(Company, pk=company_pk, user=request.user)
        product = Product.objects.filter(pk=product_pk).first()
        if not product:
            return JsonResponse({"ok": False, "error": "Product not found."}, status=400)
        if not product.companies.filter(pk=company_pk).exists():
            return JsonResponse({
                "ok": False,
                "error": "This product is not linked to the selected company. Edit the product and add this company under 'Link to companies', then try again.",
            }, status=400)
        if not upload:
            return JsonResponse({"ok": False, "error": "No file uploaded. Please select a file again."}, status=400)
        ext = (upload.name or "").lower().split(".")[-1]
        if ext not in ("pdf", "xlsx", "xls", "csv"):
            return JsonResponse({"ok": False, "error": "Use a PDF, Excel (.xlsx), or CSV file."}, status=400)
        if ext == "xls":
            return JsonResponse({"ok": False, "error": "Use .xlsx (Excel) instead of .xls."}, status=400)
        try:
            file_content = upload.read()
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Could not read file: {e}"}, status=400)
        if broker_commission:
            try:
                company.broker_commission_pct = Decimal(broker_commission)
                company.save(update_fields=["broker_commission_pct"])
            except Exception:
                pass
        try:
            from products.parsers import parse_upload
            rows = parse_upload(file_content, upload.name)
        except ValueError as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"Parse error: {e}"}, status=400)
        if not rows:
            return JsonResponse({
                "ok": False,
                "error": "No rate table found in the file. Ensure the file contains a table with plan names (e.g. GOLD, Silver Premium) and age bands (e.g. 0-1, 2-5).",
            }, status=400)
        plans_by_code = {p.code: p for p in Plan.objects.all()}
        age_bands_by_code = {ab.code: ab for ab in AgeBand.objects.all()}
        imported = 0
        errors = []
        for r in rows:
            plan = plans_by_code.get(r["plan_key"])
            age_band = age_bands_by_code.get(r["age_band_key"])
            if not plan or not age_band:
                errors.append(f"Unknown plan/age: {r.get('plan_key')}/{r.get('age_band_key')}")
                continue
            try:
                row, _ = ProductPrice.objects.get_or_create(
                    company=company,
                    product=product,
                    plan=plan,
                    age_band=age_band,
                )
                gender = (r.get("gender") or "B").upper()
                rate_value = Decimal(r["rate"])
                if gender == "F":
                    row.female_rate = rate_value
                elif gender == "M":
                    row.male_rate = rate_value
                else:
                    row.male_rate = rate_value
                    row.female_rate = rate_value
                row.save(update_fields=["male_rate", "female_rate"])
                CompanyProductPlan.objects.get_or_create(company=company, product=product, plan=plan)
                CompanyProductAgeBand.objects.get_or_create(company=company, product=product, age_band=age_band)
                imported += 1
            except Exception as e:
                errors.append(str(e))
        if imported == 0:
            return JsonResponse({
                "ok": False,
                "error": "No rates could be matched. Check that the file has plan names (e.g. GOLD, Silver Premium) and age bands (e.g. 0-1, 2-5) that match the system.",
            }, status=400)
        return JsonResponse({
            "ok": True,
            "imported": imported,
            "errors": errors[:20],
        })


class QuoteEditView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect("quotes")


class QuoteDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        return redirect("quotes")
