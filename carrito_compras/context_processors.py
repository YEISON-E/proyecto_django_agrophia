def cart_nav_context(request):
    cart = request.session.get("shopping_cart", {}) or {}
    total_items = len(cart)

    return {
        "cart_items_count": total_items,
    }
