document.addEventListener("DOMContentLoaded", function () {
  var timer = document.getElementById("admin-code-timer");
  var remainingNode = document.getElementById("admin-code-remaining");
  var codeInput = document.getElementById("code");
  var submitButton = document.getElementById("admin-code-submit");

  if (!timer || !remainingNode) {
    return;
  }

  var remaining = parseInt(timer.dataset.remaining || "0", 10);
  var loginUrl = timer.dataset.loginUrl || "/usuarios/login/";

  if (isNaN(remaining)) {
    return;
  }

  var intervalId = null;

  var setExpiredState = function () {
    timer.classList.add("admin-auth__timer--expired");
    timer.textContent = "El codigo expiro. Redirigiendo al login...";

    if (codeInput) {
      codeInput.disabled = true;
    }
    if (submitButton) {
      submitButton.disabled = true;
    }

    window.setTimeout(function () {
      window.location.href = loginUrl;
    }, 1500);
  };

  var render = function () {
    if (remaining <= 0) {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
      setExpiredState();
      return;
    }

    remainingNode.textContent = String(remaining);
  };

  render();

  intervalId = window.setInterval(function () {
    remaining -= 1;
    render();
  }, 1000);
});
