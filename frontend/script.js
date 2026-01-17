let currentMode = 'validacion';
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const submitBtn = document.getElementById('submitBtn');
const fileList = document.getElementById('selectedFilesList');
const resultArea = document.getElementById('resultArea');
const loading = document.getElementById('loading');

// Mode Switching
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (token) {
        try {
            const res = await fetch('/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.ok) {
                const user = await res.json();
                const ui = document.getElementById('userInfoDisplay');
                if (ui) {
                    const name = user.full_name || user.username;
                    ui.innerHTML = `<i class="fas fa-user-circle" style="margin-right: 8px;"></i> ${name} <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; margin-left: 10px; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.4);">${user.role.toUpperCase()}</span>`;
                }
            }
        } catch (e) {
            console.error(e);
        }
    }
});

function setMode(mode) {
    currentMode = mode;
    document.getElementById('btnValidacion').classList.toggle('active', mode === 'validacion');
    document.getElementById('btnFatiga').classList.toggle('active', mode === 'fatiga');

    // Reset files and UI
    fileInput.value = '';
    updateFileList([]);
    resultArea.style.display = 'none';

    const uploadText = document.getElementById('uploadText');
    if (mode === 'validacion') {
        uploadText.innerText = 'Arrastra exactamente 2 archivos aquí';
        submitBtn.innerText = 'Validar Archivos';
    } else {
        uploadText.innerText = 'Arrastra entre 2 y 10 archivos aquí';
        submitBtn.innerText = 'Ejecutar Fatiga';
    }
}

// Drag & Drop
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--primary-color)';
    dropZone.style.backgroundColor = 'rgba(99, 102, 241, 0.1)';
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--glass-border)';
    dropZone.style.backgroundColor = 'transparent';
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = 'var(--glass-border)';
    dropZone.style.backgroundColor = 'transparent';
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

let selectedFiles = [];

function handleFiles(files) {
    selectedFiles = Array.from(files);
    updateFileList(selectedFiles);
    validateConstraints();
}

function updateFileList(files) {
    fileList.innerHTML = '';
    files.forEach(file => {
        const li = document.createElement('li');
        li.innerHTML = `<i class="far fa-file-excel"></i> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileList.appendChild(li);
    });
}

function validateConstraints() {
    let isValid = false;
    const count = selectedFiles.length;

    if (currentMode === 'validacion') {
        isValid = count === 2;
    } else {
        isValid = count >= 2 && count <= 10;
    }

    submitBtn.disabled = !isValid;

    // Optional: Visual feedback if too many files
    if (currentMode === 'validacion' && count > 2) {
        fileList.innerHTML += `<li style="color: var(--error)">Error: Solo se permiten 2 archivos en modo Validación.</li>`;
    }
}

async function processFiles() {
    if (submitBtn.disabled) return;

    loading.style.display = 'block';
    resultArea.style.display = 'none';
    submitBtn.disabled = true;

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    const endpoint = currentMode === 'validacion'
        ? '/validate'
        : '/fatiga';

    // Add mapping if exists
    if (currentMapping) {
        formData.append('mapping', JSON.stringify(currentMapping));
        // Reset mapping after use? Or keep for retry? 
        // Better keep until success or file change.
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        loading.style.display = 'none';
        submitBtn.disabled = false;

        // Check for Excel File
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") !== -1) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Extract filename from header or fallback
            let filename = "Reporte_Validacion.xlsx";
            const disposition = response.headers.get('content-disposition');
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            a.download = currentMode === 'validacion' ? filename : "Reporte_Fatiga.xlsx";
            document.body.appendChild(a);
            a.click();
            a.remove();

            // Clear mapping on success
            currentMapping = null;

            showResult(true, { message: "Reporte generado y descargado exitosamente." });
            return;
        }

        const data = await response.json();

        if (response.status === 409) {
            showMappingUI(data);
            return;
        }

        showResult(response.ok, data);

    } catch (error) {
        loading.style.display = 'none';
        submitBtn.disabled = false;
        showResult(false, { detail: "Error: " + error });
    }
}

function showResult(success, data) {
    resultArea.style.display = 'block';
    resultArea.className = 'result-area ' + (success ? 'success' : 'error');

    const title = document.getElementById('resultTitle');
    const message = document.getElementById('resultMessage');
    const details = document.getElementById('errorDetails');

    details.innerHTML = '';

    if (success) {
        title.innerText = '¡Éxito!';
        message.innerText = data.message || 'Operación completada correctamente.';

        if (data.details) {
            const info = document.createElement('div');
            info.style.marginTop = '10px';
            info.style.fontSize = '0.9rem';
            info.innerHTML = `
                <p>Archivos procesados: ${data.details.files_processed.join(', ')}</p>
                <p>Filas validadas: ${data.details.rows_validated}</p>
            `;
            details.appendChild(info);
        }
    } else {
        title.innerText = 'Error de Validación';
        message.innerText = data.detail || 'Ocurrió un error desconocido.';

        // Handle specific validation errors list if present
        // Depending on how backend sends it. 
        // Currently backend sends 'detail' as a string if it's a 400 exception.
        // If we returned a JSON with errors list manually:
        if (data.errors && Array.isArray(data.errors)) {
            const ul = document.createElement('ul');
            ul.style.marginTop = '10px';
            data.errors.forEach(err => {
                const li = document.createElement('li');
                li.innerText = err;
                ul.appendChild(li);
            });
            details.appendChild(ul);
        }
    }
}

// --- MAPPING UI ---
const mappingModal = document.getElementById('mappingModal');
let currentMapping = null;

function showMappingUI(data) {
    mappingModal.style.display = 'block';

    // Helper to create selects
    const createSelects = (containerId, titleId, fileName, fileCols, required, missing) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        const title = document.getElementById(titleId);
        if (title) title.innerText = fileName || 'Archivo';

        container.innerHTML = ''; // Clear

        required.forEach(field => {
            const row = document.createElement('div');
            row.className = 'mapping-row';
            row.style.marginBottom = '10px';

            const label = document.createElement('label');
            label.innerText = field;
            label.style.display = 'block';
            label.style.fontWeight = 'bold';
            if (missing && missing.includes(field)) {
                label.style.color = '#ef4444'; // Red
                label.innerText += ' (Falta)';
            }

            const select = document.createElement('select');
            select.dataset.field = field;
            select.style.width = '100%';
            select.style.padding = '5px';

            // Default option
            const def = document.createElement('option');
            def.value = '';
            def.innerText = '-- Seleccionar --';
            select.appendChild(def);

            fileCols.forEach(col => {
                const opt = document.createElement('option');
                opt.value = col;
                opt.innerText = col;
                if (col.toLowerCase() === field.toLowerCase()) opt.selected = true;
                select.appendChild(opt);
            });

            row.appendChild(label);
            row.appendChild(select);
            container.appendChild(row);
        });
    };

    createSelects('mappingFile1', 'mappingTitle1', data.file_1_name, data.file_1_columns, data.required_fields, data.missing_1);
    createSelects('mappingFile2', 'mappingTitle2', data.file_2_name, data.file_2_columns, data.required_fields, data.missing_2);
}

function closeMapping() {
    mappingModal.style.display = 'none';
}

function submitMapping() {
    const getMapping = (containerId) => {
        const map = {};
        const selects = document.querySelectorAll(`#${containerId} select`);
        selects.forEach(s => {
            if (s.value) map[s.dataset.field] = s.value;
        });
        return map;
    };

    currentMapping = {
        file1: getMapping('mappingFile1'),
        file2: getMapping('mappingFile2')
    };

    closeMapping();
    processFiles();
}

// Add event listener for file change to reset mapping
fileInput.addEventListener('click', () => {
    currentMapping = null;
});
