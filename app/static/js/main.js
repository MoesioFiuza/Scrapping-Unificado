let processosData = [];
let isScraping = false;
let scrapingSessionId = null;
let pollingInterval = null;
let abortRequested = false;
let tribunaisMap = {};

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
            mostrarProcessos(processosData);
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
}

function getTribunalNome(codigo) {
    return tribunaisMap[codigo] || codigo || 'Não identificado';
}

function mostrarProcessos(processos) {
    const section = document.getElementById('processosSection');
    const list = document.getElementById('processosList');
    const countDiv = document.getElementById('processosCount');
    const statsDiv = document.getElementById('processosStats');
    
    countDiv.textContent = `${processos.length} processo${processos.length !== 1 ? 's' : ''} identificado${processos.length !== 1 ? 's' : ''}`;
    
    const sucesso = processos.filter(p => p.status === 'sucesso').length;
    const erro = processos.filter(p => p.status === 'erro').length;
    const processando = processos.filter(p => p.status === 'processando').length;
    const pendente = processos.filter(p => p.status === 'pendente').length;
    
    statsDiv.innerHTML = `
        ${sucesso > 0 ? `<span class="stat-item success">✓ ${sucesso} sucesso</span>` : ''}
        ${erro > 0 ? `<span class="stat-item error">✗ ${erro} erros</span>` : ''}
        ${processando > 0 ? `<span class="stat-item processando">⏳ ${processando} processando</span>` : ''}
        ${pendente > 0 ? `<span class="stat-item pending">⏸ ${pendente} pendentes</span>` : ''}
    `;
    
    // Mostrar seção de resultados se houver processos processados
    const resultadosSection = document.getElementById('resultadosSection');
    if (resultadosSection && processos.some(p => p.status === 'sucesso' || p.status === 'erro')) {
        resultadosSection.style.display = 'block';
        // Garantir que os event listeners estejam anexados
        anexarEventListenersExportacao();
    }
    
    list.innerHTML = processos.map((p, index) => {
        const statusIcon = p.status === 'sucesso' ? '✓' : 
                          p.status === 'erro' ? '✗' : 
                          p.status === 'processando' ? '⟳' : '⏳';
        
        const tribunalNome = getTribunalNome(p.tribunal);
        
        return `
        <div class="processo-item ${p.status}" data-index="${index}">
            <div class="processo-header">
                <div class="processo-main-info">
                    <div class="processo-numero">${p.numero_processo}</div>
                    <div class="processo-tribunal">
                        <span class="tribunal-badge-small">${tribunalNome}</span>
                    </div>
                </div>
                <div class="processo-status ${p.status}">
                    ${statusIcon} ${p.status === 'processando' ? 'processando' : p.status}
                </div>
            </div>
            ${p.dados?.dados_processo?.assunto ? `
                <div class="processo-info">
                    <strong>Assunto:</strong> ${p.dados.dados_processo.assunto.substring(0, 120)}${p.dados.dados_processo.assunto.length > 120 ? '...' : ''}
                </div>
            ` : ''}
            ${p.erro ? `
                <div class="processo-info error-text">
                    <strong>Erro:</strong> ${p.erro}
                </div>
            ` : ''}
        </div>
        `;
    }).join('');
    
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function atualizarProcesso(numeroProcesso, resultado) {
    const index = processosData.findIndex(p => p.numero_processo === numeroProcesso);
    if (index >= 0) {
        processosData[index] = {
            ...processosData[index],
            ...resultado
        };
        mostrarProcessos(processosData);
        
        // Garantir que a seção de resultados apareça quando houver processos processados
        const resultadosSection = document.getElementById('resultadosSection');
        if (resultadosSection && processosData.some(p => p.status === 'sucesso' || p.status === 'erro')) {
            resultadosSection.style.display = 'block';
            anexarEventListenersExportacao();
        }
    }
}

function saveScrapingState() {
    if (scrapingSessionId) {
        localStorage.setItem('scrapingSessionId', scrapingSessionId);
        localStorage.setItem('processosData', JSON.stringify(processosData));
        localStorage.setItem('isScraping', 'true');
        console.log('Estado do scraping salvo no localStorage');
    }
}

function loadScrapingState() {
    const savedSessionId = localStorage.getItem('scrapingSessionId');
    const savedProcessosData = localStorage.getItem('processosData');
    const savedIsScraping = localStorage.getItem('isScraping');
    
    if (savedSessionId && savedIsScraping === 'true') {
        console.log('Sessão de scraping detectada no localStorage:', savedSessionId);
        
        scrapingSessionId = savedSessionId;
        isScraping = true;
        
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
            data.resultados_parciais.forEach((resultado) => {
                atualizarProcesso(resultado.numero_processo, resultado);
            });
        }
        
        const actionButton = document.getElementById('actionButton');
        const abortButton = document.getElementById('abortarScraping');
        
        if (actionButton) {
            if (data.status === 'completed') {
                finalizarScraping();
            } else if (data.status === 'processing' || data.status === 'starting') {
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
            showToast('Sessão de scraping em andamento detectada. Reconectando...', 'info');
        } else if (data.status === 'completed') {
            if (data.resultados) {
                data.resultados.forEach((resultado) => {
                    atualizarProcesso(resultado.numero_processo, resultado);
                });
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
    scrapingSessionId = null;
    isScraping = false;
}

document.getElementById('actionButton')?.addEventListener('click', async () => {
    const button = document.getElementById('actionButton');
    
    if (isScraping) {
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
    
    abortButton.removeAttribute('style');
    abortButton.style.cssText = 'display: inline-flex !important;';
    abortButton.disabled = false;
    
    isScraping = true;
    abortRequested = false;
    
    processosData.forEach(p => {
        if (p.status === 'pendente') {
            p.status = 'processando';
        }
    });
    mostrarProcessos(processosData);
    
    try {
        const response = await fetch('/api/processos/scraper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ processos: processosData })
        });
        
        const data = await response.json();
        if (data.success && data.session_id) {
            scrapingSessionId = data.session_id;
            saveScrapingState();
            startPolling();
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
                // Atualizar todos os processos com os resultados finais
                if (data.resultados) {
                    data.resultados.forEach((resultado) => {
                        atualizarProcesso(resultado.numero_processo, resultado);
                    });
                }
                // Garantir que a seção de resultados e os listeners estejam ativos antes de finalizar
                const resultadosSection = document.getElementById('resultadosSection');
                if (resultadosSection) {
                    resultadosSection.style.display = 'block';
                    anexarEventListenersExportacao();
                }
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
                // Atualizar processos que foram processados
                if (data.resultados_parciais && data.resultados_parciais.length > 0) {
                    data.resultados_parciais.forEach((resultado) => {
                        atualizarProcesso(resultado.numero_processo, resultado);
                    });
                }
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
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

function finalizarScraping() {
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
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.btn-extracoes, .btn-downloads, .btn-scraper').forEach(btn => {
        btn.classList.remove('active');
    });

    const scraperBtn = document.getElementById('scraperBtn');

    if (tabName === 'extracoes') {
        const extracoesTab = document.getElementById('extracoesTab');
        const extracoesBtn = document.getElementById('extracoesBtn');
        if (extracoesTab) extracoesTab.classList.add('active');
        if (extracoesBtn) extracoesBtn.classList.add('active');
        if (scraperBtn) scraperBtn.style.display = 'flex';
        setTimeout(() => loadExtracoes(), 100);
    } else if (tabName === 'downloads') {
        const downloadsTab = document.getElementById('downloadsTab');
        const downloadsBtn = document.getElementById('downloadsBtn');
        if (downloadsTab) downloadsTab.classList.add('active');
        if (downloadsBtn) downloadsBtn.classList.add('active');
        if (scraperBtn) scraperBtn.style.display = 'flex';
        setTimeout(() => loadDownloads(), 100);
    } else {
        const scraperTab = document.getElementById('scraperTab');
        if (scraperTab) scraperTab.classList.add('active');
        if (scraperBtn) {
            scraperBtn.classList.add('active');
            scraperBtn.style.display = 'none';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const extracoesBtn = document.getElementById('extracoesBtn');
    const downloadsBtn = document.getElementById('downloadsBtn');
    const scraperBtn = document.getElementById('scraperBtn');
    const refreshBtn = document.getElementById('refreshExtracoes');
    const refreshDownloads = document.getElementById('refreshDownloads');

    if (extracoesBtn) {
        extracoesBtn.addEventListener('click', () => switchTab('extracoes'));
    }
    if (downloadsBtn) {
        downloadsBtn.addEventListener('click', () => switchTab('downloads'));
    }
    if (scraperBtn) {
        scraperBtn.addEventListener('click', () => switchTab('scraper'));
    }
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadExtracoes);
    }
    if (refreshDownloads) {
        refreshDownloads.addEventListener('click', loadDownloads);
    }
});

async function loadDownloads() {
    const downloadsTab = document.getElementById('downloadsTab');
    const downloadsList = document.getElementById('downloadsList');
    if (!downloadsTab || !downloadsTab.classList.contains('active') || !downloadsList) {
        return;
    }

    downloadsList.innerHTML = `
        <div class="extracoes-loading">
            <span class="spinner-small"></span>
            <span>Carregando downloads...</span>
        </div>
    `;

    try {
        const response = await fetch('/api/downloads/listar');
        if (!response.ok) {
            throw new Error('Falha ao listar downloads');
        }
        const data = await response.json();
        const apps = data.apps || [];

        if (!apps.length) {
            downloadsList.innerHTML = `
                <div class="downloads-empty">
                    Nenhum aplicativo publicado ainda.
                </div>
            `;
            return;
        }

        downloadsList.innerHTML = apps.map((app) => {
            const version = app.version
                ? `<strong>v${app.version}</strong>`
                : '<em>sem versão publicada</em>';
            const when = app.released_at
                ? ` · ${new Date(app.released_at).toLocaleString('pt-BR')}`
                : '';
            const notes = app.notes
                ? `<p class="downloads-meta">${app.notes}</p>`
                : '';
            const files = (app.files || []);
            const buttons = files.length
                ? files.map((f) => `
                    <a class="btn btn-secondary"
                       href="/api/downloads/file/${encodeURIComponent(app.app_id)}/${encodeURIComponent(f.filename)}"
                       download>
                        ${f.label || f.filename}
                    </a>
                `).join('')
                : `<span class="downloads-meta">Arquivos ainda não disponíveis no servidor.</span>`;

            return `
                <div class="downloads-app-card">
                    <h3>${app.name || app.app_id}</h3>
                    <div class="downloads-meta">${version}${when}</div>
                    ${notes}
                    <div class="downloads-actions">${buttons}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Erro ao carregar downloads:', error);
        downloadsList.innerHTML = `
            <div class="downloads-empty">
                Erro ao carregar downloads. Faça login novamente ou tente atualizar.
            </div>
        `;
    }
}

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
                const totalProcessos = data.extracoes.reduce((sum, e) => sum + (e.estatisticas?.total_processos || 0), 0);
                const raspado = data.extracoes.filter(e => e.tipo === 'raspado').length;
                const tratado = data.extracoes.filter(e => e.tipo === 'tratado').length;
                
                extracoesStats.innerHTML = `
                    ${totalProcessos > 0 ? `<span class="stat-item-extracao">📊 ${totalProcessos} processos</span>` : ''}
                    ${raspado > 0 ? `<span class="stat-item-extracao">📄 ${raspado} raspado${raspado !== 1 ? 's' : ''}</span>` : ''}
                    ${tratado > 0 ? `<span class="stat-item-extracao">✅ ${tratado} tratado${tratado !== 1 ? 's' : ''}</span>` : ''}
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
                
                const tipoLabel = extracao.tipo === 'raspado' ? 'Raspado' : 'Tratado';
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
                            <span class="extracao-cell-badge ${extracao.tipo}">
                                ${extracao.tipo === 'raspado' ? '📄' : '✅'} ${tipoLabel}
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