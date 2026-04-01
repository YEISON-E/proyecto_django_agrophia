document.addEventListener("DOMContentLoaded", function () {
  const conversation = document.querySelector(".messages__conversation");
  if (conversation) {
    conversation.scrollTop = conversation.scrollHeight;
  }

  const replyTextarea = document.querySelector(".messages__reply-text");
  if (replyTextarea) {
    replyTextarea.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" || event.shiftKey) {
        return;
      }
      event.preventDefault();
      const form = replyTextarea.closest("form");
      if (form) {
        form.requestSubmit();
      }
    });
  }

  const backButton = document.querySelector(".messages__chat-back");
  if (backButton) {
    backButton.addEventListener("click", function () {
      // Allow default navigation on desktop and mobile fallback.
    });
  }
});