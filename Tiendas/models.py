from usuarios.models import Shop as UsuarioShop


class Shop(UsuarioShop):
	class Meta:
		proxy = True
		app_label = "Tiendas"
