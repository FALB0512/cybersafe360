/* TotalSecurity — avisos y confirmaciones propias de la plataforma */
(function () {
    var ultimo = 0;

    function toast(tipo, texto) {
        var c = document.getElementById('tsToasts');
        if (!c) return;
        var ahora = Date.now();
        if (tipo === 'warn' && ahora - ultimo < 250) return; /* un solo aviso por envío */
        ultimo = ahora;
        var iconos = { success: '✓', danger: '!', warn: '⚠', info: 'i' };
        var el = document.createElement('div');
        el.className = 'ts-toast ts-' + tipo;
        var ico = document.createElement('div');
        ico.className = 'ts-ico';
        ico.textContent = iconos[tipo] || 'i';
        var txt = document.createElement('div');
        txt.className = 'ts-txt';
        txt.textContent = texto;
        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'ts-x';
        x.setAttribute('aria-label', 'Cerrar');
        x.innerHTML = '&times;';
        x.onclick = function () { el.remove(); };
        el.appendChild(ico);
        el.appendChild(txt);
        el.appendChild(x);
        c.appendChild(el);
        setTimeout(function () {
            el.classList.add('ts-out');
            setTimeout(function () { el.remove(); }, 300);
        }, 6000);
    }
    window.tsToast = toast;

    function etiqueta(el) {
        if (el.type === 'radio') {
            var item = el.closest('.control-item');
            if (item) return 'control ' + item.dataset.num + ' de ' + item.closest('[data-dominio]').dataset.dominio;
        }
        var cont = el.closest('.row > div') || el.parentElement;
        var lab = cont && cont.querySelector('label');
        return lab ? lab.textContent.trim() : 'un campo obligatorio';
    }

    /* Reemplaza el aviso nativo del navegador por uno propio */
    document.addEventListener('invalid', function (e) {
        e.preventDefault();
        toast('warn', 'Falta completar: ' + etiqueta(e.target));
    }, true);

    /* Confirmaciones dentro de la plataforma */
    var modalEl = document.getElementById('tsConfirm');
    var okBtn = document.getElementById('tsConfirmOk');
    var accion = null;
    if (okBtn && modalEl && window.bootstrap) {
        okBtn.addEventListener('click', function () {
            var f = accion;
            accion = null;
            bootstrap.Modal.getInstance(modalEl).hide();
            if (f) f();
        });
    }
    document.addEventListener('submit', function (e) {
        var f = e.target;
        if (!f.dataset || !f.dataset.confirm || !modalEl || !window.bootstrap) return;
        if (f.dataset.confirmado === '1') return;
        e.preventDefault();
        document.getElementById('tsConfirmText').textContent = f.dataset.confirm;
        accion = function () { f.dataset.confirmado = '1'; f.submit(); };
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }, true);

    /* Mensajes del servidor, mostrados como avisos de la plataforma */
    document.querySelectorAll('[data-ts-flash]').forEach(function (n) {
        var tipo = n.dataset.tsFlash;
        toast(tipo === 'success' ? 'success' : (tipo === 'danger' ? 'danger' : 'info'), n.textContent.trim());
        n.remove();
    });
})();
