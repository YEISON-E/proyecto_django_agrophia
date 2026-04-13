// Espera a que el HTML del documento este completamente cargado.
document.addEventListener("DOMContentLoaded", function () {
  // Referencia al contenedor visual del temporizador.
  var timer = document.getElementById("admin-code-timer");
  // Referencia al nodo donde se muestra el numero de segundos restantes.
  var remainingNode = document.getElementById("admin-code-remaining");
  // Referencia al input donde el usuario escribe el codigo.
  var codeInput = document.getElementById("code");
  // Referencia al boton de envio del formulario.
  var submitButton = document.getElementById("admin-code-submit");

  // Si faltan nodos criticos del temporizador, se cancela la ejecucion.
  if (!timer || !remainingNode) {
    // Sale sin ejecutar logica adicional.
    return;
  }

  // Lee segundos restantes desde data-remaining y los convierte a entero base 10.
  var remaining = parseInt(timer.dataset.remaining || "0", 10);
  // Lee URL de redireccion desde data-login-url o usa ruta por defecto.
  var loginUrl = timer.dataset.loginUrl || "/usuarios/login/";

  // Si remaining no es un numero valido, detiene la ejecucion.
  if (isNaN(remaining)) {
    // Sale sin iniciar temporizador.
    return;
  }

  // Guarda el identificador del setInterval para poder detenerlo luego.
  var intervalId = null;

  // Funcion que aplica estado de expiracion cuando el contador llega a cero.
  var setExpiredState = function () {
    // Agrega clase CSS para estilizar visualmente el estado expirado.
    timer.classList.add("admin-auth__timer--expired");
    // Reemplaza el texto del temporizador por mensaje de expiracion.
    timer.textContent = "El código expiró. Redirigiendo al login...";

    // Si existe input de codigo, lo deshabilita para evitar mas escritura.
    if (codeInput) {
      // Deshabilita el campo del codigo.
      codeInput.disabled = true;
    }
    // Si existe boton de envio, lo deshabilita para evitar nuevos submits.
    if (submitButton) {
      // Deshabilita el boton de confirmar codigo.
      submitButton.disabled = true;
    }

    // Espera 1.5 segundos antes de redirigir al login.
    window.setTimeout(function () {
      // Redirige al usuario a la URL de login.
      window.location.href = loginUrl;
    }, 1500);
  };

  // Funcion que renderiza el valor del contador o ejecuta expiracion.
  var render = function () {
    // Si el tiempo ya se agoto o es menor a cero.
    if (remaining <= 0) {
      // Si el intervalo esta activo, lo detiene.
      if (intervalId) {
        // Limpia el intervalo para que no siga ejecutandose.
        window.clearInterval(intervalId);
      }
      // Aplica la logica de expiracion visual y de redireccion.
      setExpiredState();
      // Sale para no seguir actualizando el contador.
      return;
    }

    // Muestra en pantalla la cantidad de segundos restantes.
    remainingNode.textContent = String(remaining);
  };

  // Render inicial del contador apenas carga la pagina.
  render();

  // Inicia intervalo que descuenta 1 segundo cada 1000 ms.
  intervalId = window.setInterval(function () {
    // Decrementa el contador en una unidad.
    remaining -= 1;
    // Vuelve a renderizar con el nuevo valor.
    render();
  }, 1000);
});
