let processosData = [];
let resultadosData = [];

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
            processosData = data.processos;
            mostrarProcessos(data.processos);
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

function mostrarProcessos(processos) {
    const section = document.getElementById('processosSection');
    const list = document.getElementById('processosList');
    const countDiv = document.getElementById('processosCount');
    const statsDiv = document.getElementById('processosStats');
    
    const sucesso = processos.filter(p => p.status === 'sucesso').length;
    const erro = processos.filter(p => p.status === 'erro').length;
    const pendente = processos.filter(p => p.status === 'pendente').length;
    
    countDiv.textContent = `${processos.length} processos encontrados`;
    
    statsDiv.innerHTML = `
        ${sucesso > 0 ? `<span class="stat-item success">✓ ${sucesso} válidos</span>` : ''}
        ${erro > 0 ? `<span class="stat-item error">✗ ${erro} inválidos</span>` : ''}
        ${pendente > 0 ? `<span class="stat-item pending">⏳ ${pendente} pendentes</span>` : ''}
    `;
    
    list.innerHTML = processos.map(p => `
        <div class="processo-item ${p.status}">
            <div class="processo-header">
                <div>
                    <div class="processo-numero">${p.numero_processo}</div>
                    <div class="processo-tribunal">${p.tribunal || 'Não identificado'}</div>
                </div>
            </div>
            <div class="processo-status ${p.status}">
                ${p.status === 'sucesso' ? '✓' : p.status === 'erro' ? '✗' : '⏳'} ${p.status}
            </div>
        </div>
    `).join('');
    
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Iniciar scraping
document.getElementById('iniciarScraping')?.addEventListener('click', async () => {
    const button = document.getElementById('iniciarScraping');
    button.disabled = true;
    button.querySelector('.btn-content').style.display = 'none';
    button.querySelector('.btn-loader').style.display = 'flex';
    
    try {
        const response = await fetch('/api/processos/scraper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ processos: processosData })
        });
        
        const data = await response.json();
        if (data.success) {
            resultadosData = data.resultados;
            mostrarResultados(data.resultados);
            document.getElementById('resultadosSection').style.display = 'block';
            document.getElementById('resultadosSection').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            showToast('Raspagem concluída com sucesso!', 'success');
        } else {
            showToast('Erro: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Erro ao iniciar scraping: ' + error.message, 'error');
    } finally {
        button.disabled = false;
        button.querySelector('.btn-content').style.display = 'flex';
        button.querySelector('.btn-loader').style.display = 'none';
    }
});

function mostrarResultados(resultados) {
    const list = document.getElementById('resultadosList');
    const countDiv = document.getElementById('resultadosCount');
    const statsDiv = document.getElementById('resultadosStats');
    
    const sucesso = resultados.filter(r => r.status === 'sucesso').length;
    const erro = resultados.filter(r => r.status === 'erro').length;
    
    countDiv.textContent = `${resultados.length} processos processados`;
    
    statsDiv.innerHTML = `
        ${sucesso > 0 ? `<span class="stat-item success">✓ ${sucesso} sucesso</span>` : ''}
        ${erro > 0 ? `<span class="stat-item error">✗ ${erro} erros</span>` : ''}
    `;
    
    list.innerHTML = resultados.map(r => `
        <div class="processo-item ${r.status}">
            <div class="processo-header">
                <div>
                    <div class="processo-numero">${r.numero_processo}</div>
                    <div class="processo-tribunal">${r.tribunal || ''}</div>
                </div>
            </div>
            ${r.dados?.dados_processo?.assunto ? `
                <div class="processo-info">
                    <strong>Assunto:</strong> ${r.dados.dados_processo.assunto.substring(0, 100)}${r.dados.dados_processo.assunto.length > 100 ? '...' : ''}
                </div>
            ` : ''}
            ${r.erro ? `
                <div class="processo-info" style="color: var(--error);">
                    <strong>Erro:</strong> ${r.erro}
                </div>
            ` : ''}
            <div class="processo-status ${r.status}">
                ${r.status === 'sucesso' ? '✓' : '✗'} ${r.status}
            </div>
        </div>
    `).join('');
}

// Exportar resultados
document.getElementById('exportarResultados')?.addEventListener('click', async () => {
    const button = document.getElementById('exportarResultados');
    button.disabled = true;
    
    try {
        const response = await fetch('/api/resultados/exportar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ resultados: resultadosData })
        });
        
        const contentType = response.headers.get('content-type');
        
        if (response.ok) {
            if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `resultados_${new Date().getTime()}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                showToast('Arquivo exportado com sucesso!', 'success');
            } else {
                const data = await response.json();
                if (data.error) {
                    showToast('Erro ao exportar: ' + data.error, 'error');
                }
            }
        } else {
            try {
                const errorData = await response.json();
                showToast('Erro ao exportar: ' + (errorData.error || 'Erro desconhecido'), 'error');
            } catch (e) {
                showToast('Erro ao exportar: ' + response.statusText, 'error');
            }
        }
    } catch (error) {
        showToast('Erro ao exportar: ' + error.message, 'error');
    } finally {
        button.disabled = false;
    }
});