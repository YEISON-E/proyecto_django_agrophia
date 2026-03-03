from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache

# Create your views here.


@never_cache
def shopping_cart(request):
	if not request.user.is_authenticated:
		return redirect("usuarios:login")
	return render(request, "carrito_compras/shopping-car.html")
