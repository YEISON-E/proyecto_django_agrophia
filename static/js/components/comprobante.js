// Inicia una funcion autoejecutable para encapsular variables y evitar colisiones globales.
(function () {
  // Activa modo estricto para prevenir errores comunes de JavaScript.
  'use strict';

  // Bloque: fecha/hora local usando la zona horaria del dispositivo del usuario.
  const localDateNodes = document.querySelectorAll('.receipt-local-datetime[data-iso]');
  // Si existen nodos con fecha ISO, los procesa uno por uno.
  if (localDateNodes.length) {
    // Recorre cada nodo de fecha encontrado en el documento.
    localDateNodes.forEach((node) => {
      // Lee la fecha ISO desde data-iso del elemento.
      const iso = node.dataset.iso;
      // Lee formato deseado desde data-format o usa "short" por defecto.
      const format = node.dataset.format || 'short';
      // Crea objeto Date con el valor ISO.
      const date = new Date(iso);
      // Si la fecha es invalida, salta este nodo.
      if (Number.isNaN(date.getTime())) {
        return;
      }

      // Define opciones de formato segun el tipo solicitado (long/short).
      const options = format === 'long'
        // Configuracion para formato largo con mes en texto.
        ? {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
            hourCycle: 'h12',
          }
        // Configuracion para formato corto con mes numerico.
        : {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
            hourCycle: 'h12',
          };

      // Formatea la fecha con locale es-CO y las opciones definidas.
      const formatted = new Intl.DateTimeFormat('es-CO', options).format(date);
      // Escribe el texto formateado en el nodo del comprobante.
      node.textContent = formatted;
    });
  }

  // Bloque: boton para compartir enlace del comprobante.
  const shareBtn = document.getElementById('shareBtn');
  // Si existe el boton compartir, registra su evento click.
  if (shareBtn) {
    // Maneja accion de compartir al hacer click.
    shareBtn.addEventListener('click', async function () {
      // Toma la URL actual de la pagina.
      const url   = window.location.href;
      // Define titulo a compartir desde data-title o usa document.title.
      const title = shareBtn.dataset.title || document.title;

      // Si el navegador soporta Web Share API, intenta compartir nativamente.
      if (navigator.share) {
        try {
          // Abre dialogo nativo de compartir.
          await navigator.share({ title, url });
        // Ignora errores comunes como cancelacion del usuario.
        } catch (_) { /* user cancelled */ }
      } else {
        // Fallback: intenta copiar la URL al portapapeles.
        try {
          // Copia enlace para compartir manualmente.
          await navigator.clipboard.writeText(url);
          // Muestra confirmacion visual de copiado.
          showToast('Enlace copiado al portapapeles');
        // Si falla el portapapeles, usa prompt como ultimo recurso.
        } catch (_) {
          // Abre cuadro para copiar enlace manualmente.
          prompt('Copia este enlace:', url);
        }
      }
    });
  }

  // Bloque: boton para imprimir comprobante.
  const printBtn = document.getElementById('printBtn');
  // Si existe el boton imprimir, registra su evento click.
  if (printBtn) {
    // Ejecuta impresion del documento actual.
    printBtn.addEventListener('click', function () {
      // Abre dialogo de impresion del navegador.
      window.print();
    });
  }

  // Helper: muestra un toast temporal con mensaje en pantalla.
  function showToast(message) {
    // Busca el elemento toast por su id.
    const toast = document.getElementById('shareToast');
    // Si no existe toast, termina la funcion.
    if (!toast) return;
    // Asigna el texto recibido al contenido del toast.
    toast.textContent = message;
    // Muestra el toast agregando clase CSS de visibilidad.
    toast.classList.add('show');
    // Oculta el toast despues de 2.5 segundos.
    setTimeout(() => toast.classList.remove('show'), 2500);
  }
// Cierra la funcion autoejecutable.
})();
