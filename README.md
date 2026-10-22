# AgroPhia

## Descripción

AgroPhia es una aplicación web desarrollada con **Django** que conecta directamente a **agricultores** y **clientes**. Los agricultores crean su tienda y publican sus productos del campo; los clientes los exploran, se comunican con el vendedor, los agregan al carrito y realizan pedidos. Además, un **panel de administración** propio permite gestionar usuarios, tiendas, productos y pedidos, y generar reportes en PDF.

El proyecto sigue el patrón **MVT** (Modelo - Vista - Plantilla) de Django y está dividido en aplicaciones independientes, cada una con sus modelos, vistas, rutas y plantillas HTML. El frontend se construye con plantillas de Django, CSS y JavaScript puro.

### Roles del sistema

| Rol | Qué puede hacer |
|-----|-----------------|
| **Cliente** | Registrarse, explorar productos, escribir a los vendedores, usar el carrito, pagar, consultar y cancelar pedidos, descargar comprobantes. |
| **Agricultor** | Crear y editar su tienda, publicar/editar/desactivar productos, responder mensajes de clientes, gestionar el estado de los pedidos recibidos. |
| **Administrador** | Acceder al panel `/administrador/` (protegido con verificación en dos pasos), gestionar usuarios, tiendas, productos y pedidos, enviar mensajes y generar reportes PDF. |

### Funcionalidades principales

- **Registro en dos pasos** con foto de perfil, selección de departamento y municipio de Colombia.
- **Inicio de sesión seguro**: bloqueo temporal tras intentos fallidos y notificación al administrador cuando un usuario bloqueado intenta ingresar.
- **Recuperación de contraseña** mediante código enviado por correo electrónico (con tiempo de expiración).
- **Tiendas**: creación en dos pasos, perfil público del vendedor, activar/desactivar tienda y soporte de punto físico.
- **Productos**: categorías (Frutas, Vegetales, Lácteos, Carne, Granos, Otros), unidades de medida validadas por categoría, stock, varias imágenes por producto, activar/desactivar y solicitud de reactivación al administrador.
- **Carrito de compras** y **checkout** con método de pago (Tarjeta, Nequi) y método de entrega (Recogido en tienda, Envío a domicilio).
- **Pedidos** con estados (Pendiente, Confirmado, En curso, Completado, Cancelado), ventana de cancelación de 7 horas y comprobante imprimible.
- **Mensajería** entre cliente y agricultor por producto, con respuestas en formato de conversación.
- **Panel administrativo**: CRUD de usuarios, tiendas, productos y pedidos; bloqueo/desbloqueo; mensajes individuales y masivos; notificaciones; reportes en PDF (ReportLab).

## Estructura del Proyecto

```
/proyecto_django_agrophia
│-- /agrophia/                     # Configuración principal del proyecto Django
│   ├── settings.py                # Apps instaladas, middlewares, base de datos, correo, idioma y zona horaria
│   ├── urls.py                    # Rutas raíz que incluyen las rutas de cada app
│   ├── views.py                   # Vistas base del sitio
│   ├── wsgi.py / asgi.py          # Puntos de entrada para servidores de despliegue
│
│-- /usuarios/                     # Registro, login, perfil, recuperación de contraseña y páginas legales
│   ├── models.py                  # Register (perfil de negocio y rol del usuario)
│   ├── views.py / urls.py
│   ├── middleware.py              # Limpia datos temporales del flujo de registro
│   ├── /management/commands/
│   │   └── crear_admin_agrophia.py  # Comando para crear/actualizar un administrador
│   ├── /migrations/
│   ├── /templates/usuarios/
│
│-- /Tiendas/                      # Tiendas de los agricultores
│   ├── models.py                  # Shop
│   ├── views.py / urls.py
│   ├── context_processors.py      # Datos de navegación de la tienda en las plantillas
│   ├── /migrations/
│   ├── /templates/tiendas/        # Páginas y /components/ reutilizables
│
│-- /Productos/                    # Catálogo de productos
│   ├── models.py                  # Product, ProductImage
│   ├── views.py / urls.py
│   ├── /migrations/
│   ├── /templates/productos/      # Páginas y /components/ (tarjetas, formularios, detalle)
│
│-- /carrito_compras/              # Carrito y checkout
│   ├── views.py / urls.py
│   ├── context_processors.py      # Contador del carrito en la barra de navegación
│   ├── /templates/carrito_compras/
│
│-- /Pedidos/                      # Pedidos y comprobantes
│   ├── models.py                  # Order, OrderItem
│   ├── views.py / urls.py
│   ├── /migrations/
│   ├── /templates/pedidos/
│
│-- /Mensajes/                     # Mensajería y notificaciones
│   ├── models.py                  # CustomerMessage, FarmerReply, AdminToUserMessage, AdminNotification
│   ├── views.py / urls.py
│   ├── /migrations/
│   ├── /templates/mensajes/
│
│-- /Administrador/                # Panel administrativo
│   ├── views.py / urls.py
│   ├── middleware.py              # AdminTwoFactorMiddleware (protege /administrador/)
│   ├── context_processors.py
│   ├── departamentos_municipios.py  # Datos de departamentos y municipios
│   ├── tests.py                   # Pruebas del panel admin
│   ├── /templates/administrador/  # Páginas y /componentes/ (tablas, toolbars, tarjetas, sidebar)
│
│-- /static/                       # Archivos estáticos globales
│   ├── /css/                      # Estilos por página y por componente
│   ├── /js/                       # Scripts del frontend (+ /components/)
│   ├── /img/                      # Imágenes
│   ├── /icons/                    # Iconos
│
│-- /media/                        # (se genera) Fotos de perfil y de productos subidas por los usuarios
│-- /session_files/                # Archivos de sesión
│-- manage.py                      # Utilidad de línea de comandos de Django
│-- requirements.txt               # Dependencias de Python
│-- .gitignore                     # Archivos y carpetas a ignorar en Git
│-- LICENSE                        # Licencia CC0 1.0 Universal
│-- README.md                      # Documentación del proyecto
```

## Descripción detallada estructura

📂 **/agrophia/**
Configuración global del proyecto.

- `settings.py` → Define las apps instaladas, los middlewares, los *context processors*, la base de datos, el idioma (`es-co`), la zona horaria (`America/Bogota`), los archivos estáticos/media y el correo SMTP.
- `urls.py` → Enruta cada prefijo a su aplicación (`/usuarios/`, `/tiendas/`, `/productos/`, `/carrito/`, `/mensajes/`, `/pedidos/`, `/administrador/`).

📂 **/usuarios/**
Autenticación y perfiles. El modelo `Register` guarda los datos de negocio de la persona (documento, contacto, ubicación, estado/rol, intentos fallidos de login) y se enlaza con el `User` de Django mediante `id_usuario`.

📂 **/Tiendas/**
Modelo `Shop` (nombre, contacto, ubicación, horario, punto físico, estado activo) y vistas para crear, editar, activar y desactivar la tienda, además del perfil público del vendedor.

📂 **/Productos/**
Modelos `Product` y `ProductImage`. Incluye validaciones de negocio en `clean()` (nombre, descripción, precio mayor que 0, stock mínimo, unidad válida según la categoría) y restricciones de base de datos para precio y stock.

📂 **/carrito_compras/**
Carrito de compras guardado en sesión y proceso de *checkout* que valida el método de pago, el método de entrega, la dirección y el stock, y crea el pedido.

📂 **/Pedidos/**
Modelos `Order` y `OrderItem`. Vistas para que el cliente consulte, cancele y descargue el comprobante, y para que el agricultor revise y actualice el estado de los pedidos recibidos.

📂 **/Mensajes/**
Mensajes cliente → agricultor asociados a un producto, respuestas del agricultor, mensajes del administrador a los usuarios y notificaciones para el administrador (por ejemplo, solicitudes de reactivación de productos o intentos de ingreso de usuarios bloqueados).

📂 **/Administrador/**
Panel de gestión protegido. El middleware `AdminTwoFactorMiddleware` exige que el usuario esté autenticado, tenga rol de administrador y valide un código de seguridad antes de entrar a cualquier ruta bajo `/administrador/`.

📂 **/static/**
CSS, JavaScript e imágenes. Los estilos y scripts están separados por página o componente.

📂 **/media/**
Se crea automáticamente al subir archivos. No se versiona en Git.

## Instalación

### Requisitos previos

- Python 3.10 o superior (requerido por Django 5.2) y `pip`
- Git
- Base de datos: **SQLite** (incluida con Python, es la configuración por defecto). Opcionalmente MySQL o PostgreSQL, ya que `requirements.txt` incluye `mysqlclient` y `psycopg`.
- Una cuenta de correo con SMTP habilitado (por defecto Gmail con contraseña de aplicación) para la recuperación de contraseña y el código de verificación del administrador.

### Clonar el repositorio

```sh
git clone <URL-DEL-REPOSITORIO>
cd proyecto_django_agrophia-dev
```

### Creación del entorno y dependencias

```sh
# Crear el entorno virtual
python -m venv venv

# Activarlo
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

# Instalar las dependencias
pip install -r requirements.txt
```

> **Nota:** `mysqlclient` necesita las librerías de desarrollo de MySQL en algunos sistemas (en Linux, por ejemplo, `libmysqlclient-dev` y `pkg-config`). Si solo usarás SQLite y la instalación falla, puedes quitarlo temporalmente de `requirements.txt`.

### Configuración

Las opciones se encuentran en `agrophia/settings.py`:

| Configuración | Valor por defecto | Descripción |
|---------------|-------------------|-------------|
| `DATABASES` | SQLite (`db.sqlite3`) | Para usar MySQL o PostgreSQL, cambia `ENGINE` y agrega `NAME`, `USER`, `PASSWORD`, `HOST` y `PORT`. |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | Cuenta de ejemplo del proyecto | Usa tu propia cuenta SMTP y una contraseña de aplicación. |
| `SESSION_COOKIE_AGE` | 3600 s | La sesión expira en 1 hora. |
| `PASSWORD_RESET_TIMEOUT` | 300 s | Vigencia del enlace/código de recuperación. |
| `DEBUG` / `ALLOWED_HOSTS` | `True` / `[]` | Solo para desarrollo. |

> ⚠️ **Seguridad:** `SECRET_KEY` y las credenciales de correo están escritas directamente en `settings.py`. Antes de publicar el repositorio o desplegar en producción, muévelas a variables de entorno (por ejemplo, con un archivo `.env`, que ya está en `.gitignore`), pon `DEBUG = False`, define `ALLOWED_HOSTS` y **cambia las credenciales actuales**.

### Base de datos y servidor

```sh
# Aplicar las migraciones (crea las tablas)
python manage.py migrate

# Crear el administrador del sistema
python manage.py crear_admin_agrophia \
  --documento 1234567890 \
  --email admin@correo.com \
  --nombres "Nombre" \
  --apellidos "Apellido" \
  --telefono 3000000000 \
  --password "UnaContraseñaSegura123"

# Iniciar el servidor de desarrollo
python manage.py runserver
```

El comando `crear_admin_agrophia` crea o actualiza el `User` de Django y su perfil `Register` con rol de administrador. Opciones adicionales: `--tipo-documento`, `--departamento`, `--municipio` y `--direccion`. El documento debe tener entre 8 y 10 dígitos y la contraseña al menos 8 caracteres.

## Uso

- Acceder a la aplicación en `http://127.0.0.1:8000/`
- Acceder al panel administrativo en `http://127.0.0.1:8000/administrador/home/`
  (al iniciar sesión como administrador se solicita un código de verificación enviado al correo)

### Rutas principales

| Prefijo | App | Ejemplos |
|---------|-----|----------|
| `/` | usuarios | Página de inicio |
| `/usuarios/` | usuarios | `login/`, `register/`, `forgot-password/`, `profile/`, `productos/` |
| `/tiendas/` | Tiendas | `interface-farmer/`, `create-shop/`, `profile-shop/`, `seller/<id>/` |
| `/productos/` | Productos | `create-product/`, `update-product/<id>/`, `descripcion-product/<id>/`, `disabled-products/` |
| `/carrito/` | carrito_compras | `shopping-cart/`, `add/`, `checkout/` |
| `/pedidos/` | Pedidos | `mis-pedidos/`, `pedidos-farmer/`, `mis-pedidos/<id>/comprobante/` |
| `/mensajes/` | Mensajes | `enviados/`, `recibidos-agricultor/`, `enviar/` |
| `/administrador/` | Administrador | `home/`, `usuarios/`, `tiendas/`, `productos/`, `pedidos/`, `notificaciones/` |

## Pruebas

Ejecutar las pruebas con el comando de Django:

```sh
# Todas las pruebas
python manage.py test

# Solo las del panel administrativo
python manage.py test Administrador
```

Actualmente las pruebas implementadas están en `Administrador/tests.py` (envío masivo de mensajes desde el panel admin). Los archivos `tests.py` de las demás aplicaciones están creados y pendientes de completar.

## Contribución

1. Hacer un fork del repositorio (crear una copia del repositorio en tu propia cuenta.)
2. Crear una rama (`feature-nueva`)
3. Realizar cambios y hacer commit
4. Crear un pull request

## Flujo

Resumen del flujo de una petición (patrón MVT de Django)

1. El navegador envía una petición HTTP (Ej: `GET /productos/descripcion-product/5/`)
2. Los middlewares la procesan (sesión, limpieza del registro, CSRF, autenticación, verificación 2FA del admin si la ruta empieza por `/administrador/`)
3. `agrophia/urls.py` la dirige a la app correspondiente (`Productos/urls.py`)
4. La ruta llama a la vista (`Productos/views.py`)
5. La vista aplica la lógica de negocio y consulta los modelos (`Productos/models.py`), que acceden a la base de datos mediante el ORM de Django
6. La vista renderiza una plantilla (`Productos/templates/productos/...`) con apoyo de los *context processors* y los archivos de `static/`
7. La respuesta viaja de regreso: Plantilla → Vista → Middlewares → Navegador

### Flujo de compra

1. El cliente agrega productos al carrito (`/carrito/add/`)
2. En el *checkout* elige método de pago y de entrega; el sistema valida stock, dirección y disponibilidad de recogida en tienda
3. Se crea el pedido (`Order` + `OrderItem`) en estado **Pendiente**
4. El cliente puede cancelarlo durante las primeras 7 horas mientras siga pendiente
5. El agricultor lo gestiona hasta dejarlo **Completado**, y el cliente puede descargar el comprobante

### Prefijos para indicar el tipo de cambio en GitHub:

1. feat: (feature/funcionalidad) Nueva funcionalidad.
2. fix: Corrección de errores.
3. docs: Cambios en la documentación.
4. style: Cambios en el formato del código (sin afectar la lógica).
5. refactor: Refactorización del código (sin cambios en la funcionalidad).
6. test: Adición o modificación de pruebas.
7. chore: Cambios en el proceso de construcción o herramientas auxiliares.

## Ejemplos

1. feat: Agregar validación de stock en el checkout
2. fix: Corregir el bloqueo de usuario tras intentos fallidos de login
3. docs: Actualizar el README con los pasos de instalación

## Licencia

Este proyecto se distribuye bajo la licencia **CC0 1.0 Universal**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
