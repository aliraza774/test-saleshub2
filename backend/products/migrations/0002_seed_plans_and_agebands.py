# Seed Plan and AgeBand from rate chart (e.g. Adamjee / Mednet)

from django.db import migrations


def seed_plans(apps, schema_editor):
    Plan = apps.get_model("products", "Plan")
    plans = [
        ("GOLD", "Gold", 1),
        ("SILVER_PREMIUM", "Silver Premium", 2),
        ("SILVER_CLASSIC", "Silver Classic", 3),
        ("GREEN", "Green", 4),
        ("EMERALD", "Emerald", 5),
        ("PEARL", "Pearl", 6),
        ("SILK_ROAD", "Silk Road", 7),
    ]
    for code, name, order in plans:
        Plan.objects.get_or_create(code=code, defaults={"name": name, "sort_order": order})


def seed_age_bands(apps, schema_editor):
    AgeBand = apps.get_model("products", "AgeBand")
    bands = [
        ("000-001", "0-1", 0, 1, 1),
        ("002-005", "2-5", 2, 5, 2),
        ("006-015", "6-15", 6, 15, 3),
        ("016-020", "16-20", 16, 20, 4),
        ("021-025", "21-25", 21, 25, 5),
        ("026-030", "26-30", 26, 30, 6),
        ("031-035", "31-35", 31, 35, 7),
        ("036-040", "36-40", 36, 40, 8),
        ("041-045", "41-45", 41, 45, 9),
        ("046-050", "46-50", 46, 50, 10),
        ("051-055", "51-55", 51, 55, 11),
        ("056-059", "56-59", 56, 59, 12),
        ("060", "60", 60, 60, 13),
        ("061-065", "61-65", 61, 65, 14),
        ("066-070", "66-70", 66, 70, 15),
        ("071-075", "71-75", 71, 75, 16),
        ("076-099", "76-99", 76, 99, 17),
    ]
    for code, label, min_a, max_a, order in bands:
        AgeBand.objects.get_or_create(
            code=code,
            defaults={"label": label, "min_age": min_a, "max_age": max_a, "sort_order": order},
        )


def reverse_plans(apps, schema_editor):
    Plan = apps.get_model("products", "Plan")
    Plan.objects.all().delete()


def reverse_age_bands(apps, schema_editor):
    AgeBand = apps.get_model("products", "AgeBand")
    AgeBand.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_plans),
        migrations.RunPython(seed_age_bands, reverse_age_bands),
    ]
