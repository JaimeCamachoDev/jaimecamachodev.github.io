// Tema claro/oscuro y filtro del portfolio. Sin dependencias.
(function () {
  "use strict";

  // --- Tema ---
  var raiz = document.documentElement;
  function ponerTema(t) {
    raiz.setAttribute("data-tema", t);
    try { localStorage.setItem("tema", t); } catch (e) {}
  }
  var boton = document.querySelector(".cambiar-tema");
  if (boton) {
    boton.addEventListener("click", function () {
      ponerTema(raiz.getAttribute("data-tema") === "claro" ? "oscuro" : "claro");
    });
  }

  // --- Filtro ---
  var portfolio = document.querySelector(".portfolio");
  var caja = document.getElementById("filtro-texto");
  if (!portfolio || !caja) return;

  var chips = Array.prototype.slice.call(document.querySelectorAll(".filtro-chip"));
  var tarjetas = Array.prototype.slice.call(portfolio.querySelectorAll(".tarjeta"));
  var filas = Array.prototype.slice.call(portfolio.querySelectorAll(".paquetes tr[data-texto]"));
  var secciones = Array.prototype.slice.call(portfolio.querySelectorAll(".categoria"));
  var vacio = document.getElementById("filtro-vacio");
  var activos = {};

  // Minúsculas y sin tildes, para que "partícula" encuentre "particulas"
  function normalizar(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  function coincide(el, palabras, etiquetas) {
    var texto = normalizar(el.getAttribute("data-texto") || el.textContent);
    var tags = " " + (el.getAttribute("data-tags") || "") + " ";
    for (var i = 0; i < palabras.length; i++) if (texto.indexOf(palabras[i]) < 0) return false;
    for (var j = 0; j < etiquetas.length; j++) if (tags.indexOf(" " + etiquetas[j] + " ") < 0) return false;
    return true;
  }

  function aplicar() {
    var palabras = normalizar(caja.value).split(/\s+/).filter(Boolean);
    var etiquetas = Object.keys(activos);
    var hay = 0;
    tarjetas.concat(filas).forEach(function (el) {
      var ok = coincide(el, palabras, etiquetas);
      el.hidden = !ok;
      if (ok) hay++;
    });
    secciones.forEach(function (s) {
      s.hidden = !s.querySelector(".tarjeta:not([hidden]), tr[data-texto]:not([hidden])");
    });
    if (vacio) vacio.hidden = hay > 0;
  }

  caja.addEventListener("input", aplicar);
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      var t = c.getAttribute("data-tag");
      if (activos[t]) delete activos[t]; else activos[t] = true;
      c.setAttribute("aria-pressed", activos[t] ? "true" : "false");
      aplicar();
    });
  });
})();
