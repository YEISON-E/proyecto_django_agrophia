document.addEventListener('DOMContentLoaded', function () {
  const shopAlert = document.getElementById('shop-created-alert');
  const shopConfirm = document.getElementById('shop-created-confirm');

  if (shopAlert && shopConfirm) {
    shopConfirm.addEventListener('click', function () {
      shopAlert.remove();
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    });
  }

  const blockedOverlay = document.getElementById('blocked-account-overlay');
  const blockedCloseBtn = document.getElementById('blocked-account-close');
  const blockedOpenMessageBtn = document.getElementById('blocked-account-open-message');
  const messageModal = document.getElementById('blocked-account-message-modal');
  const messageBackdrop = document.getElementById('blocked-account-message-backdrop');
  const messageCloseBtn = document.getElementById('blocked-account-message-close');
  const messageForm = document.getElementById('blocked-account-message-form');
  const messageTextarea = document.getElementById('blocked-account-message-text');
  const tokenInput = document.getElementById('blocked-account-token');
  const feedbackOverlay = document.getElementById('blocked-account-feedback-overlay');
  const feedbackMessage = document.getElementById('blocked-account-feedback-message');
  const feedbackClose = document.getElementById('blocked-account-feedback-close');

  if (!blockedOverlay || !blockedCloseBtn) {
    return;
  }

  const getCookie = function (name) {
    const cookieValue = document.cookie
      .split(';')
      .map((cookie) => cookie.trim())
      .find((cookie) => cookie.startsWith(name + '='));
    return cookieValue ? decodeURIComponent(cookieValue.split('=')[1]) : '';
  };

  const closeBlockedOverlay = function () {
    blockedOverlay.classList.add('profile-shop-alert-overlay--closing');
    blockedOverlay.setAttribute('aria-hidden', 'true');
    window.setTimeout(function () {
      blockedOverlay.classList.remove('profile-shop-alert-overlay--open', 'profile-shop-alert-overlay--closing');
    }, 180);
  };

  const showFeedback = function (messageText) {
    if (!feedbackOverlay || !feedbackMessage) {
      return;
    }
    feedbackMessage.textContent = messageText;
    feedbackOverlay.classList.remove('profile-shop-alert-overlay--closing');
    feedbackOverlay.classList.add('profile-shop-alert-overlay--open');
    feedbackOverlay.setAttribute('aria-hidden', 'false');
  };

  const closeFeedback = function () {
    if (!feedbackOverlay || !feedbackOverlay.classList.contains('profile-shop-alert-overlay--open')) {
      return;
    }
    feedbackOverlay.classList.add('profile-shop-alert-overlay--closing');
    feedbackOverlay.setAttribute('aria-hidden', 'true');
    window.setTimeout(function () {
      feedbackOverlay.classList.remove('profile-shop-alert-overlay--open', 'profile-shop-alert-overlay--closing');
    }, 180);
  };

  const openMessageModal = function () {
    if (!messageModal) {
      return;
    }
    messageModal.classList.add('seller-message-modal--open');
    messageModal.setAttribute('aria-hidden', 'false');
    if (messageTextarea) {
      messageTextarea.value = '';
    }
  };

  const closeMessageModal = function () {
    if (!messageModal) {
      return;
    }
    messageModal.classList.remove('seller-message-modal--open');
    messageModal.setAttribute('aria-hidden', 'true');
  };

  blockedCloseBtn.addEventListener('click', closeBlockedOverlay);
  blockedOverlay.addEventListener('click', function (event) {
    if (event.target === blockedOverlay) {
      closeBlockedOverlay();
    }
  });

  if (blockedOpenMessageBtn) {
    blockedOpenMessageBtn.addEventListener('click', function () {
      openMessageModal();
    });
  }

  if (messageCloseBtn) {
    messageCloseBtn.addEventListener('click', closeMessageModal);
  }

  if (messageBackdrop) {
    messageBackdrop.addEventListener('click', closeMessageModal);
  }

  if (feedbackClose) {
    feedbackClose.addEventListener('click', closeFeedback);
  }

  if (feedbackOverlay) {
    feedbackOverlay.addEventListener('click', function (event) {
      if (event.target === feedbackOverlay) {
        closeFeedback();
      }
    });
  }

  if (messageForm) {
    messageForm.addEventListener('submit', async function (event) {
      event.preventDefault();

      const endpoint = messageForm.dataset.endpoint;
      const token = tokenInput ? tokenInput.value : '';
      const messageText = (messageTextarea ? messageTextarea.value : '').trim();
      if (!endpoint || !token) {
        showFeedback('No se pudo preparar la solicitud. Intenta iniciar sesión nuevamente.');
        return;
      }

      const submitButton = messageForm.querySelector("button[type='submit']");
      if (submitButton) {
        submitButton.disabled = true;
      }

      try {
        const body = new FormData();
        body.append('token', token);
        body.append('message', messageText);

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: body,
          credentials: 'same-origin',
        });

        const data = await response.json();
        if (!response.ok || !data.ok) {
          throw new Error(data.error || 'No se pudo enviar el mensaje.');
        }

        closeMessageModal();
        showFeedback(data.message || 'Tu mensaje fue enviado al administrador.');
      } catch (error) {
        showFeedback(error.message || 'No se pudo enviar el mensaje al administrador.');
      } finally {
        if (submitButton) {
          submitButton.disabled = false;
        }
      }
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      closeMessageModal();
      closeFeedback();
    }
  });
});
