from .models import Shop


def shop_nav_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "has_active_shop": False,
            "has_inactive_shop": False,
        }

    return {
        "has_active_shop": Shop.objects.filter(owner=user, is_active=True).exists(),
        "has_inactive_shop": Shop.objects.filter(owner=user, is_active=False).exists(),
    }
