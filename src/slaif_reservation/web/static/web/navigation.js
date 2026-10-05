/* Accessible application navigation; no data, requests or stored state. */
(function () {
  "use strict";
  const header = document.querySelector(".site-header");
  const toggle = document.querySelector(".nav-toggle");
  if (header && toggle) {
    header.classList.add("nav-ready");
    toggle.addEventListener("click", function () {
      const open = header.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && header.classList.contains("is-open")) {
        header.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }
  document.querySelectorAll("nav a[href]").forEach(function (link) {
    const path = link.getAttribute("href");
    if (path === window.location.pathname || (path !== "/" && window.location.pathname.startsWith(path))) {
      link.setAttribute("aria-current", "page");
    }
  });
})();
