def cart_nav_context(request):
    cart = request.session.get("shopping_cart", {}) or {}
    total_items = 0

    for quantity in cart.values():
        try:
            total_items += max(0, int(quantity))
        except (TypeError, ValueError):
            continue

    return {
        "cart_items_count": total_items,
    }
