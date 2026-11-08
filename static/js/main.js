/* Plateforme de cas cliniques - interactions front-end */
(function () {
  "use strict";

  /* ---- Assistant multi-etapes ---- */
  var current = 0;
  var TOTAL = 10;

  window.goTo = function (index) {
    var sections = document.querySelectorAll(".form-section");
    var items = document.querySelectorAll(".step-item");
    if (!sections.length || index < 0 || index >= sections.length) return;
    current = index;
    sections.forEach(function (s, i) { s.classList.toggle("active", i === index); });
    items.forEach(function (it, i) {
      it.classList.toggle("active", i === index);
      it.classList.toggle("completed", i < index);
    });
    var wrap = document.querySelector(".wizard-form");
    if (wrap) window.scrollTo({ top: wrap.offsetTop - 80, behavior: "smooth" });
  };
  window.nextStep = function () { if (current < TOTAL - 1) window.goTo(current + 1); };
  window.prevStep = function () { if (current > 0) window.goTo(current - 1); };

  /* ---- Chips (cases a cocher stylees) ---- */
  window.toggleChip = function (cb) {
    var chip = cb.closest(".checkbox-chip");
    if (chip) chip.classList.toggle("checked", cb.checked);
  };

  document.addEventListener("DOMContentLoaded", function () {
    // Init compteur d'etapes reel
    var sections = document.querySelectorAll(".form-section");
    if (sections.length) TOTAL = sections.length;

    // Chips : refleter l'etat sur clic
    document.querySelectorAll(".checkbox-chip input[type=checkbox]").forEach(function (cb) {
      cb.addEventListener("change", function () { window.toggleChip(cb); });
    });

    // Menu mobile
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var ouvert = links.classList.toggle("open");
        toggle.setAttribute("aria-expanded", ouvert ? "true" : "false");
      });
    }

    // Fermeture des messages flash
    document.querySelectorAll(".alert-close").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var a = btn.closest(".alert");
        a.style.opacity = "0"; setTimeout(function () { a.remove(); }, 250);
      });
    });
    document.querySelectorAll(".alert-success, .alert-info").forEach(function (a) {
      setTimeout(function () { var b = a.querySelector(".alert-close"); if (b) b.click(); }, 6000);
    });

    // Confirmation avant suppression
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
      });
    });

    // Apercu des images (upload multiple)
    document.querySelectorAll('input[type="file"][accept^="image"]').forEach(function (input) {
      input.addEventListener("change", function () {
        var vieux = input.parentNode.querySelector(".img-preview-row");
        if (vieux) vieux.remove();
        if (!input.files.length) return;
        var row = document.createElement("div");
        row.className = "img-preview-row";
        Array.from(input.files).slice(0, 6).forEach(function (file) {
          if (file.type.startsWith("image/")) {
            var img = document.createElement("img");
            img.className = "img-preview";
            img.src = URL.createObjectURL(file);
            row.appendChild(img);
          }
        });
        input.parentNode.appendChild(row);
      });
    });

    // Verification mots de passe identiques
    var conf = document.querySelector('form[data-validate] #confirmation, form[data-validate] #mdp_confirme');
    if (conf) {
      var form = conf.closest("form");
      form.addEventListener("submit", function (e) {
        var mdp = form.querySelector("#mot_de_passe, #mdp_nouveau");
        if (mdp && mdp.value !== conf.value) {
          e.preventDefault();
          conf.setCustomValidity("Les mots de passe ne correspondent pas.");
          conf.reportValidity();
        } else { conf.setCustomValidity(""); }
      });
    }
  });
})();
