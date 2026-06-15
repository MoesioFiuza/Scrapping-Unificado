let processosData = [];
let isScraping = false;
let scrapingSessionId = null;
/** Início da sessão de scraping (ms) para estimativa de tempo restante */
let scrapingStartedAtMs = null;
let pollingInterval = null;
let abortRequested = false;
let cliJobActive = false;
/** Job CLI ativo (polling) — progresso e ETA */
let activeCliJobId = null;
let cliLastJobPayload = null;
let cliJobStartedAtMs = null;
let tribunaisMap = {};
let cliOpcoes = {};

/** Máximo de cards renderizados por vez (evita travar o DOM com milhares de nós) */
const PROCESSOS_POR_PAGINA = 100;
let processosPaginaAtual = 0;
let saveScrapingStateTimeout = null;

function escapeHtml(s) {
    if (s == null || s === '') return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatDurPortugues(ms) {
    if (ms == null || !Number.isFinite(ms) || ms < 0) return '—';
    const s = Math.round(ms / 1000);
    if (s < 60) return `${s} s`;
    const m = Math.floor(s / 60);
    const rs = s % 60;
    if (m < 60) return rs ? `${m} min ${rs} s` : `${m} min`;
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return rm ? `${h} h ${rm} min` : `${h} h`;
}

function contarProcessosScrapingConcluidos() {
    return processosData.filter((p) => p.status === 'sucesso' || p.status === 'erro').length;
}

function esconderBarraEtaScraping() {
    const wrap = document.getElementById('scrapingEtaWrap');
    if (wrap) {
        wrap.style.display = 'none';
        wrap.textContent = '';
    }
}

/** Atualiza a barra de tempo estimado (scraper normal ou extração CLI). */
function atualizarBarraEtaScraping() {
    const wrap = document.getElementById('scrapingEtaWrap');
    if (!wrap) return;

    const modoCli = cliJobActive && activeCliJobId;
    const modoScraper = isScraping && scrapingSessionId;

    if (!modoCli && !modoScraper) {
        esconderBarraEtaScraping();
        return;
    }

    if (modoCli) {
        if (cliJobStartedAtMs == null) cliJobStartedAtMs = Date.now();
        const total =
            (cliLastJobPayload && cliLastJobPayload.total_processos) || processosData.length || 0;
        if (total === 0) {
            wrap.style.display = 'none';
            return;
        }
        wrap.style.display = 'block';
        const parciais = (cliLastJobPayload && cliLastJobPayload.resultados_parciais) || [];
        const done = Array.isArray(parciais) ? parciais.length : 0;
        const elapsed = Date.now() - cliJobStartedAtMs;
        const st = cliLastJobPayload && cliLastJobPayload.status;
        if (done === 0 && st !== 'completed') {
            wrap.textContent =
                `CLI · A aguardar o 1.º processo… Decorrido: ${formatDurPortugues(elapsed)}. A estimativa total aparece após o primeiro resultado reportado pelo servidor.`;
            return;
        }
        if (st === 'completed' && done >= total) {
            const avgMs = elapsed / Math.max(1, done);
            wrap.innerHTML = `<strong>CLI · ${done}/${total}</strong> concluídos · média <strong>${(avgMs / 1000).toFixed(1)} s</strong>/processo · <strong>concluído</strong> · decorrido ${formatDurPortugues(elapsed)}`;
            return;
        }
        const avgMs = elapsed / Math.max(1, done);
        const remaining = Math.max(0, total - done);
        const etaMs = remaining * avgMs;
        const etaText =
            remaining === 0
                ? 'A finalizar ficheiros…'
                : `restante estimado ${formatDurPortugues(etaMs)}`;
        wrap.innerHTML = `<strong>CLI · ${done}/${total}</strong> · média <strong>${(avgMs / 1000).toFixed(1)} s</strong>/processo · <strong>${etaText}</strong> · decorrido ${formatDurPortugues(elapsed)}`;
        return;
    }

    if (!isScraping || !scrapingSessionId) {
        esconderBarraEtaScraping();
        return;
    }
    if (scrapingStartedAtMs == null) scrapingStartedAtMs = Date.now();
    const total = processosData.length;
    if (total === 0) {
        wrap.style.display = 'none';
        return;
    }
    wrap.style.display = 'block';
    const done = contarProcessosScrapingConcluidos();
    const elapsed = Date.now() - scrapingStartedAtMs;
    if (done === 0) {
        wrap.textContent =
            `A aguardar o 1.º processo… Decorrido: ${formatDurPortugues(elapsed)}. A estimativa do total aparece após o primeiro.`;
        return;
    }
    const avgMs = elapsed / done;
    const remaining = Math.max(0, total - done);
    const etaMs = remaining * avgMs;
    const etaText =
        remaining === 0
            ? 'A finalizar…'
            : `restante estimado ${formatDurPortugues(etaMs)}`;
    wrap.innerHTML = `<strong>${done}/${total}</strong> concluídos · média <strong>${(avgMs / 1000).toFixed(1)} s</strong>/processo · <strong>${etaText}</strong> · decorrido ${formatDurPortugues(elapsed)}`;
}

function computarEstatisticasProcessos(processos) {
    let sucesso = 0;
    let erro = 0;
    let processando = 0;
    let pendente = 0;
    for (let i = 0; i < processos.length; i++) {
        const st = processos[i].status;
        if (st === 'sucesso') sucesso++;
        else if (st === 'erro') erro++;
        else if (st === 'processando') processando++;
        else if (st === 'pendente') pendente++;
    }
    return { sucesso, erro, processando, pendente };
}

function atualizarSecaoResultadosSeNecessario() {
    const resultadosSection = document.getElementById('resultadosSection');
    if (resultadosSection && processosData.some(p => p.status === 'sucesso' || p.status === 'erro')) {
        resultadosSection.style.display = 'block';
        anexarEventListenersExportacao();
    }
}

/** Aplica vários resultados na memória e redesenha a lista uma única vez (performance no polling). */
function aplicarResultadosParciaisEmLote(resultados) {
    if (!resultados || resultados.length === 0) return;
    resultados.forEach((resultado) => {
        atualizarProcesso(resultado.numero_processo, resultado, { skipRender: true });
    });
    mostrarProcessos(processosData, { scrollIntoView: false });
    atualizarSecaoResultadosSeNecessario();
    if (scrapingSessionId) {
        saveScrapingState();
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

const fileInput = document.getElementById('fileInput');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileSelected = document.getElementById('fileSelected');
const fileName = document.getElementById('fileName');
const fileRemove = document.getElementById('fileRemove');

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        fileName.textContent = file.name;
        fileUploadArea.querySelector('.file-upload-content').style.display = 'none';
        fileSelected.style.display = 'flex';
    }
});

fileRemove.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.value = '';
    fileSelected.style.display = 'none';
    fileUploadArea.querySelector('.file-upload-content').style.display = 'block';
});

fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        fileInput.dispatchEvent(new Event('change'));
    }
});

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!fileInput.files[0]) {
        showToast('Por favor, selecione um arquivo', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    uploadBtn.disabled = true;
    uploadBtn.querySelector('.btn-content').style.display = 'none';
    uploadBtn.querySelector('.btn-loader').style.display = 'flex';
    statusDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            processosData = data.processos.map(p => ({
                ...p,
                status: 'pendente',
                dados: null,
                erro: null
            }));
            processosPaginaAtual = 0;
            mostrarProcessos(processosData, { scrollIntoView: true });
            statusDiv.textContent = `✅ ${data.total_processos} processos identificados com sucesso!`;
            statusDiv.className = 'status-message success';
            statusDiv.style.display = 'flex';
            showToast(`${data.total_processos} processos identificados!`, 'success');
        } else {
            statusDiv.textContent = `❌ Erro: ${data.error}`;
            statusDiv.className = 'status-message error';
            statusDiv.style.display = 'flex';
            showToast('Erro ao processar arquivo', 'error');
        }
    } catch (error) {
        statusDiv.textContent = `❌ Erro ao fazer upload: ${error.message}`;
        statusDiv.className = 'status-message error';
        statusDiv.style.display = 'flex';
        showToast('Erro ao fazer upload', 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.querySelector('.btn-content').style.display = 'flex';
        uploadBtn.querySelector('.btn-loader').style.display = 'none';
    }
});

async function carregarTribunais() {
    const container = document.getElementById('tribunaisContainer');
    
    try {
        const response = await fetch('/api/tribunais');
        const data = await response.json();
        
        if (data.success && data.tribunais) {
            data.tribunais.forEach(t => {
                tribunaisMap[t.codigo] = t.nome;
            });
            
            container.innerHTML = `
                ${data.tribunais.map(t => `
                    <div class="tribunal-badge">
                        <div class="tribunal-icon">⚖️</div>
                        <div class="tribunal-info">
                            <div class="tribunal-nome">${t.nome}</div>
                            <div class="tribunal-codigo">Código: ${t.codigo}</div>
                        </div>
                        <div class="tribunal-check">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            container.innerHTML = '<div class="tribunais-error">Erro ao carregar tribunais disponíveis</div>';
        }
    } catch (error) {
        console.error('Erro ao carregar tribunais:', error);
        container.innerHTML = '<div class="tribunais-error">Erro ao carregar tribunais. Tente recarregar a página.</div>';
    }
    await carregarCliOpcoes();
}

function getScraperModo() {
    const r = document.querySelector('input[name="scraperModo"]:checked');
    return r && r.value === 'cli' ? 'cli' : 'normal';
}

async function carregarCliOpcoes() {
    try {
        const response = await fetch('/api/processos/cli-opcoes');
        const data = await response.json();
        if (data.success && data.opcoes) {
            cliOpcoes = data.opcoes;
            popularSelectCliTribunal();
        }
    } catch (e) {
        console.warn('CLI opções não carregadas', e);
    }
}

function popularSelectCliTribunal() {
    const sel = document.getElementById('cliTribunalSelect');
    if (!sel) return;
    const keys = Object.keys(cliOpcoes).filter((k) => tribunaisMap[k]);
    sel.innerHTML = keys
        .map((k) => `<option value="${escapeHtml(k)}">${escapeHtml(tribunaisMap[k] || k)} (${escapeHtml(k)})</option>`)
        .join('');
    if (keys.length === 0) {
        sel.innerHTML = '<option value="">— Nenhum tribunal CLI —</option>';
    }
    atualizarCliJobModeDisponibilidade();
    atualizarTextoAvisoCli();
}

function atualizarCliJobModeDisponibilidade() {
    const selT = document.getElementById('cliTribunalSelect');
    const selB = document.getElementById('cliBrowserSelect');
    const selM = document.getElementById('cliJobModeSelect');
    if (!selT || !selB || !selM) return;
    const tk = selT.value;
    const br = selB.value;
    const caps = (cliOpcoes[tk] && cliOpcoes[tk][br]) || {};
    Array.from(selM.options).forEach((opt) => {
        const k = opt.value;
        const ok = k === 'movimentacoes' ? caps.movimentacoes : k === 'planilhas' ? caps.planilhas : k === 'polos' ? caps.polos : false;
        opt.disabled = !ok;
    });
    if (selM.selectedOptions[0] && selM.selectedOptions[0].disabled) {
        const first = Array.from(selM.options).find((o) => !o.disabled);
        if (first) selM.value = first.value;
    }
}

function atualizarTextoAvisoCli() {
    const el = document.getElementById('cliAvisoTexto');
    if (!el) return;
    if (getScraperModo() !== 'cli') {
        el.textContent = '';
        return;
    }
    el.textContent =
        'Todos os processos da lista devem ser do mesmo tribunal selecionado. A extração CLI pode demorar vários minutos; aguarde até aparecer a mensagem de conclusão e depois abra Minhas Extrações para baixar.';
}

function initScraperModoUi() {
    document.querySelectorAll('input[name="scraperModo"]').forEach((inp) => {
        inp.addEventListener('change', () => {
            const painel = document.getElementById('cliTipoPainel');
            const ab = document.getElementById('actionButton');
            const txt = ab && ab.querySelector('.action-text');
            if (painel) {
                painel.style.display = getScraperModo() === 'cli' ? 'block' : 'none';
            }
            if (txt) {
                txt.textContent = getScraperModo() === 'cli' ? 'Gerar extração (CLI)' : 'Iniciar Scraping';
            }
            atualizarTextoAvisoCli();
        });
    });
    const selT = document.getElementById('cliTribunalSelect');
    const selB = document.getElementById('cliBrowserSelect');
    if (selT) selT.addEventListener('change', () => { atualizarCliJobModeDisponibilidade(); atualizarTextoAvisoCli(); });
    if (selB) selB.addEventListener('change', atualizarCliJobModeDisponibilidade);
}

function labelTipoExtracao(tipo) {
    const map = {
        raspado: { icon: '📄', label: 'Raspado' },
        tratado: { icon: '✅', label: 'Tratado' },
        movimentacoes_cli: { icon: '📋', label: 'Movimentações (CLI)' },
        polos_cli: { icon: '⚖️', label: 'Polos (CLI)' },
        raspado_cli: { icon: '📄', label: 'Raspado (CLI)' },
        tratado_cli: { icon: '✅', label: 'Tratado (CLI)' },
    };
    return map[tipo] || { icon: '📎', label: tipo || 'Extração' };
}

function reverterProcessosCliEmProcessamento() {
    processosData.forEach((p) => {
        if (p.status === 'processando') {
            p.status = 'pendente';
            p.erro = null;
        }
    });
}

async function iniciarCliExtracaoComPolling(body, button, btnContent, btnLoader) {
    const res = await fetch('/api/processos/cli-extracao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    let data;
    try {
        data = await res.json();
    } catch {
        showToast('Resposta inválida do servidor.', 'error');
        return false;
    }
    if (!res.ok) {
        showToast(data.error || `Erro HTTP ${res.status}`, 'error');
        return false;
    }
    if (!data.success || !data.job_id) {
        showToast(data.error || 'Erro ao iniciar extração CLI', 'error');
        return false;
    }
    const jobId = data.job_id;
    activeCliJobId = jobId;
    cliJobStartedAtMs = Date.now();
    cliLastJobPayload = null;
    processosData.forEach((p) => {
        if (p.status === 'pendente') p.status = 'processando';
    });
    mostrarProcessos(processosData);
    atualizarBarraEtaScraping();

    const maxT = 720;
    let t = 0;

    const limparEstadoCliJob = () => {
        activeCliJobId = null;
        cliLastJobPayload = null;
        cliJobStartedAtMs = null;
        esconderBarraEtaScraping();
    };

    const tick = async () => {
        t++;
        try {
            const st = await fetch(`/api/processos/cli-extracao/${jobId}`);
            if (!st.ok) {
                if (t >= maxT) {
                    reverterProcessosCliEmProcessamento();
                    mostrarProcessos(processosData, { scrollIntoView: false });
                    limparEstadoCliJob();
                    return 'done_err';
                }
                return 'continue';
            }
            const j = await st.json();
            cliLastJobPayload = j;

            if (Array.isArray(j.resultados_parciais) && j.resultados_parciais.length > 0) {
                aplicarResultadosParciaisEmLote(j.resultados_parciais);
            }
            atualizarBarraEtaScraping();

            if (j.status === 'completed') {
                if (Array.isArray(j.resultados_parciais) && j.resultados_parciais.length > 0) {
                    aplicarResultadosParciaisEmLote(j.resultados_parciais);
                }
                mostrarProcessos(processosData, { scrollIntoView: false });
                limparEstadoCliJob();
                showToast('Extração CLI concluída. Abra Minhas Extrações para baixar.', 'success');
                return 'done_ok';
            }
            if (j.status === 'error') {
                reverterProcessosCliEmProcessamento();
                mostrarProcessos(processosData, { scrollIntoView: false });
                limparEstadoCliJob();
                showToast(j.error || 'Erro na extração CLI', 'error');
                return 'done_err';
            }
            if (t >= maxT) {
                reverterProcessosCliEmProcessamento();
                mostrarProcessos(processosData, { scrollIntoView: false });
                limparEstadoCliJob();
                showToast('Tempo limite ao aguardar extração CLI.', 'error');
                return 'done_err';
            }
        } catch {
            if (t >= maxT) {
                reverterProcessosCliEmProcessamento();
                mostrarProcessos(processosData, { scrollIntoView: false });
                limparEstadoCliJob();
                return 'done_err';
            }
        }
        return 'continue';
    };

    return await new Promise((resolve) => {
        let iv = null;
        let finished = false;
        const finish = (ok) => {
            if (finished) return;
            finished = true;
            if (iv) {
                clearInterval(iv);
                iv = null;
            }
            resolve(ok);
        };
        const loopBody = async () => {
            const r = await tick();
            if (r === 'done_ok') finish(true);
            else if (r === 'done_err') finish(false);
        };
        void (async () => {
            await loopBody();
            if (finished) return;
            iv = setInterval(() => {
                void loopBody();
            }, 2000);
        })();
    });
}

function getTribunalNome(codigo) {
    return tribunaisMap[codigo] || codigo || 'Não identificado';
}

/** PJe CE (8.06) e eSAJ CE (8.06_esaj) compartilham o mesmo segmento CNJ no upload. */
function processoCompativelComTribunal(tribunalProcesso, tribunalEscolhido) {
    if (tribunalProcesso === tribunalEscolhido) return true;
    if (tribunalEscolhido === '8.06_esaj' && tribunalProcesso === '8.06') return true;
    return false;
}

function mostrarProcessos(processos, options = {}) {
    const scrollIntoView = options.scrollIntoView === true;
    const section = document.getElementById('processosSection');
    const list = document.getElementById('processosList');
    const countDiv = document.getElementById('processosCount');
    const statsDiv = document.getElementById('processosStats');
    const pagDiv = document.getElementById('processosPagination');

    countDiv.textContent = `${processos.length} processo${processos.length !== 1 ? 's' : ''} identificado${processos.length !== 1 ? 's' : ''}`;

    const { sucesso, erro, processando, pendente } = computarEstatisticasProcessos(processos);

    statsDiv.innerHTML = `
        ${sucesso > 0 ? `<span class="stat-item success">✓ ${sucesso} sucesso</span>` : ''}
        ${erro > 0 ? `<span class="stat-item error">✗ ${erro} erros</span>` : ''}
        ${processando > 0 ? `<span class="stat-item processando">⏳ ${processando} processando</span>` : ''}
        ${pendente > 0 ? `<span class="stat-item pending">⏸ ${pendente} pendentes</span>` : ''}
    `;

    const resultadosSection = document.getElementById('resultadosSection');
    if (resultadosSection && processos.some(p => p.status === 'sucesso' || p.status === 'erro')) {
        resultadosSection.style.display = 'block';
        anexarEventListenersExportacao();
    }

    const total = processos.length;
    const porPagina = PROCESSOS_POR_PAGINA;
    const totalPaginas = Math.max(1, Math.ceil(total / porPagina));
    if (processosPaginaAtual >= totalPaginas) {
        processosPaginaAtual = Math.max(0, totalPaginas - 1);
    }
    const inicio = total > porPagina ? processosPaginaAtual * porPagina : 0;
    const fatia = total > porPagina ? processos.slice(inicio, inicio + porPagina) : processos;

    list.innerHTML = fatia.map((p, idx) => {
        const globalIndex = inicio + idx;
        const statusIcon = p.status === 'sucesso' ? '✓' :
            p.status === 'erro' ? '✗' :
                p.status === 'processando' ? '⟳' : '⏳';

        const tribunalNome = escapeHtml(getTribunalNome(p.tribunal));
        const numeroEsc = escapeHtml(p.numero_processo || '');
        let assuntoHtml = '';
        if (p.dados?.dados_processo?.assunto) {
            const a = p.dados.dados_processo.assunto;
            const trecho = a.substring(0, 120) + (a.length > 120 ? '...' : '');
            assuntoHtml = `
                <div class="processo-info">
                    <strong>Assunto:</strong> ${escapeHtml(trecho)}
                </div>
            `;
        }
        let erroHtml = '';
        if (p.erro) {
            erroHtml = `
                <div class="processo-info error-text">
                    <strong>Erro:</strong> ${escapeHtml(p.erro)}
                </div>
            `;
        }

        return `
        <div class="processo-item ${p.status}" data-index="${globalIndex}">
            <div class="processo-header">
                <div class="processo-main-info">
                    <div class="processo-numero">${numeroEsc}</div>
                    <div class="processo-tribunal">
                        <span class="tribunal-badge-small">${tribunalNome}</span>
                    </div>
                </div>
                <div class="processo-status ${p.status}">
                    ${statusIcon} ${p.status === 'processando' ? 'processando' : p.status}
                </div>
            </div>
            ${assuntoHtml}
            ${erroHtml}
        </div>
        `;
    }).join('');

    if (pagDiv) {
        if (total > porPagina) {
            pagDiv.style.display = 'flex';
            const fim = Math.min(inicio + fatia.length, total);
            pagDiv.innerHTML = `
                <button type="button" class="btn btn-primary" data-pag="prev" ${processosPaginaAtual === 0 ? 'disabled' : ''}>Anterior</button>
                <span class="processos-pagination-info">Mostrando ${inicio + 1}–${fim} de ${total} · Página ${processosPaginaAtual + 1} de ${totalPaginas}</span>
                <button type="button" class="btn btn-primary" data-pag="next" ${processosPaginaAtual >= totalPaginas - 1 ? 'disabled' : ''}>Próxima</button>
            `;
            pagDiv.onclick = (e) => {
                const btn = e.target.closest('button[data-pag]');
                if (!btn || btn.disabled) return;
                const dir = btn.getAttribute('data-pag');
                if (dir === 'prev') {
                    processosPaginaAtual = Math.max(0, processosPaginaAtual - 1);
                } else if (dir === 'next') {
                    processosPaginaAtual = Math.min(totalPaginas - 1, processosPaginaAtual + 1);
                }
                mostrarProcessos(processosData, { scrollIntoView: false });
            };
        } else {
            pagDiv.style.display = 'none';
            pagDiv.innerHTML = '';
            pagDiv.onclick = null;
        }
    }

    section.style.display = 'block';
    if (scrollIntoView) {
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function atualizarProcesso(numeroProcesso, resultado, options = {}) {
    const skipRender = options.skipRender === true;
    const alvo = String(numeroProcesso || '').trim();
    const index = processosData.findIndex((p) => String(p.numero_processo || '').trim() === alvo);
    if (index >= 0) {
        processosData[index] = {
            ...processosData[index],
            ...resultado
        };
        if (!skipRender) {
            mostrarProcessos(processosData, { scrollIntoView: options.scrollIntoView === true });
            atualizarSecaoResultadosSeNecessario();
        }
    }
}

function saveScrapingState(options = {}) {
    if (!scrapingSessionId) return;
    localStorage.setItem('scrapingSessionId', scrapingSessionId);
    localStorage.setItem('isScraping', 'true');
    if (scrapingStartedAtMs != null) {
        localStorage.setItem('scrapingStartedAt', String(scrapingStartedAtMs));
    }
    const persistProcessos = () => {
        try {
            localStorage.setItem('processosData', JSON.stringify(processosData));
            console.log('Estado do scraping salvo no localStorage');
        } catch (e) {
            console.warn('Não foi possível salvar processosData (lista muito grande ou quota):', e);
        }
    };
    if (options.immediate) {
        if (saveScrapingStateTimeout) {
            clearTimeout(saveScrapingStateTimeout);
            saveScrapingStateTimeout = null;
        }
        persistProcessos();
        return;
    }
    if (saveScrapingStateTimeout) {
        clearTimeout(saveScrapingStateTimeout);
    }
    saveScrapingStateTimeout = setTimeout(() => {
        saveScrapingStateTimeout = null;
        persistProcessos();
    }, 800);
}

function loadScrapingState() {
    const savedSessionId = localStorage.getItem('scrapingSessionId');
    const savedProcessosData = localStorage.getItem('processosData');
    const savedIsScraping = localStorage.getItem('isScraping');
    
    if (savedSessionId && savedIsScraping === 'true') {
        console.log('Sessão de scraping detectada no localStorage:', savedSessionId);
        
        scrapingSessionId = savedSessionId;
        isScraping = true;
        const ts = localStorage.getItem('scrapingStartedAt');
        scrapingStartedAtMs = ts ? parseInt(ts, 10) : Date.now();

        if (savedProcessosData) {
            try {
                processosData = JSON.parse(savedProcessosData);
            } catch (e) {
                console.error('Erro ao restaurar processosData:', e);
            }
        }
        
        verificarSessaoAtiva(savedSessionId);
    }
}

async function verificarSessaoAtiva(sessionId) {
    try {
        const response = await fetch(`/api/processos/status/${sessionId}`);
        
        if (!response.ok) {
            limparEstadoScraping();
            return;
        }
        
        const data = await response.json();
        
        if (data.status === 'error' && data.error && data.error.includes('Sessão não encontrada')) {
            limparEstadoScraping();
            showToast('A sessão anterior expirou. Por favor, inicie um novo scraping.', 'info');
            return;
        }
        
        console.log('Sessão ainda ativa, reconectando...');
        
        const processosSection = document.getElementById('processosSection');
        if (processosSection) {
            processosSection.style.display = 'block';
        }
        
        if (data.resultados_parciais && data.resultados_parciais.length > 0) {
            aplicarResultadosParciaisEmLote(data.resultados_parciais);
        } else if (processosData.length > 0) {
            mostrarProcessos(processosData, { scrollIntoView: false });
        }
        
        const actionButton = document.getElementById('actionButton');
        const abortButton = document.getElementById('abortarScraping');
        
        if (actionButton) {
            if (data.status === 'processing' || data.status === 'starting') {
                actionButton.disabled = true;
                const btnContent = actionButton.querySelector('.btn-content');
                const btnLoader = actionButton.querySelector('.btn-loader');
                if (btnContent) btnContent.style.display = 'none';
                if (btnLoader) btnLoader.style.display = 'flex';
            }
        }
        
        if (abortButton && data.status !== 'completed' && data.status !== 'aborted') {
            abortButton.style.cssText = 'display: inline-flex !important;';
            abortButton.disabled = false;
        }
        
        if (data.status === 'processing' || data.status === 'starting') {
            startPolling();
            atualizarBarraEtaScraping();
            showToast('Sessão de scraping em andamento detectada. Reconectando...', 'info');
        } else if (data.status === 'completed') {
            if (data.resultados && data.resultados.length > 0) {
                aplicarResultadosParciaisEmLote(data.resultados);
            }
            finalizarScraping();
            showToast('Scraping anterior já foi concluído.', 'success');
        }
        
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
        limparEstadoScraping();
    }
}

function limparEstadoScraping() {
    localStorage.removeItem('scrapingSessionId');
    localStorage.removeItem('processosData');
    localStorage.removeItem('isScraping');
    localStorage.removeItem('scrapingStartedAt');
    scrapingSessionId = null;
    scrapingStartedAtMs = null;
    isScraping = false;
}

document.getElementById('actionButton')?.addEventListener('click', async () => {
    const button = document.getElementById('actionButton');

    if (isScraping || cliJobActive) {
        return;
    }

    const abortButton = document.getElementById('abortarScraping');

    if (!abortButton) {
        console.error('Botão abortarScraping não encontrado!');
        return;
    }

    button.disabled = true;
    const btnContent = button.querySelector('.btn-content');
    const btnLoader = button.querySelector('.btn-loader');

    if (btnContent) btnContent.style.display = 'none';
    if (btnLoader) btnLoader.style.display = 'flex';

    if (getScraperModo() === 'cli') {
        abortButton.style.cssText = 'display: none !important;';
        abortButton.disabled = true;
        cliJobActive = true;
        try {
            const tribunalKey = document.getElementById('cliTribunalSelect')?.value;
            const browser = document.getElementById('cliBrowserSelect')?.value || 'chrome';
            const jobMode = document.getElementById('cliJobModeSelect')?.value || 'movimentacoes';
            const workers = parseInt(document.getElementById('cliWorkersInput')?.value || '3', 10) || 3;

            if (!tribunalKey) {
                showToast('Selecione o tribunal para a extração CLI.', 'error');
            } else {
                const mism = processosData.filter(
                    (p) => !processoCompativelComTribunal(p.tribunal, tribunalKey),
                );
                if (mism.length > 0) {
                    showToast(
                        `Há ${mism.length} processo(s) de outro tribunal. A lista deve ser só do tribunal escolhido (${tribunalKey}).`,
                        'error',
                    );
                } else {
                    const body = {
                        tribunal_key: tribunalKey,
                        browser,
                        job_mode: jobMode,
                        workers,
                        processos: processosData,
                    };
                    const ok = await iniciarCliExtracaoComPolling(body, button, btnContent, btnLoader);
                    if (ok) {
                        setTimeout(() => loadExtracoes(), 500);
                    }
                }
            }
        } catch (error) {
            showToast('Erro na extração CLI: ' + error.message, 'error');
        } finally {
            cliJobActive = false;
            button.disabled = false;
            if (btnContent) btnContent.style.display = 'flex';
            if (btnLoader) btnLoader.style.display = 'none';
        }
        return;
    }

    abortButton.removeAttribute('style');
    abortButton.style.cssText = 'display: inline-flex !important;';
    abortButton.disabled = false;

    isScraping = true;
    abortRequested = false;

    processosData.forEach((p) => {
        if (p.status === 'pendente') {
            p.status = 'processando';
        }
    });
    mostrarProcessos(processosData);

    try {
        const response = await fetch('/api/processos/scraper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ processos: processosData }),
        });

        const data = await response.json();
        if (data.success && data.session_id) {
            scrapingSessionId = data.session_id;
            scrapingStartedAtMs = Date.now();
            localStorage.setItem('scrapingStartedAt', String(scrapingStartedAtMs));
            saveScrapingState({ immediate: true });
            startPolling();
            atualizarBarraEtaScraping();
        } else {
            showToast('Erro: ' + (data.error || 'Erro desconhecido'), 'error');
            resetScrapingState();
        }
    } catch (error) {
        showToast('Erro ao iniciar scraping: ' + error.message, 'error');
        resetScrapingState();
    }
});

function startPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    let consecutiveErrors = 0;
    const maxErrors = 3;
    
    pollingInterval = setInterval(async () => {
        if (!scrapingSessionId || abortRequested) {
            stopPolling();
            return;
        }
        
        try {
            const response = await fetch(`/api/processos/status/${scrapingSessionId}`);
            
            if (!response.ok) {
                consecutiveErrors++;
                if (consecutiveErrors >= maxErrors) {
                    stopPolling();
                    resetScrapingState();
                    showToast('Erro ao verificar status. Por favor, tente novamente.', 'error');
                }
                return;
            }
            
            const data = await response.json();
            
            // Resetar contador de erros se a requisição foi bem-sucedida
            consecutiveErrors = 0;
            
            if (data.status === 'completed') {
                stopPolling();
                if (data.resultados && data.resultados.length > 0) {
                    aplicarResultadosParciaisEmLote(data.resultados);
                }
                const resultadosSection = document.getElementById('resultadosSection');
                if (resultadosSection) {
                    resultadosSection.style.display = 'block';
                    anexarEventListenersExportacao();
                }
                esconderBarraEtaScraping();
                finalizarScraping();
                showToast('Raspagem concluída com sucesso!', 'success');
            } else if (data.status === 'aborted') {
                stopPolling();
                resetScrapingState();
                showToast('Scraping abortado pelo usuário', 'error');
            } else if (data.status === 'error') {
                stopPolling();
                resetScrapingState();
                showToast(data.error || 'Erro no scraping. Por favor, tente novamente.', 'error');
            } else if (data.status === 'processing' || data.status === 'starting') {
                if (data.resultados_parciais && data.resultados_parciais.length > 0) {
                    aplicarResultadosParciaisEmLote(data.resultados_parciais);
                }
                atualizarBarraEtaScraping();
            }
        } catch (error) {
            consecutiveErrors++;
            console.error('Erro ao verificar status:', error);
            
            // Se houver muitos erros consecutivos, parar o polling
            if (consecutiveErrors >= maxErrors) {
                stopPolling();
                resetScrapingState();
                showToast('Erro ao verificar status do scraping. Por favor, tente novamente.', 'error');
            }
        }
    }, 1500); // Polling a cada 1.5 segundos
    atualizarBarraEtaScraping();
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function finalizarScraping() {
    esconderBarraEtaScraping();
    isScraping = false;
    scrapingSessionId = null;

    const button = document.getElementById('actionButton');
    const abortButton = document.getElementById('abortarScraping');

    if (!button) {
        console.error('Botão actionButton não encontrado!');
        return;
    }

    // Resetar botão para estado inicial
    const icon = button.querySelector('.action-icon');
    const text = button.querySelector('.action-text');
    const loaderText = button.querySelector('.loader-text');

    if (icon) icon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
    if (text) text.textContent = 'Iniciar Scraping';
    if (loaderText) loaderText.textContent = 'Processando...';

    button.disabled = false;
    const btnContent = button.querySelector('.btn-content');
    const btnLoader = button.querySelector('.btn-loader');

    if (btnContent) btnContent.style.display = 'flex';
    if (btnLoader) btnLoader.style.display = 'none';

    button.classList.remove('btn-success');
    button.classList.add('btn-primary');

    if (abortButton) {
        abortButton.style.cssText = 'display: none !important;';
    }

    // SEMPRE exibir a seção de resultados e anexar os listeners de exportação
    const resultadosSection = document.getElementById('resultadosSection');
    if (resultadosSection) {
        resultadosSection.style.display = 'block';
        resultadosSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        anexarEventListenersExportacao();
    }

    // limpar storage somente no fim (para não perder o estado antes de renderizar os botões)
    limparEstadoScraping();

    button.offsetHeight;
}

function resetScrapingState() {
    esconderBarraEtaScraping();
    isScraping = false;
    scrapingSessionId = null;
    limparEstadoScraping();
    stopPolling();
    
    const button = document.getElementById('actionButton');
    const abortButton = document.getElementById('abortarScraping');
    
    if (!button || !abortButton) {
        console.error('Botões não encontrados!');
        return;
    }
    
    processosData.forEach(p => {
        if (p.status === 'processando') {
            p.status = 'pendente';
        }
    });
    mostrarProcessos(processosData);
    
    button.disabled = false;
    const btnContent = button.querySelector('.btn-content');
    const btnLoader = button.querySelector('.btn-loader');
    if (btnContent) btnContent.style.display = 'flex';
    if (btnLoader) btnLoader.style.display = 'none';
    button.classList.remove('btn-success');
    button.classList.add('btn-primary');
    abortButton.style.display = 'none';
    abortButton.style.setProperty('display', 'none', 'important');
}

document.getElementById('abortarScraping')?.addEventListener('click', async () => {
    if (!scrapingSessionId) return;
    
    abortRequested = true;
    const abortButton = document.getElementById('abortarScraping');
    abortButton.disabled = true;
    
    try {
        const response = await fetch(`/api/processos/abort/${scrapingSessionId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            limparEstadoScraping(); 
            resetScrapingState();
            showToast('Scraping abortado com sucesso', 'info');
        } else {
            showToast('Erro ao abortar scraping', 'error');
            abortRequested = false;
            abortButton.disabled = false;
        }
    } catch (error) {
        showToast('Erro ao abortar scraping: ' + error.message, 'error');
        abortRequested = false;
        abortButton.disabled = false;
    }
});

// Função para anexar event listeners de exportação
function anexarEventListenersExportacao() {
    const exportarRaspadoBtn = document.getElementById('exportarRaspado');
    const exportarTratadoBtn = document.getElementById('exportarTratado');
    
    if (exportarRaspadoBtn && !exportarRaspadoBtn.hasAttribute('data-listener-attached')) {
        exportarRaspadoBtn.addEventListener('click', exportarRaspado);
        exportarRaspadoBtn.setAttribute('data-listener-attached', 'true');
        console.log('Event listener adicionado ao botão exportarRaspado');
    }
    
    if (exportarTratadoBtn && !exportarTratadoBtn.hasAttribute('data-listener-attached')) {
        exportarTratadoBtn.addEventListener('click', exportarTratado);
        exportarTratadoBtn.setAttribute('data-listener-attached', 'true');
        console.log('Event listener adicionado ao botão exportarTratado');
    }
}

// Exportar planilha raspada
function exportarRaspado() {
    console.log('Exportar raspado chamado');
    const button = document.getElementById('exportarRaspado');
    
    if (!button) {
        console.error('Botão exportarRaspado não encontrado!');
        showToast('Erro: Botão não encontrado', 'error');
        return;
    }
    
    button.disabled = true;
    button.querySelector('.btn-content').style.display = 'none';
    button.querySelector('.btn-loader').style.display = 'flex';
    
    const resultados = processosData.filter(p => p.status === 'sucesso' || p.status === 'erro');
    console.log('Resultados para exportar:', resultados.length);
    
    if (resultados.length === 0) {
        showToast('Nenhum resultado para exportar', 'error');
        button.disabled = false;
        button.querySelector('.btn-content').style.display = 'flex';
        button.querySelector('.btn-loader').style.display = 'none';
        return;
    }
    
    fetch('/api/resultados/exportar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resultados: resultados })
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        
        if (response.ok) {
            if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                return response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `resultados_raspados_${new Date().getTime()}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    showToast('Planilha raspada exportada com sucesso!', 'success');
                });
            } else {
                return response.json().then(data => {
                    if (data.error) {
                        showToast('Erro ao exportar: ' + data.error, 'error');
                    }
                });
            }
        } else {
            return response.json().then(errorData => {
                showToast('Erro ao exportar: ' + (errorData.error || 'Erro desconhecido'), 'error');
            });
        }
    })
    .catch(error => {
        showToast('Erro ao exportar: ' + error.message, 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.querySelector('.btn-content').style.display = 'flex';
        button.querySelector('.btn-loader').style.display = 'none';
    });
}

// Exportar planilha tratada
function exportarTratado() {
    console.log('Exportar tratado chamado');
    const button = document.getElementById('exportarTratado');
    
    if (!button) {
        console.error('Botão exportarTratado não encontrado!');
        showToast('Erro: Botão não encontrado', 'error');
        return;
    }
    
    button.disabled = true;
    button.querySelector('.btn-content').style.display = 'none';
    button.querySelector('.btn-loader').style.display = 'flex';
    
    const resultados = processosData.filter(p => p.status === 'sucesso' || p.status === 'erro');
    console.log('Resultados para exportar:', resultados.length);
    
    if (resultados.length === 0) {
        showToast('Nenhum resultado para exportar', 'error');
        button.disabled = false;
        button.querySelector('.btn-content').style.display = 'flex';
        button.querySelector('.btn-loader').style.display = 'none';
        return;
    }
    
    fetch('/api/resultados/exportar-tratado', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resultados: resultados })
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        
        if (response.ok) {
            if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                return response.blob().then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `resultados_tratados_${new Date().getTime()}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    showToast('Planilha tratada exportada com sucesso!', 'success');
                });
            } else {
                return response.json().then(data => {
                    if (data.error) {
                        showToast('Erro ao exportar: ' + data.error, 'error');
                    }
                });
            }
        } else {
            return response.json().then(errorData => {
                showToast('Erro ao exportar: ' + (errorData.error || 'Erro desconhecido'), 'error');
            });
        }
    })
    .catch(error => {
        showToast('Erro ao exportar: ' + error.message, 'error');
    })
    .finally(() => {
        button.disabled = false;
        button.querySelector('.btn-content').style.display = 'flex';
        button.querySelector('.btn-loader').style.display = 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    carregarTribunais();
    loadScrapingState();
    initScraperModoUi();

    // Event listeners para exportação
    setTimeout(() => {
        anexarEventListenersExportacao();
    }, 100);
    
    // Mostrar seção de resultados se houver processos processados
    const resultadosSection = document.getElementById('resultadosSection');
    if (resultadosSection && processosData.some(p => p.status === 'sucesso' || p.status === 'erro')) {
        resultadosSection.style.display = 'block';
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const abortButton = document.getElementById('abortarScraping');
    if (abortButton) {
        abortButton.style.setProperty('display', 'inline-flex', 'important');
    }
});

// Verificar role e mostrar link admin se for admin
async function checkAdminAccess() {
    try {
        const response = await fetch('/api/auth/check');
        const data = await response.json();
        
        if (data.authenticated && data.role === 'admin') {
            const adminLink = document.getElementById('adminLink');
            if (adminLink) {
                adminLink.style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('Erro ao verificar acesso admin:', error);
    }
}

// Logout functionality
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        if (confirm('Deseja realmente sair?')) {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                if (data.success) {
                    window.location.href = '/login';
                }
            } catch (error) {
                console.error('Erro ao fazer logout:', error);
                window.location.href = '/login';
            }
        }
    });
}

checkAdminAccess();


function switchTab(tabName) {
    // Esconder todas as abas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remover active de todos os botões
    document.querySelectorAll('.btn-extracoes, .btn-scraper').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Mostrar aba selecionada
    if (tabName === 'extracoes') {
        const extracoesTab = document.getElementById('extracoesTab');
        const extracoesBtn = document.getElementById('extracoesBtn');
        const scraperBtn = document.getElementById('scraperBtn');
        
        if (extracoesTab) extracoesTab.classList.add('active');
        if (extracoesBtn) extracoesBtn.classList.add('active');
        if (scraperBtn) scraperBtn.style.display = 'flex';
        
        // Carregar extrações após um pequeno delay para garantir que a aba está visível
        setTimeout(() => {
            loadExtracoes();
        }, 100);
    } else {
        const scraperTab = document.getElementById('scraperTab');
        const scraperBtn = document.getElementById('scraperBtn');
        
        if (scraperTab) scraperTab.classList.add('active');
        if (scraperBtn) {
            scraperBtn.classList.add('active');
            scraperBtn.style.display = 'none';
        }
    }
}

// Event listeners para botões de abas
document.addEventListener('DOMContentLoaded', () => {
    const extracoesBtn = document.getElementById('extracoesBtn');
    const scraperBtn = document.getElementById('scraperBtn');
    
    if (extracoesBtn) {
        extracoesBtn.addEventListener('click', () => switchTab('extracoes'));
    }
    
    if (scraperBtn) {
        scraperBtn.addEventListener('click', () => switchTab('scraper'));
    }
});


document.addEventListener('DOMContentLoaded', () => {
    // Botão de atualizar extrações
    const refreshBtn = document.getElementById('refreshExtracoes');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadExtracoes);
    }
});

async function loadExtracoes() {
    // Verificar se estamos na aba de extrações
    const extracoesTab = document.getElementById('extracoesTab');
    if (!extracoesTab || !extracoesTab.classList.contains('active')) {
        return; // Não carregar se não estiver na aba ativa
    }
    
    const extracoesList = document.getElementById('extracoesList');
    const extracoesCount = document.getElementById('extracoesCount');
    const extracoesStats = document.getElementById('extracoesStats');
    
    if (!extracoesList) {
        console.warn('Elemento extracoesList não encontrado');
        return;
    }
    
    extracoesList.innerHTML = `
        <div class="extracoes-loading">
            <span class="spinner-small"></span>
            <span>Carregando extrações...</span>
        </div>
    `;
    
    try {
        const response = await fetch('/api/extracoes/listar');
        const data = await response.json();
        
        if (data.success) {
            // Atualizar contador e estatísticas gerais
            if (extracoesCount) {
                extracoesCount.textContent = `${data.extracoes.length} extração${data.extracoes.length !== 1 ? 'ões' : ''} encontrada${data.extracoes.length !== 1 ? 's' : ''}`;
            }
            
            if (extracoesStats && data.extracoes.length > 0) {
                const totalProcessos = data.extracoes.reduce(
                    (sum, e) => sum + (e.estatisticas?.total_processos || e.total_processos || 0),
                    0,
                );
                const raspado = data.extracoes.filter((e) => e.tipo === 'raspado' || e.tipo === 'raspado_cli').length;
                const tratado = data.extracoes.filter((e) => e.tipo === 'tratado' || e.tipo === 'tratado_cli').length;
                const cliOutros = data.extracoes.filter((e) =>
                    ['movimentacoes_cli', 'polos_cli'].includes(e.tipo),
                ).length;

                extracoesStats.innerHTML = `
                    ${totalProcessos > 0 ? `<span class="stat-item-extracao">📊 ${totalProcessos} processos</span>` : ''}
                    ${raspado > 0 ? `<span class="stat-item-extracao">📄 ${raspado} raspado${raspado !== 1 ? 's' : ''}</span>` : ''}
                    ${tratado > 0 ? `<span class="stat-item-extracao">✅ ${tratado} tratado${tratado !== 1 ? 's' : ''}</span>` : ''}
                    ${cliOutros > 0 ? `<span class="stat-item-extracao">⚙️ ${cliOutros} CLI</span>` : ''}
                `;
            }
            
            if (data.extracoes.length === 0) {
                extracoesList.innerHTML = `
                    <div class="extracoes-empty" style="padding: 60px 20px; text-align: center; background: white; border-radius: var(--radius-sm);">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 64px; height: 64px; margin: 0 auto 20px; opacity: 0.5;">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                        </svg>
                        <p style="font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">Nenhuma extração encontrada</p>
                        <p style="font-size: 14px; color: var(--text-lighter);">
                            Suas exportações aparecerão aqui após você exportar os resultados
                        </p>
                    </div>
                `;
                return;
            }
            
            extracoesList.innerHTML = `
                <table class="extracoes-table">
                    <thead>
                        <tr>
                            <th>Arquivo</th>
                            <th>Tipo</th>
                            <th>Data de Criação</th>
                            <th>Estatísticas</th>
                            <th>Distribuição por Tribunal</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.extracoes.map(extracao => {
                const dataCriacao = new Date(extracao.data_criacao);
                const dataFormatada = dataCriacao.toLocaleString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                const tipoInfo = labelTipoExtracao(extracao.tipo);
                const tipoLabel = tipoInfo.label;
                const tipoIcon = tipoInfo.icon;
                const stats = extracao.estatisticas || {};
                const totalProcessos = stats.total_processos || extracao.total_processos || 0;
                const tribunais = stats.tribunais || {};
                const totalTribunais = stats.total_tribunais || Object.keys(tribunais).length;
                const maiorTribunal = stats.maior_tribunal;
                const menorTribunal = stats.menor_tribunal;
                
                // Renderizar estatísticas de tribunais
                let tribunaisHTML = '';
                if (Object.keys(tribunais).length > 0) {
                    const tribunaisOrdenados = Object.entries(tribunais)
                        .sort((a, b) => b[1].count - a[1].count)
                        .slice(0, 5); // Mostrar apenas os 5 primeiros
                    
                    tribunaisHTML = tribunaisOrdenados.map(([tribunal, info]) => `
                        <div class="extracao-tribunal-item">
                            <span class="extracao-tribunal-item-name">${getTribunalNome(tribunal) || tribunal}</span>
                            <span class="extracao-tribunal-item-count">${info.count}</span>
                            <span class="extracao-tribunal-item-percent">${info.percent}%</span>
                        </div>
                    `).join('');
                    
                    if (Object.keys(tribunais).length > 5) {
                        tribunaisHTML += `<div style="padding: 6px 10px; font-size: 0.75rem; color: var(--text-secondary); font-style: italic;">+${Object.keys(tribunais).length - 5} tribunal(is) adicional(is)</div>`;
                    }
                }
                
                return `
                    <tr>
                        <td class="extracao-cell-filename">${extracao.filename}</td>
                        <td>
                            <span class="extracao-cell-badge ${extracao.tipo.replace(/[^a-z0-9_-]/gi, '_')}">
                                ${tipoIcon} ${tipoLabel}
                            </span>
                        </td>
                        <td>${dataFormatada}</td>
                        <td>
                            <div class="extracao-cell-stats">
                                <div class="extracao-stat-item">
                                    <span class="extracao-stat-label">Total de Processos</span>
                                    <span class="extracao-stat-value">${totalProcessos}</span>
                                </div>
                                <div class="extracao-stat-item">
                                    <span class="extracao-stat-label">Tribunais Diferentes</span>
                                    <span class="extracao-stat-value">${totalTribunais}</span>
                                </div>
                                ${maiorTribunal && maiorTribunal.codigo ? `
                                <div class="extracao-stat-item">
                                    <span class="extracao-stat-label">Maior Tribunal</span>
                                    <span class="extracao-stat-value">${getTribunalNome(maiorTribunal.codigo) || maiorTribunal.codigo} (${maiorTribunal.count})</span>
                                </div>
                                ` : ''}
                                ${menorTribunal && menorTribunal.codigo && menorTribunal.codigo !== maiorTribunal?.codigo ? `
                                <div class="extracao-stat-item">
                                    <span class="extracao-stat-label">Menor Tribunal</span>
                                    <span class="extracao-stat-value">${getTribunalNome(menorTribunal.codigo) || menorTribunal.codigo} (${menorTribunal.count})</span>
                                </div>
                                ` : ''}
                            </div>
                        </td>
                        <td>
                            ${Object.keys(tribunais).length > 0 ? `
                                <div class="extracao-cell-tribunais">
                                    ${tribunaisHTML}
                                </div>
                            ` : '<span style="color: var(--text-lighter);">N/A</span>'}
                        </td>
                        <td>
                            <div class="extracao-cell-actions">
                                <button class="btn btn-primary" onclick="downloadExtracao('${extracao.id}')">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path>
                                        <polyline points="7 10 12 15 17 10"></polyline>
                                        <line x1="12" y1="15" x2="12" y2="3"></line>
                                    </svg>
                                    Download
                                </button>
                                <button class="btn btn-danger" onclick="deleteExtracao('${extracao.id}', '${extracao.filename}')">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                                    </svg>
                                    Excluir
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('')}
                    </tbody>
                </table>
            `;
        } else {
            extracoesList.innerHTML = `
                <div class="extracoes-empty">
                    <p>Erro ao carregar extrações</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar extrações:', error);
        extracoesList.innerHTML = `
            <div class="extracoes-empty">
                <p>Erro ao carregar extrações. Tente novamente.</p>
            </div>
        `;
    }
}

async function downloadExtracao(extracaoId) {
    try {
        window.location.href = `/api/extracoes/download/${extracaoId}`;
        showToast('Download iniciado', 'success');
    } catch (error) {
        console.error('Erro ao fazer download:', error);
        showToast('Erro ao fazer download', 'error');
    }
}

async function deleteExtracao(extracaoId, filename) {
    if (!confirm(`Tem certeza que deseja excluir a extração "${filename}"?\n\nEsta ação não pode ser desfeita.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/extracoes/deletar/${extracaoId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message || 'Extração removida com sucesso', 'success');
            loadExtracoes();
        } else {
            showToast(data.error || 'Erro ao remover extração', 'error');
        }
    } catch (error) {
        console.error('Erro ao deletar extração:', error);
        showToast('Erro ao remover extração', 'error');
    }
}

// Recarregar extrações após exportar
const originalExportarRaspado = window.exportarRaspado;
const originalExportarTratado = window.exportarTratado;

// Interceptar exportações para recarregar a lista
document.addEventListener('DOMContentLoaded', () => {
    const exportarRaspadoBtn = document.getElementById('exportarRaspado');
    const exportarTratadoBtn = document.getElementById('exportarTratado');
    
    if (exportarRaspadoBtn) {
        exportarRaspadoBtn.addEventListener('click', () => {
            setTimeout(() => {
                loadExtracoes();
            }, 2000);
        });
    }
    
    if (exportarTratadoBtn) {
        exportarTratadoBtn.addEventListener('click', () => {
            setTimeout(() => {
                loadExtracoes();
            }, 2000);
        });
    }
});