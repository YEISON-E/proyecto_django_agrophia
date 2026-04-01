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
});