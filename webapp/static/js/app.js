(function () {
  "use strict";

  function dismissToastsLater() {
    document.querySelectorAll(".toast").forEach(function (toast) {
      setTimeout(function () {
        toast.classList.add("fade-out");
        setTimeout(function () { toast.remove(); }, 250);
      }, 3200);
    });
  }

  function pushToast(mensagem, categoria) {
    var container = document.getElementById("toasts");
    if (!container) return;
    var el = document.createElement("div");
    el.className = "toast toast-" + (categoria || "success");
    el.textContent = mensagem;
    container.appendChild(el);
    dismissToastsLater();
  }
  window.appToast = pushToast;

  function copiarTextoFallback(texto) {
    var textarea = document.createElement("textarea");
    textarea.value = texto;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    var copiado = false;
    try {
      copiado = document.execCommand("copy");
    } catch (e) {
      copiado = false;
    }
    document.body.removeChild(textarea);
    return copiado;
  }

  function copiarTexto(texto) {
    // navigator.clipboard só existe em contexto seguro (https:// ou localhost);
    // acessado em http://<ip-da-rede> ele é undefined e quebra silenciosamente.
    if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(function () {
        pushToast("Mensagem copiada!", "success");
      }).catch(function () {
        if (copiarTextoFallback(texto)) {
          pushToast("Mensagem copiada!", "success");
        } else {
          pushToast("Não foi possível copiar automaticamente. Selecione o texto manualmente.", "error");
        }
      });
      return;
    }
    if (copiarTextoFallback(texto)) {
      pushToast("Mensagem copiada!", "success");
    } else {
      pushToast("Não foi possível copiar automaticamente. Selecione o texto manualmente.", "error");
    }
  }
  window.appCopiar = copiarTexto;

  function montarLinkWhatsapp(botao) {
    var textareaId = botao.getAttribute("data-textarea");
    var numero = botao.getAttribute("data-numero");
    if (!numero) return;
    var textarea = document.getElementById(textareaId);
    var texto = textarea ? textarea.value : "";
    var url = "https://wa.me/" + numero + "?text=" + encodeURIComponent(texto);
    window.open(url, "_blank", "noopener");
  }
  window.appAbrirWhatsapp = montarLinkWhatsapp;

  var chartInstances = {};

  function destruirChart(id) {
    if (chartInstances[id]) {
      chartInstances[id].destroy();
      delete chartInstances[id];
    }
  }

  function initCharts() {
    var elSituacao = document.getElementById("chart-situacao");
    var dadosSituacaoEl = document.getElementById("dados-situacao");
    if (elSituacao && dadosSituacaoEl && window.Chart) {
      destruirChart("chart-situacao");
      var raw = JSON.parse(dadosSituacaoEl.textContent);
      chartInstances["chart-situacao"] = new Chart(elSituacao, {
        type: "doughnut",
        data: {
          labels: raw.labels,
          datasets: [{ data: raw.valores, backgroundColor: raw.cores, borderColor: "#fcfcfb", borderWidth: 2 }],
        },
        options: {
          cutout: "62%",
          plugins: {
            legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, font: { family: "system-ui" } } },
            tooltip: { callbacks: { label: function (ctx) {
              var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
              var pct = total ? Math.round((ctx.raw / total) * 100) : 0;
              return ctx.label + ": " + ctx.raw + " (" + pct + "%)";
            } } },
          },
        },
      });
    }

    var elMeses = document.getElementById("chart-meses");
    var dadosMesesEl = document.getElementById("dados-meses");
    if (elMeses && dadosMesesEl && window.Chart) {
      destruirChart("chart-meses");
      var rawMeses = JSON.parse(dadosMesesEl.textContent);
      chartInstances["chart-meses"] = new Chart(elMeses, {
        type: "bar",
        data: {
          labels: rawMeses.labels,
          datasets: [{ data: rawMeses.valores, backgroundColor: "#2a78d6", borderRadius: 4, maxBarThickness: 34 }],
        },
        options: {
          plugins: { legend: { display: false }, tooltip: { displayColors: false } },
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#e1e0d9" } },
            x: { grid: { display: false } },
          },
        },
      });
    }
  }
  window.appInitCharts = initCharts;

  function ativarAba(grupo, aba) {
    document.querySelectorAll('.tab[data-group="' + grupo + '"]').forEach(function (el) {
      el.classList.toggle("active", el.getAttribute("data-tab") === aba);
    });
    document.querySelectorAll('.tab-panel[data-group="' + grupo + '"]').forEach(function (el) {
      el.style.display = el.getAttribute("data-tab") === aba ? "" : "none";
    });
  }
  window.appAbaAtivar = ativarAba;

  function fecharModal() {
    var root = document.getElementById("modal-root");
    if (root) root.innerHTML = "";
  }
  window.appFecharModal = fecharModal;

  function abrirPainel() {
    var overlay = document.getElementById("painel-overlay");
    if (!overlay) return;
    var alvo = document.getElementById("painel-gerenciamento");
    if (alvo) {
      alvo.innerHTML = '<div class="card" style="display:flex; justify-content:center; padding:3rem"><span class="spinner"></span></div>';
    }
    overlay.classList.add("open");
    document.body.classList.add("no-scroll");
  }
  window.appAbrirPainel = abrirPainel;

  function fecharPainel() {
    var overlay = document.getElementById("painel-overlay");
    if (overlay) overlay.classList.remove("open");
    document.body.classList.remove("no-scroll");
  }
  window.appFecharPainel = fecharPainel;

  function initCertPicker() {
    var busca = document.getElementById("cert-picker-busca");
    var lista = document.getElementById("cert-picker-lista");
    var vazio = document.getElementById("cert-picker-vazio");
    if (!busca || !lista || busca.dataset.appInit) return;
    busca.dataset.appInit = "1";
    busca.addEventListener("input", function () {
      var termo = busca.value.trim().toLowerCase();
      var visiveis = 0;
      Array.prototype.forEach.call(lista.children, function (item) {
        var nome = item.getAttribute("data-nome") || "";
        var mostra = !termo || nome.indexOf(termo) !== -1;
        item.style.display = mostra ? "" : "none";
        if (mostra) visiveis++;
      });
      if (vazio) vazio.style.display = visiveis ? "none" : "";
    });
  }
  window.appInitCertPicker = initCertPicker;

  function selecionarCertItem(el) {
    var lista = document.getElementById("cert-picker-lista");
    if (lista) {
      Array.prototype.forEach.call(lista.children, function (item) { item.classList.remove("active"); });
    }
    el.classList.add("active");
  }
  window.appSelecionarCertItem = selecionarCertItem;

  function initDropzones() {
    document.querySelectorAll(".dropzone").forEach(function (zone) {
      if (zone.dataset.appInit) return;
      zone.dataset.appInit = "1";
      var input = zone.querySelector('input[type="file"]');
      var nomeEl = zone.querySelector(".dropzone-filename");
      if (!input) return;
      function atualizarNome() {
        if (input.files && input.files[0]) {
          if (nomeEl) nomeEl.textContent = input.files[0].name;
          zone.classList.add("has-file");
        } else {
          if (nomeEl) nomeEl.textContent = "";
          zone.classList.remove("has-file");
        }
      }
      input.addEventListener("change", atualizarNome);
      zone.addEventListener("dragover", function (e) { e.preventDefault(); zone.classList.add("dragover"); });
      zone.addEventListener("dragleave", function () { zone.classList.remove("dragover"); });
      zone.addEventListener("drop", function (e) {
        e.preventDefault();
        zone.classList.remove("dragover");
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
          input.files = e.dataTransfer.files;
          atualizarNome();
        }
      });
    });
  }
  window.appInitDropzones = initDropzones;

  function confirmarAcao(opcoes) {
    var root = document.getElementById("modal-root");
    if (!root) return;
    var titulo = opcoes.titulo || "Confirmar ação";
    var texto = opcoes.texto || "Tem certeza?";
    var rotuloConfirmar = opcoes.rotuloConfirmar || "Confirmar";
    root.innerHTML =
      '<div class="modal-backdrop" onclick="if(event.target===this) appFecharModal()">' +
      '<div class="modal-box"><h3>' + titulo + "</h3><p>" + texto + "</p>" +
      '<div class="modal-actions">' +
      '<button type="button" class="btn" onclick="appFecharModal()">Cancelar</button>' +
      '<button type="button" class="btn btn-danger" id="modal-confirm-btn">' + rotuloConfirmar + "</button>" +
      "</div></div></div>";
    document.getElementById("modal-confirm-btn").addEventListener("click", function () {
      fecharModal();
      if (typeof opcoes.aoConfirmar === "function") opcoes.aoConfirmar();
    });
  }
  window.appConfirmar = confirmarAcao;

  function alternarTema() {
    var root = document.documentElement;
    var atual = root.getAttribute("data-theme") || "light";
    var novo = atual === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", novo);
    try { localStorage.setItem("app-theme", novo); } catch (e) {}
  }
  window.appAlternarTema = alternarTema;

  var buscaGlobalState = { resultados: [], indice: -1, timer: null };

  function abrirBuscaGlobal() {
    var root = document.getElementById("modal-root");
    if (!root) return;
    buscaGlobalState = { resultados: [], indice: -1, timer: null };
    root.innerHTML =
      '<div class="modal-backdrop" onclick="if(event.target===this) appFecharModal()">' +
      '<div class="modal-box command-palette">' +
      '<input type="text" id="busca-global-input" class="command-input" placeholder="Buscar empresa, sócio ou CNPJ..." autocomplete="off">' +
      '<div id="busca-global-resultados" class="command-results"></div>' +
      '<div class="command-hint muted">Setas para navegar · Enter para abrir · Esc para fechar</div>' +
      "</div></div>";
    var input = document.getElementById("busca-global-input");
    input.addEventListener("input", onBuscaGlobalInput);
    input.addEventListener("keydown", onBuscaGlobalKeydown);
    input.focus();
  }
  window.appAbrirBuscaGlobal = abrirBuscaGlobal;

  function onBuscaGlobalInput(e) {
    var termo = e.target.value.trim();
    clearTimeout(buscaGlobalState.timer);
    if (!termo) { renderResultadosBusca([]); return; }
    buscaGlobalState.timer = setTimeout(function () {
      fetch(window.APP_URLS.buscaGlobal + "?q=" + encodeURIComponent(termo))
        .then(function (r) { return r.json(); })
        .then(renderResultadosBusca)
        .catch(function () { renderResultadosBusca([]); });
    }, 200);
  }

  function renderResultadosBusca(itens) {
    buscaGlobalState.resultados = itens;
    buscaGlobalState.indice = itens.length ? 0 : -1;
    var container = document.getElementById("busca-global-resultados");
    if (!container) return;
    if (!itens.length) {
      container.innerHTML = '<div class="command-empty muted">Nenhum certificado encontrado.</div>';
      return;
    }
    container.innerHTML = itens.map(function (item, i) {
      return '<div class="command-item' + (i === 0 ? " active" : "") + '" data-id="' + item.id + '" onclick="appIrParaCertificado(' + item.id + ')">' +
        '<div class="command-item-main"><strong>' + item.empresa + "</strong>" +
        (item.nome_socio ? ' <span class="muted">· ' + item.nome_socio + "</span>" : "") + "</div>" +
        '<span class="badge ' + item.situacao_classe + '">' + item.situacao + "</span>" +
        "</div>";
    }).join("");
  }

  function onBuscaGlobalKeydown(e) {
    var itens = buscaGlobalState.resultados;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (itens.length) { buscaGlobalState.indice = (buscaGlobalState.indice + 1) % itens.length; marcarItemAtivo(); }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (itens.length) { buscaGlobalState.indice = (buscaGlobalState.indice - 1 + itens.length) % itens.length; marcarItemAtivo(); }
    } else if (e.key === "Enter") {
      e.preventDefault();
      var atual = itens[buscaGlobalState.indice];
      if (atual) irParaCertificado(atual.id);
    }
  }

  function marcarItemAtivo() {
    var container = document.getElementById("busca-global-resultados");
    if (!container) return;
    Array.prototype.forEach.call(container.children, function (el, i) {
      el.classList.toggle("active", i === buscaGlobalState.indice);
    });
  }

  function irParaCertificado(id) {
    window.location.href = window.APP_URLS.certificadosLista + "?abrir=" + id;
  }
  window.appIrParaCertificado = irParaCertificado;

  document.body.addEventListener("htmx:afterSettle", function () {
    dismissToastsLater();
    initCharts();
    initDropzones();
    initCertPicker();
  });
  document.body.addEventListener("htmx:afterRequest", function (e) {
    if (e.detail.successful && e.target.classList && e.target.classList.contains("js-fecha-modal-sucesso")) {
      fecharModal();
    }
  });
  document.body.addEventListener("appToast", function (e) {
    pushToast(e.detail.mensagem, e.detail.categoria);
  });
  document.body.addEventListener("appFecharPainel", function () {
    fecharPainel();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      fecharModal();
      fecharPainel();
    }
    var isCtrlK = (e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K");
    if (isCtrlK) {
      e.preventDefault();
      abrirBuscaGlobal();
    }
  });
  document.addEventListener("DOMContentLoaded", function () {
    dismissToastsLater();
    initCharts();
    initDropzones();
    initCertPicker();
  });
})();
