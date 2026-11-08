/* =========================================================================
   Plateforme de cas cliniques - interactions front-end
   ========================================================================= */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {

    /* --- Menu mobile --------------------------------------------------- */
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var ouvert = links.classList.toggle("open");
        toggle.classList.toggle("open", ouvert);
        toggle.setAttribute("aria-expanded", ouvert ? "true" : "false");
      });
    }

    /* --- Fermeture des messages flash --------------------------------- */
    document.querySelectorAll(".alert-close").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var alerte = btn.closest(".alert");
        alerte.style.transition = "opacity .25s, transform .25s";
        alerte.style.opacity = "0";
        alerte.style.transform = "translateY(-8px)";
        setTimeout(function () { alerte.remove(); }, 250);
      });
    });
    // Disparition automatique des messages de succes / info apres 6 s
    document.querySelectorAll(".alert-success, .alert-info").forEach(function (a) {
      setTimeout(function () {
        var b = a.querySelector(".alert-close");
        if (b) b.click();
      }, 6000);
    });

    /* --- Confirmation avant suppression ------------------------------- */
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        if (!window.confirm(form.getAttribute("data-confirm"))) {
          e.preventDefault();
        }
      });
    });

    /* --- Apercu des images selectionnees ------------------------------ */
    document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
      input.addEventListener("change", function () {
        var ancien = input.parentNode.querySelector(".img-preview");
        if (ancien) ancien.remove();
        var fichier = input.files && input.files[0];
        if (fichier && fichier.type.startsWith("image/")) {
          var img = document.createElement("img");
          img.className = "img-preview";
          img.src = URL.createObjectURL(fichier);
          input.parentNode.appendChild(img);
        }
      });
    });

    /* --- Verification des mots de passe identiques -------------------- */
    var formInscription = document.querySelector('form[data-validate] #confirmation');
    if (formInscription) {
      var form = formInscription.closest("form");
      form.addEventListener("submit", function (e) {
        var mdp = form.querySelector("#mot_de_passe");
        if (mdp && mdp.value !== formInscription.value) {
          e.preventDefault();
          formInscription.setCustomValidity("Les mots de passe ne correspondent pas.");
          formInscription.reportValidity();
        } else {
          formInscription.setCustomValidity("");
        }
      });
    }
  });
})();
