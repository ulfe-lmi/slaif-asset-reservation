(function () {
  "use strict";

  var tokenElement = document.getElementById("one-time-bearer-token");

  function scrubToken() {
    if (tokenElement) {
      tokenElement.textContent = "No longer available";
    }
  }

  window.addEventListener("pagehide", scrubToken);
  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      scrubToken();
    }
  });
})();
