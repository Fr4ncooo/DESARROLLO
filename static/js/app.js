// Oculta los avisos de Django después de unos segundos
document.querySelectorAll('.aviso').forEach(function (el) {
    setTimeout(function () { el.hidden = true; }, 4000);
});
