// Presentation only. Duration arithmetic and all validation stay on the server.
const reservationForm = document.querySelector("[data-reservation-form]");
if (reservationForm) {
  const updateCustomEnd = () => {
    const selected = reservationForm.querySelector('input[name="duration"]:checked');
    const custom = !selected || selected.value === "custom";
    reservationForm.querySelectorAll("[data-custom-end]").forEach((field) => {
      field.hidden = !custom;
      field.querySelectorAll("input, select").forEach((input) => {
        input.disabled = !custom;
        if (input.name === "end") input.required = custom;
      });
    });
  };
  reservationForm.querySelectorAll('input[name="duration"]').forEach((input) => {
    input.addEventListener("change", updateCustomEnd);
  });
  updateCustomEnd();
}
