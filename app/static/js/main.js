let processosData = [];
let isScraping = false;
let scrapingSessionId = null;
let pollingInterval = null;
let abortRequested = false;
let tribunaisMap = {}; // Mapa de códigos para nomes

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// File upload handling
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

// Drag and drop
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

// Upload form
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
    
    // Show loading state
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

// Carregar tribunais disponíveis
async function carregarTribunais() {
    const container = document.getElementById('tribunaisContainer');
    
    try {
        const response = await fetch('/api/tribunais');
        const data = await response.json();
        
        if (data.success && data.tribunais) {
            // Criar mapa de códigos para nomes
            data.tribunais.forEach(t => {
                tribunaisMap[t.codigo] = t.nome;
            });
            
            // Exibir tribunais na sidebar
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

// Função auxiliar para obter nome do tribunal
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
    }
}

// Iniciar scraping
document.getElementById('actionButton')?.addEventListener('click', async () => {
    const button = document.getElementById('actionButton');
    
    // Verificar se o botão está no modo de exportar (tem classe btn-success)
    if (button.classList.contains('btn-success')) {
        exportarResultados();
        return;
    }
    
    // Se estiver fazendo scraping, não fazer nada
    if (isScraping) {
        return;
    }
    
    const abortButton = document.getElementById('abortarScraping');
    
    if (!abortButton) {
        console.error('Botão abortarScraping não encontrado!');
        return;
    }
    
    button.disabled = true;
    button.querySelector('.btn-content').style.display = 'none';
    button.querySelector('.btn-loader').style.display = 'flex';
    
    // Mostrar botão abortar (usar !important via setAttribute)
    abortButton.style.display = 'inline-flex';
    abortButton.style.setProperty('display', 'inline-flex', 'important');
    
    isScraping = true;
    abortRequested = false;
    
    // Marcar todos como processando
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
    
    if (!button || !abortButton) {
        console.error('Botões não encontrados!');
        return;
    }
    
    // Mudar botão para exportar
    const icon = button.querySelector('.action-icon');
    const text = button.querySelector('.action-text');
    const loaderText = button.querySelector('.loader-text');
    
    if (icon) {
        icon.innerHTML = '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>';
    }
    if (text) {
        text.textContent = 'Exportar para Excel';
    }
    if (loaderText) {
        loaderText.textContent = 'Exportando...';
    }
    
    button.disabled = false;
    const btnContent = button.querySelector('.btn-content');
    const btnLoader = button.querySelector('.btn-loader');
    
    if (btnContent) btnContent.style.display = 'flex';
    if (btnLoader) btnLoader.style.display = 'none';
    
    button.classList.remove('btn-primary');
    button.classList.add('btn-success');
    
    // Esconder botão abortar
    abortButton.style.display = 'none';
    abortButton.style.setProperty('display', 'none', 'important');
}

function resetScrapingState() {
    isScraping = false;
    scrapingSessionId = null;
    stopPolling();
    
    const button = document.getElementById('actionButton');
    const abortButton = document.getElementById('abortarScraping');
    
    if (!button || !abortButton) {
        console.error('Botões não encontrados!');
        return;
    }
    
    // Reverter processos pendentes que estavam processando
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
    
    // Remover classe btn-success se existir
    button.classList.remove('btn-success');
    button.classList.add('btn-primary');
    
    // Esconder botão abortar
    abortButton.style.display = 'none';
    abortButton.style.setProperty('display', 'none', 'important');
}

// Abortar scraping
document.getElementById('abortarScraping')?.addEventListener('click', async () => {
    if (!scrapingSessionId) return;
    
    abortRequested = true;
    const abortButton = document.getElementById('abortarScraping');
    abortButton.disabled = true;
    
    try {
        const response = await fetch(`/api/processos/abort/${scrapingSessionId}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            stopPolling();
            resetScrapingState();
            showToast('Scraping abortado com sucesso', 'error');
        } else {
            showToast('Erro ao abortar: ' + data.error, 'error');
            abortButton.disabled = false;
        }
    } catch (error) {
        showToast('Erro ao abortar scraping: ' + error.message, 'error');
        abortButton.disabled = false;
    }
});

// Exportar resultados
function exportarResultados() {
    const button = document.getElementById('actionButton');
    button.disabled = true;
    button.querySelector('.btn-content').style.display = 'none';
    button.querySelector('.btn-loader').style.display = 'flex';
    
    const resultados = processosData.filter(p => p.status === 'sucesso' || p.status === 'erro');
    
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
                    a.download = `resultados_${new Date().getTime()}.xlsx`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    showToast('Arquivo exportado com sucesso!', 'success');
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

// Carregar tribunais ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    carregarTribunais();
});