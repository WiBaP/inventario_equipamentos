let dispositivosCache = [];
let filtroAtual = "todos";

const STATUS_OPCOES = ["Disponivel", "Em uso", "Manutenção", "Descarte", "Coleta","Emprestado"];
const ESTADO_OPCOES = ["São Paulo", "Paraná", "Goias"];



// ------------------------------
// LISTAR
// ------------------------------
async function listar() {
    const resp = await fetch("/dispositivos/listar");
    dispositivosCache = await resp.json();

    filtroAtual = "todos";
    renderizarTabela();
}

// ------------------------------
// EDITAR
// ------------------------------
function editar(id) {

    const linha = document.getElementById(`linha_${id}`);
    if (!linha) return;

    const tds = linha.querySelectorAll("td");
    const colunaAcoes = tds[tds.length - 1];

    for (let i = 0; i < tds.length - 1; i++) {

        const valorAtual = tds[i].innerText;
        tds[i].dataset.valorOriginal = valorAtual;

        if (i === 7) {
            let html = `<select class="form-select form-select-sm">`;
            STATUS_OPCOES.forEach(op => {
                html += `<option ${op === valorAtual ? "selected" : ""}>${op}</option>`;
            });
            html += `</select>`;
            tds[i].innerHTML = html;
            continue;
        }

        if (i === 8) {
            let html = `<select class="form-select form-select-sm">`;
            ESTADO_OPCOES.forEach(op => {
                html += `<option ${op === valorAtual ? "selected" : ""}>${op}</option>`;
            });
            html += `</select>`;
            tds[i].innerHTML = html;
            continue;
        }

        tds[i].contentEditable = true;
        tds[i].style.backgroundColor = "#fff7cc";
    }

    // 🔴 ESSENCIAL: trocar os botões
    colunaAcoes.innerHTML = `
        <button class="btn btn-success btn-sm me-1"
            onclick="salvar(${id})">Salvar</button>
        <button class="btn btn-secondary btn-sm"
            onclick="cancelarEdicao(${id})">Cancelar</button>
    `;
}

// ------------------------------
// SALVAR
// ------------------------------
async function salvar(id) {

    const linha = document.getElementById(`linha_${id}`);
    const tds = linha.querySelectorAll("td");

    const body = {
        hostname: tds[0].innerText,
        memoriagb: tds[5].innerText,
        ultimousuario: tds[6].innerText,
        status: tds[7].querySelector("select")?.value || "",
        estado: tds[8].querySelector("select")?.value || "",
        obs: tds[9].innerText
    };

    const usuario = localStorage.getItem("usuario"); // vem do login

    const resp = await fetch(`/dispositivos/alterar/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": usuario
        },
        body: JSON.stringify(body)
    });

    const data = await resp.json();

    if (data.conflito_usuario) {
        window.conflitoAtual = {
            usuario: body.ultimousuario,
            hostname: data.hostname_atual,  // ← já tem
            memoriagb: data.memoriagb,      // ← já tem
            estado: data.estado,            // ← já tem
            idDispositivoAntigo: data.id_dispositivo,
            bodyAtual: body,
            idAtual: id
        };

        abrirModalConflito(
            body.ultimousuario,
            data.hostname_atual
        );

        return; // ⛔ para o save normal
    }
    console.log("RETORNO BACK:", data);



    if (!resp.ok) {
        alert("Erro ao salvar!");
        console.error("Erro:", await resp.text());
        return;
    }

    alert("Dispositivo alterado com sucesso!");
    pesquisar();
}

// ------------------------------
// CANCELAR EDIÇÃO
// ------------------------------
function cancelarEdicao(id) {
    const linha = document.getElementById(`linha_${id}`);
    if (!linha) return;

    const tds = linha.querySelectorAll("td");

    // restaura valores originais
    for (let i = 0; i < tds.length - 1; i++) {
        if (tds[i].dataset.valorOriginal !== undefined) {
            tds[i].innerHTML = tds[i].dataset.valorOriginal;
        }
        tds[i].contentEditable = false;
        tds[i].style.backgroundColor = "";
        delete tds[i].dataset.valorOriginal;
    }

    // recupera o dispositivo do cache PELO ID
    const dispositivo = dispositivosCache.find(d => d.id === id);
    if (!dispositivo) return;

    const classeBotao = dispositivo.termo_existe ? "btn-success" : "btn-danger";

    // restaura coluna de ações COMPLETA
    const colunaAcoes = tds[tds.length - 1];
    colunaAcoes.innerHTML = `
        <button class="btn ${classeBotao} btn-sm me-1"
            onclick="abrirTermo('${dispositivo.ultimousuario}', ${dispositivo.termo_existe})">
            Termo
        </button>

        <button class="btn btn-warning btn-sm"
            onclick="editar(${id})">
            Alterar
        </button>
    `;
}

// ------------------------------
// ADICIONAR
// ------------------------------
async function adicionar() {
    const body = {
        hostname: document.getElementById("add_hostname").value,
        serialnumber: document.getElementById("add_serial").value,
        fabricante: document.getElementById("add_fabricante").value,
        modelo: document.getElementById("add_modelo").value,
        cpu: document.getElementById("add_cpu").value,
        memoriagb: document.getElementById("add_memoria").value,
        ultimousuario: document.getElementById("add_ultimo").value,
        status: document.getElementById("add_status").value,
        estado: document.getElementById("add_estado").value,
        obs: document.getElementById("add_obs").value,
    };

    await fetch("/dispositivos/incluir", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    listar();
    document.querySelector("#modalAdd .btn-close").click();
}

// ------------------------------
// Pesquisar
// ------------------------------
async function pesquisar() {
    const termo = document.getElementById("pesquisa").value.trim();

    if (termo === "") {
        listar();
        return;
    }

    const resp = await fetch(`/dispositivos/pesquisar/${encodeURIComponent(termo)}`);
    dispositivosCache = await resp.json();

    filtroAtual = "todos";
    renderizarTabela();
}

/* ------------------- PENDENTES DE RETIRADA ------------------- */
async function abrirPendentes() {
    const resp = await fetch("/dispositivos/verificar_ad");
    const dados = await resp.json();

    let html = "";

    if (dados.length === 0) {
        html = `<tr><td colspan="4" class="text-center">Nenhum dispositivo pendente de retirada</td></tr>`;
    } else {
        dados.forEach(d => {
            html += `
                <tr>
                    <td>${d.hostname ?? ""}</td>
                    <td>${d.ultimousuario ?? ""}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="confirmarRetirada('${d.hostname}')">
                            Confirmado
                        </button>
                    </td>
                </tr>
            `;
        });
    }

    document.getElementById("tabelaPendentes").innerHTML = html;

    const modal = new bootstrap.Modal(document.getElementById("modalPendentes"));
    modal.show();
}

// ------------------------------
// TERMO - ABRIR MODAL
// ------------------------------
function abrirTermo(usuario, existe) {

    console.log("=== ABRIR TERMO ===");
    console.log("Usuário:", usuario);
    console.log("Existe (vindo da tabela):", existe);

    window.usuarioTermoAtual = usuario;

    if (existe) {
        console.log("➡ Vai abrir MODAL VISUALIZAR");

        document.getElementById("linkVisualizar").href =
            `/termo-download/${encodeURIComponent(usuario)}`;

        const modalVisualizar =
            bootstrap.Modal.getOrCreateInstance(
                document.getElementById("modalVisualizarTermo")
            );

        modalVisualizar.show();

    } else {
        console.log("➡ Vai abrir MODAL UPLOAD");

        document.getElementById("usuarioTermo").value = usuario; // ← MUDOU AQUI

        const modalUpload =
            bootstrap.Modal.getOrCreateInstance(
                document.getElementById("modalTermo")
            );

        modalUpload.show();
    }
}

// ------------------------------
// TERMO - UPLOAD
// ------------------------------
async function enviarTermo() {
    const usuario = document.getElementById("usuarioTermo").value; // ← MUDOU AQUI
    const arquivo = document.getElementById("arquivoTermo").files[0];

    if (!arquivo) {
        alert("Escolha um arquivo PDF!");
        return;
    }

    const form = new FormData();
    form.append("file", arquivo);

    const resp = await fetch(`/upload-termo/${usuario}`, {
        method: "POST",
        body: form
    });

    const data = await resp.json();
    alert(data.mensagem || "Termo enviado!");

    document.querySelector("#modalTermo .btn-close").click();
    pesquisar();
}

/*----------------------ALTERAR O TERMO -------------------------*/
function abrirAlterarTermo() {
    const usuario = window.usuarioTermoAtual;

    const modalVisualizar = bootstrap.Modal.getInstance(
        document.getElementById("modalVisualizarTermo")
    );

    if (modalVisualizar) {
        modalVisualizar.hide();
    }

    document.getElementById("usuarioTermo").value = usuario; // ← MUDOU AQUI
    document.getElementById("arquivoTermo").value = "";

    if (document.getElementById("btnEnviarTermo")) {
        document.getElementById("btnEnviarTermo").innerText = "Atualizar Termo";
    }

    const modalUpload =
        bootstrap.Modal.getOrCreateInstance(
            document.getElementById("modalTermo")
        );

    modalUpload.show();
}

/* ---------------- CONFIRMAR RETIRADA ---------------- */
async function confirmarRetirada(hostname) {
    console.log("Confirmando retirada do:", hostname);

    const resp = await fetch(`/dispositivos/confirmar_retirada/${hostname}`, {
        method: "PUT"
    });

    if (!resp.ok) {
        console.error("Erro ao confirmar retirada:", resp.statusText);
        return;
    }

    const data = await resp.json();
    console.log(data);

    // Fecha o modal
    const modalEl = document.getElementById("modalPendentes");
    const modal = bootstrap.Modal.getInstance(modalEl); // pega a instância do modal
    if (modal) modal.hide();

    // Atualiza os dados
    abrirPendentes();
    listar();
}

/* ---------------- RENDERIZAR A TABELA ---------------- */
function renderizarTabela() {
    let html = "";

    let dadosFiltrados = dispositivosCache;

    if (filtroAtual === "verde") {
        dadosFiltrados = dispositivosCache.filter(d => d.termo_existe);
    } else if (filtroAtual === "vermelho") {
        dadosFiltrados = dispositivosCache.filter(d => !d.termo_existe);
    }

    dadosFiltrados.forEach(d => {
        const classeBotao = d.termo_existe ? "btn-success" : "btn-danger";

        html += `
        <tr id="linha_${d.id}">
            <td>${d.hostname}</td>
            <td>${d.serialnumber ?? ""}</td>
            <td>${d.fabricante ?? ""}</td>
            <td>${d.modelo ?? ""}</td>
            <td>${d.cpu ?? ""}</td>
            <td>${d.memoriagb ?? ""}</td>
            <td>${d.ultimousuario ?? ""}</td>
            <td>${d.status ?? ""}</td>
            <td>${d.estado ?? ""}</td>
            <td>${d.obs ?? ""}</td>
            <td>
                <button class="btn ${classeBotao} btn-sm me-1"
                    onclick="abrirTermo('${d.ultimousuario}', ${d.termo_existe})">
                    Termo
                </button>

                <button class="btn btn-warning btn-sm"
                    onclick="editar(${d.id})">
                    Alterar
                </button>
            </td>
        </tr>
        `;
    });

    document.getElementById("tabela").innerHTML = html;
    atualizarContadores();
}

/* ---------------- FILTRO DE TERMOS ---------------- */
function aplicarFiltro(tipo) {
    filtroAtual = tipo;
    renderizarTabela();
}

function atualizarContadores() {
    const total = dispositivosCache.length;
    const comTermo = dispositivosCache.filter(d => d.termo_existe).length;
    const semTermo = dispositivosCache.filter(d => !d.termo_existe).length;

    document.getElementById("totalNotas").innerText = total;
    document.getElementById("totalComTermo").innerText = comTermo;
    document.getElementById("totalSemTermo").innerText = semTermo;
}

function abrirModalConflito(usuario, hostname) {

    // NÃO sobrescreve, só garante os dados
    window.conflitoAtual.usuario = usuario;
    window.conflitoAtual.hostname = hostname;

    document.getElementById("textoConflito").innerText =
        `O usuário ${usuario} já possui a máquina ${hostname}. O que deseja fazer com ela?`;

    document.getElementById("acaoConflito").value = "";

    const modal = new bootstrap.Modal(
        document.getElementById("modalConflitoUsuario")
    );
    modal.show();
}

async function confirmarConflito() {
    const acao = document.getElementById("acaoConflito").value;
    if (!acao) {
        alert("Selecione uma ação.");
        return;
    }

    switch (acao) {

        case "manutencao": {
            const motivo = prompt("Informe o motivo da manutenção:");
            if (!motivo) return alert("Motivo é obrigatório.");
            await aplicarManutencao(motivo);
            break;
        }

        case "disponivel": {
            const obs = prompt("Deseja adicionar uma observação? (opcional)") || "";
            await aplicarDisponivel(obs);
            break;
        }

        case "descarte": {
            const motivo = prompt("Informe o motivo do descarte:");
            if (!motivo) return alert("Motivo do descarte é obrigatório.");
            await aplicarDescarte(motivo);
            break;
        }

        case "emprestado": {
            const novoUsuario = prompt("Informe o usuário para quem ficará emprestado:");
            if (!novoUsuario) return alert("Usuário é obrigatório.");
            const obs = prompt("Deseja adicionar uma observação? (opcional)") || "";
            await aplicarEmprestado(novoUsuario, obs);
            break;
        }

        case "permanece": {
            console.log("Permanece com usuário – salvando máquina atual");

            const { idAtual, bodyAtual } = window.conflitoAtual;

            const body = {
                ...bodyAtual,
                ignorar_conflito: true
            };

            await fetch(`/dispositivos/alterar/${idAtual}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "usuario-acao": localStorage.getItem("usuario")
                },
                body: JSON.stringify(body)
            });

            fecharModalConflito();
            pesquisar();
            break;
        }


    }
}

async function aplicarManutencao(motivo) {

    const { idDispositivoAntigo, idAtual, bodyAtual, hostname } = window.conflitoAtual;

    const bodyAntigo = {
        hostname: hostname,
        memoriagb: bodyAtual.memoriagb,
        ultimousuario: "",
        status: "Manutenção",
        estado: bodyAtual.estado,
        obs: motivo
    };

    await fetch(`/dispositivos/alterar/${idDispositivoAntigo}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAntigo)
    });

    await fetch(`/dispositivos/alterar/${idAtual}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAtual)
    });

    // 🔽 FECHA O MODAL
    const modalEl = document.getElementById("modalConflitoUsuario");
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();

    alert("Conflito resolvido.");
    pesquisar();
}

async function aplicarDisponivel(obs) {

    const { idDispositivoAntigo, idAtual, bodyAtual, hostname } = window.conflitoAtual;

    const bodyAntigo = {
        hostname: hostname,
        memoriagb: bodyAtual.memoriagb,
        ultimousuario: "",
        status: "Disponivel",
        estado: bodyAtual.estado,
        obs: obs
    };

    await fetch(`/dispositivos/alterar/${idDispositivoAntigo}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAntigo)
    });

    await fetch(`/dispositivos/alterar/${idAtual}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAtual)
    });

    const modalEl = document.getElementById("modalConflitoUsuario");
    bootstrap.Modal.getInstance(modalEl)?.hide();

    alert("Conflito resolvido.");
    pesquisar();
}

async function aplicarDescarte(motivo) {

    const { idDispositivoAntigo, idAtual, bodyAtual, hostname } = window.conflitoAtual;

    const bodyAntigo = {
        hostname: hostname,
        memoriagb: "0GB",
        ultimousuario: "",
        status: "Descarte",
        estado: bodyAtual.estado,
        obs: motivo
    };

    await fetch(`/dispositivos/alterar/${idDispositivoAntigo}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAntigo)
    });

    await fetch(`/dispositivos/alterar/${idAtual}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAtual)
    });

    const modalEl = document.getElementById("modalConflitoUsuario");
    bootstrap.Modal.getInstance(modalEl)?.hide();

    alert("Conflito resolvido.");
    pesquisar();
}

async function aplicarEmprestado(novoUsuario, obs) {

    const {
        idDispositivoAntigo,
        idAtual,
        bodyAtual,
        memoriagb,
        estado,
        hostname  // ← adicione isso também no conflitoAtual
    } = window.conflitoAtual;

    // 1️⃣ Máquina ANTIGA → emprestada
    const bodyAntigo = {
        hostname: hostname,  // ← ADICIONAR
        memoriagb: memoriagb,  // ← ADICIONAR
        ultimousuario: novoUsuario,
        status: "Emprestado",
        estado: estado,  // ← ADICIONAR
        obs: obs,
        ignorar_conflito: true
    };

    await fetch(`/dispositivos/alterar/${idDispositivoAntigo}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyAntigo)
    });

    // 2️⃣ Máquina NOVA → mantém tudo
    const bodyNovo = {
        hostname: bodyAtual.hostname,  // ← ADICIONAR
        memoriagb: bodyAtual.memoriagb,
        ultimousuario: bodyAtual.ultimousuario,
        status: bodyAtual.status,
        estado: bodyAtual.estado,
        obs: bodyAtual.obs,
        ignorar_conflito: true
    };

    await fetch(`/dispositivos/alterar/${idAtual}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "usuario-acao": localStorage.getItem("usuario")
        },
        body: JSON.stringify(bodyNovo)
    });

    fecharModalConflito();
    alert("Conflito resolvido corretamente.");
    pesquisar();
}

function fecharModalConflito() {
    const modalEl = document.getElementById("modalConflitoUsuario");
    bootstrap.Modal.getInstance(modalEl)?.hide();
}

























    

