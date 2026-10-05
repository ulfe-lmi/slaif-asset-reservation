/* SLAIF Asset Reservation — administration form guidance (presentation only).
 *
 * Django's admin select-filter JavaScript (SelectFilter2) replaces the
 * delivered <select> with the id_<name>_from / id_<name>_to list boxes
 * during the window load event. The generated list boxes keep the field's
 * rendered help text next to them but carry no aria-describedby. This
 * helper adds that missing association for the actually rendered controls:
 * it points BOTH list boxes at the field's existing rendered help div
 * (id_<name>_helptext).
 *
 * It changes no validation, submission, filtering, movement or icon
 * behavior, adds no dependency, and does nothing on pages without
 * select filters. Re-running is idempotent.
 */
(function () {
  "use strict";

  function bindSelectFilterHelp() {
    var fromBoxes = document.querySelectorAll(
      ".selector .selector-available select[id$='_from']"
    );
    fromBoxes.forEach(function (from) {
      var baseId = from.id.slice(0, -"_from".length);
      var to = document.getElementById(baseId + "_to");
      var help = document.getElementById(baseId + "_helptext");
      if (!help) {
        return;
      }
      [from, to].forEach(function (box) {
        if (box && box.getAttribute("aria-describedby") !== help.id) {
          box.setAttribute("aria-describedby", help.id);
        }
      });
    });
  }

  function schedule() {
    var run = function () {
      bindSelectFilterHelp();
      // SelectFilter2 initializes on the same window load event; the
      // follow-up macrotask runs after its listener has finished, so the
      // generated list boxes exist by then.
      window.setTimeout(bindSelectFilterHelp, 0);
    };
    if (document.readyState === "complete") {
      run();
    } else {
      window.addEventListener("load", run);
    }
  }

  schedule();
})();
