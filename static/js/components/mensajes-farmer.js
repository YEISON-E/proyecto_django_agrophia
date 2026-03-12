document.addEventListener("DOMContentLoaded", function () {
  const conversation = document.querySelector(".messages__conversation");
  if (conversation) {
    conversation.scrollTop = conversation.scrollHeight;
  }

  const backButton = document.querySelector(".messages__chat-back");
  if (backButton) {
    backButton.addEventListener("click", function () {
      // Allow default navigation on desktop and mobile fallback.
    });
  }
});