const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

// Setup Auth Header
const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

// State
let currentCallId = null;
let currentUserRole = null;
let currentUserName = null; // Store full name of current agent
let isClosedView = false; // Track if we are in Closed Studies mode
let studySelectTS = null; // TomSelect instance for main study dropdown

const obsCategories = [
    { label: "LLAMADA", category: "call", options: ["No Contesta", "Buzón de Voz", "Ocupado", "Llamar Luego", "No quiere contestar"] },
    { label: "WHATSAPP", category: "whatsapp", options: ["No Contesta", "No tiene whatsapp", "Mensaje Enviado", "No responde"] },
    { label: "SMS", category: "sms", options: ["No Contesta", "Mensaje Enviado"] },
    { label: "VIDEO", category: "video", options: ["No Contesta", "Rechaza Video"] },
    { label: "RESULTADO", category: "result", options: [
        { text: "Efectiva", type: "positive" },
        "No quiere contestar", "Cita Agendada", "No cumple el filtro del estudio", "Número Errado", "Uso otro producto"
    ]}
];

const statusMap = {
    'pending': 'Pendiente',
    'management': 'Gestionando',
    'scheduled': 'Agendado',
    'done': 'Terminado',
    'closed': 'Cerrado',
    // New caída options - RENAMED LABELS
    'caida_desempeno': 'Desempeño',
    'caida_logistica': 'Logístico',
    'caida_desempeno_campo': 'Caída Desempeño Campo', // Keep? User said "Caída Desempeño" -> "Desempeño"
    'caida_logistico_campo': 'Caída Logístico',
    // Legacy caídas mapping
    'caidas': 'Caída',
    'caida': 'Caída',
    // En campo statuses
    'en_campo': 'En Campo',
    'en campo': 'En Campo',
    'efectiva_campo': 'Efectiva Presencial', // Renamed from Efectiva en Campo
    'managed': 'Efectiva' // Renamed from Gestionado
};

const translateStatus = (s) => statusMap[s] || s;

// Init
document.addEventListener('DOMContentLoaded', async () => {
    // Ensure Excel pastes always trigger parsing (some browsers/extensions don't fire `input` reliably on paste)
    const pasteArea = document.getElementById('pasteArea');
    if (pasteArea) {
        pasteArea.addEventListener('paste', () => {
            setTimeout(() => {
                try {
                    handlePasteData();
                } catch (e) {
                    console.error('Error parsing pasted data', e);
                }
            }, 0);
        });
    }

    // Load User Info
    try {
        const uRes = await fetch('/users/me', { headers });
        if (uRes.ok) {
            const user = await uRes.json();
            currentUserRole = user.role;
            currentUserName = user.full_name || user.username;
            const infoDivs = ['userInfoDisplay', 'userInfoDisplayLanding'];
            infoDivs.forEach(id => {
                const ui = document.getElementById(id);
                if (ui) {
                    ui.innerHTML = `
                        <div style="text-align: right; margin-right: 10px;">
                            <div style="font-weight: bold;">${user.full_name || user.username}</div>
                        </div>
                        <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; border: 1px solid rgba(255,255,255,0.4); text-transform: uppercase;">${user.role}</span>
                        <i class="fas fa-user-circle" style="font-size: 2rem; margin-left: 10px;"></i>
                    `;
                }
            });

            if (currentUserRole === 'superuser' || currentUserRole === 'coordinator' || currentUserRole === 'auxiliar') {
                // Show Import action for Superuser/Coordinator/Agent (for Filtros)
                const importAct = document.getElementById('importAction');
                if (importAct) importAct.style.display = 'block'; 
                // Note: The specific Traer de otro estudio button inside it is restricted later in JS if needed
                // but usually agents don't see the sidebar if they are not in CRM.

                // Show Landing, Hide CRM
                document.getElementById('superuserLanding').style.display = 'flex';
                document.getElementById('crmInterface').style.display = 'none';

                // Cargar Base y Gestión de Estudios only for Superuser/Coordinator
                const btnUpload = document.getElementById('btnUploadExcelLanding');
                const btnManage = document.getElementById('btnManageStudiesLanding');
                const btnReport = document.getElementById('btnDailyReportLanding');
                const btnDup = document.getElementById('btnDuplicateValidator');
                const btnBack = document.getElementById('btnBackToDashboard');

                if (btnUpload) btnUpload.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';
                if (btnManage) btnManage.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';
                if (btnReport) btnReport.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';
                if (btnDup) btnDup.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';
                if (btnBack) btnBack.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator' || currentUserRole === 'auxiliar') ? 'inline-block' : 'none';
                
                const btnBonos = document.getElementById('btnBonosEstudiosLanding');
                if (btnBonos) btnBonos.style.display = (currentUserRole === 'superuser') ? 'inline-block' : 'none';

                const btnFilters = document.getElementById('btnFiltersLanding');
                if (btnFilters) btnFilters.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';

                // Ensure Create Study Button is visible if they enter the CRM (only for super/coord)
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = (currentUserRole === 'superuser' || currentUserRole === 'coordinator') ? 'inline-block' : 'none';

                // Show Closed Studies Button for Superuser and Auxiliar
                if (currentUserRole === 'superuser' || currentUserRole === 'auxiliar' || currentUserRole === 'coordinator') {
                    const btnClosed = document.getElementById('btnClosedStudies');
                    if (btnClosed) btnClosed.style.display = 'inline-block'; // or block/flex depending on css
                }
                
                // Add a "Atender Filtros" button for agents/auxiliars on landing if desired
                // For now, they enter via CRM or we add a button here
                if (currentUserRole === 'agent' || currentUserRole === 'bizage' || currentUserRole === 'auxiliar') {
                    // If they are on landing, let's give them a way to enter filters
                }
            } else {
                // Normal User
                // Hide Create Study Button
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = 'none';
                loadStudies();
            }

            // Ensure search is visible for EVERYONE
            const search = document.getElementById('searchPanel');
            if (search) search.style.display = 'block';

            // AUTOMATICALLY LOAD ALL PENDING CALLS
            loadStudyData(null); // Null = all pending from open studies

            if (typeof initAlarmPolling === 'function') {
                initAlarmPolling();
            }

            // Show Excel Button for Superuser/Auxiliar/Coordinator
            if (currentUserRole === 'superuser' || currentUserRole === 'auxiliar' || currentUserRole === 'coordinator') {
                const btnExport = document.getElementById('btnExportExcel');
                if (btnExport) btnExport.style.display = 'inline-block';
            }



        } else {
            loadStudies();
            const btn = document.getElementById('btnCreateStudy');
            if (btn) btn.style.display = 'none';
            const search = document.getElementById('searchPanel');
            if (search) search.style.display = 'none';
            loadStudyData(null);
        }
    } catch (e) {
        console.error(e);
    }
});

// Superuser Functions
function enterCRM(showClosed = false) {
    document.getElementById('superuserLanding').style.display = 'none';
    document.getElementById('crmInterface').style.display = 'grid'; // Restore grid

    // Toggle Online Bars
    const landingBar = document.getElementById('onlineHeaderBar_Landing');
    const crmBar = document.getElementById('onlineHeaderBar_CRM');
    if (landingBar) landingBar.style.display = 'none';
    if (crmBar) crmBar.style.display = 'flex';

    isClosedView = showClosed; // Set global state

    if (showClosed) {
        // Change title to indicate closed studies
        const titleEl = document.querySelector('#crmInterface h1');
        if (titleEl) titleEl.textContent = 'Call Center CRM - Estudios Cerrados';
    } else {
        const titleEl = document.querySelector('#crmInterface h1');
        if (titleEl) titleEl.textContent = 'Call Center CRM';
    }

    loadStudies(showClosed);

    // Logic for loading data:
    if (showClosed) {
        // IMPORTANT: Clear global data cache so filters don't show old data
        allCalls = [];
        renderCallGrid([]);
        document.getElementById('callCounter').textContent = '(Seleccione un estudio cerrado)';
    } else {
        loadStudyData(null); // Load global calls
    }

    loadAgents(); // Load users for assignment

    // Toggle Temp Columns visibility based on role
    const armandoCols = document.querySelectorAll('.col-temp-armando');
    const auxiliarCols = document.querySelectorAll('.col-temp-auxiliar');

    if (currentUserRole === 'superuser') {
        armandoCols.forEach(el => el.style.display = 'table-cell');
        auxiliarCols.forEach(el => el.style.display = 'table-cell');
    } else if (currentUserRole === 'auxiliar') {
        armandoCols.forEach(el => el.style.display = 'none');
        auxiliarCols.forEach(el => el.style.display = 'table-cell');
    } else {
        armandoCols.forEach(el => el.style.display = 'none');
        auxiliarCols.forEach(el => el.style.display = 'none');
    }
}

async function updateTempInfo(callId, field, value) {
    try {
        const body = {};
        body[field] = value;

        // Optimistic UI update? No need, it's an input.
        // Debouncing could be good but for now plain onchange/onblur

        const res = await fetch(`/calls/${callId}/temp-info`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body)
        });

        if (!res.ok) {
            const err = await res.json();
            alert("Error al actualizar: " + err.detail);
        } else {
            // Optional: visual feedback
            console.log("Updated", field);
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión al guardar");
    }
}

let parsedUploadData = [];
let uploadHeaders = [];
let columnMappings = [];
let uploadMode = 'new'; // 'new' | 'existing'

const STANDARD_FIELDS = [
    { id: 'ignorar', label: '-- Ignorar esta columna --' },
    { id: 'telefono', label: 'Teléfono / Celular' },
    { id: 'nombre', label: 'Nombre' },
    { id: 'ciudad', label: 'Ciudad' },
    { id: 'observaciones', label: 'Observaciones' },
    { id: 'hora de llamada', label: 'Hora de Llamada' },
    { id: 'marca de producto', label: 'Marca de Producto' },
    { id: 'otro numero', label: 'Teléfono Alterno' },
    { id: 'cedula', label: 'Cédula / Documento' },
    { id: 'nse', label: 'NSE / Estrato' },
    { id: 'edad', label: 'Edad' },
    { id: 'rango edad', label: 'Rango de Edad' },
    { id: 'edad hijos', label: 'Edad Hijos' },
    { id: 'whatsapp', label: 'WhatsApp' },
    { id: 'barrio', label: 'Barrio' },
    { id: 'direccion', label: 'Dirección' },
    { id: 'descripcion vivienda', label: 'Descripción Vivienda' },
    { id: 'encuestado', label: 'Persona Entrevistada' },
    { id: 'supervisor', label: 'Supervisor' },
    { id: 'fecha implantacion', label: 'Fecha Implantación' },
    { id: 'fecha recoleccion', label: 'Fecha Recogida' },
    { id: 'hora recoleccion', label: 'Hora Recogida' },
    { id: 'censo', label: 'Censo / ID' },
    { id: 'encuestador', label: 'Encuestador' },
    { id: 'nombre del perro', label: 'Nombre Mascota' },
    { id: 'marca de shampoo', label: 'Marca Shampoo' },
    { id: 'variedad shampoo', label: 'Variedad Shampoo' },
    { id: 'marca tratamiento', label: 'Marca Tratamiento' },
    { id: 'variedad tratamiento', label: 'Variedad Tratamiento' },
    { id: 'marca acondicionador', label: 'Marca Acondicionador' },
    { id: 'variedad acondicionador', label: 'Variedad Acondicionador' },
    { id: 'frecuencia de lavado', label: 'Frecuencia Lavado' },
    { id: 'tipo de cabello', label: 'Tipo de Cabello' },
    { id: 'forma de cabello', label: 'Forma de Cabello' },
    { id: 'largo de cabello', label: 'Largo de Cabello' },
    { id: 'frecuencia de compra', label: 'Frecuencia de Compra' }
];

const CATEGORY_RULES = {
    'cabello': {
        expected: ['telefono', 'nombre', 'ciudad', 'marca'],
        forbidden: ['perro', 'raza', 'mascota'],
        hints: 'Recomendado para Cabello: Teléfono, Nombre, Ciudad, Marca Shampoo, Largo de Cabello. No incluya datos de mascotas.'
    },
    'mascotas': {
        expected: ['telefono', 'nombre', 'ciudad', 'perro'],
        forbidden: ['shampoo', 'cabello', 'acondicionador'],
        hints: 'Recomendado para Mascotas: Teléfono, Nombre, Ciudad, Nombre del perro. No incluya datos de cabello.'
    },
    'general': {
        expected: ['telefono', 'nombre', 'ciudad'],
        forbidden: [],
        hints: 'Recomendado: Teléfono, Nombre, Ciudad.'
    }
};

function updateUploadHints() {
    const cat = document.getElementById('uploadCategory').value;
    const hintsEl = document.getElementById('uploadHints');
    if (CATEGORY_RULES[cat]) {
        hintsEl.textContent = CATEGORY_RULES[cat].hints;
    }
    // Re-validate if data exists
    if (parsedUploadData.length > 0) {
        validateParsedData();
    }
}

async function showUploadModal(existing = false) {
    document.getElementById('uploadModal').style.display = 'flex';
    document.getElementById('uploadStudyName').value = '';
    document.getElementById('pasteArea').value = '';
    document.getElementById('previewContainer').style.display = 'none';
    document.getElementById('uploadAlertBox').style.display = 'none';
    document.getElementById('uploadError').style.display = 'none';
    document.getElementById('btnFinalUpload').style.opacity = '0.5';
    document.getElementById('btnFinalUpload').disabled = true;
    parsedUploadData = [];
    uploadHeaders = [];
    columnMappings = [];
    updateUploadHints();
    await setUploadMode(existing ? 'existing' : 'new');
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

async function setUploadMode(mode) {
    uploadMode = mode;
    const btnNew = document.getElementById('btnUploadModeNew');
    const btnExisting = document.getElementById('btnUploadModeExisting');

    // Toggle buttons style
    if (btnNew && btnExisting) {
        const isNew = mode === 'new';
        btnNew.style.background = isNew ? '#6366f1' : 'white';
        btnNew.style.color = isNew ? 'white' : '#0f172a';
        btnExisting.style.background = !isNew ? '#14b8a6' : 'white';
        btnExisting.style.color = !isNew ? 'white' : '#0f172a';
    }

    // Toggle form fields
    const studyNameInput = document.getElementById('uploadStudyName');
    const studyTypeSel = document.getElementById('uploadStudyType');
    const studyStageSel = document.getElementById('uploadStudyStage');
    const existingGroup = document.getElementById('uploadExistingStudyGroup');
    const existingSelect = document.getElementById('uploadExistingStudySelect');

    const isExisting = mode === 'existing';

    if (studyNameInput) studyNameInput.parentElement.style.display = isExisting ? 'none' : 'block';
    if (studyTypeSel) studyTypeSel.parentElement.style.display = isExisting ? 'none' : 'block';
    if (studyStageSel) studyStageSel.parentElement.style.display = isExisting ? 'none' : 'block';
    if (existingGroup) existingGroup.style.display = isExisting ? 'block' : 'none';

    if (isExisting && existingSelect) {
        await loadStudiesIntoUploadSelect();
    }

    // Re-validate button state
    if (parsedUploadData.length > 0) validateParsedData();
}

async function loadStudiesIntoUploadSelect() {
    const sel = document.getElementById('uploadExistingStudySelect');
    if (!sel) return;

    sel.innerHTML = '<option value="">Cargando...</option>';
    try {
        const res = await fetch('/studies?include_inactive=true', { headers });
        if (!res.ok) throw new Error('Could not load studies');
        const studies = await res.json();

        // Sort active first, then by name
        const sorted = (studies || []).sort((a, b) => {
            const ai = (a.is_active === true || a.is_active === 1) ? 1 : 0;
            const bi = (b.is_active === true || b.is_active === 1) ? 1 : 0;
            if (ai !== bi) return bi - ai;
            return (a.name || '').localeCompare((b.name || ''), 'es');
        });

        sel.innerHTML = '<option value="">Seleccione...</option>';
        sorted.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            const state = (s.is_active === true || s.is_active === 1) ? 'Abierto' : 'Cerrado';
            opt.textContent = `[${state}] ${s.code || 'S/C'} - ${s.name}`;
            sel.appendChild(opt);
        });
    } catch (e) {
        console.error(e);
        sel.innerHTML = '<option value="">Error cargando estudios</option>';
    }
}

function handlePasteData() {
    const text = document.getElementById('pasteArea').value;
    if (!text.trim()) {
        document.getElementById('previewContainer').style.display = 'none';
        document.getElementById('btnFinalUpload').disabled = true;
        document.getElementById('btnFinalUpload').style.opacity = '0.5';
        parsedUploadData = [];
        return;
    }

    // Parse TSV gracefully handling quotes if copied from advanced Excel logic, but standard JS split usually works for simple pasting.
    const rows = text.split('\n').map(row => row.split('\t'));

    // First row is headers
    if (rows.length < 2) return; // Need at least header and 1 row of data

    uploadHeaders = rows[0].map(h => h.trim());
    parsedUploadData = [];

    for (let i = 1; i < rows.length; i++) {
        if (rows[i].length === 1 && rows[i][0].trim() === '') continue; // skip empty rows
        let rowObj = {};
        for (let j = 0; j < uploadHeaders.length; j++) {
            rowObj[uploadHeaders[j]] = (rows[i][j] || "").trim();
        }
        parsedUploadData.push(rowObj);
    }

    // Initialize mapping
    columnMappings = uploadHeaders.map(h => {
        if (isRecognizedColumn(h)) return h; // Keep original if it's already recognized
        return ""; // Unrecognized
    });

    renderPreviewTable();
    validateParsedData();
}

window.updateColumnMapping = function (index, value) {
    columnMappings[index] = value;
    validateParsedData();
    renderPreviewTable();
};

const KNOWN_BACKEND_COLUMNS = [
    "telefono", "teléfono", "celular", "numero", "movil", "ciudad", "city",
    "codigo", "código", "cod", "id", "observaciones", "observacion", "observación", "obs",
    "hora de llamada", "hora", "cita", "marca de producto", "marca", "otro numero", "otro telefono", "telefono 2",
    "cedula", "cédula", "cc", "identificacion", "nombre", "cliente", "usuario", "nombre y apellido", "nombre completo",
    "nse", "estrato", "nivel socioeconomico", "edad", "age", "rango edad", "rango de edad", "edad rango",
    "edad hijos", "hijos", "edades hijos", "whatsapp", "wa", "celular wa",
    "barrio", "neighborhood", "sector", "direccion", "dirección", "address", "dir", "ubicacion",
    "descripcion vivienda", "descripción vivienda", "tipo vivienda", "vivienda",
    "encuestado", "respondent", "persona entrevistada", "supervisor", "sup",
    "fecha implantacion", "fecha implantación", "fecha imp",
    "fecha recoleccion", "fecha recolección", "fecha recogida", "fecha de recogida", "fecha rec",
    "hora recoleccion", "hora recolección", "hora recogida", "hora de recogida", "hora rec",
    "censo", "identifier", "encuestador", "pollster", "nombre encuestador", "implantation_pollster",
    "nombre del perro", "dog name", "mascota", "nombre de la mascota",
    "marca de shampoo", "marca shampoo", "variedad shampoo", "variedad",
    "marca tratamiento", "variedad tratamiento",
    "marca acondicionador", "variedad acondicionador", "variedad tratamiento.1",
    "frecuencia de lavado", "tipo de cabello", "forma de cabello",
    "largo de cabello", "largo", "frecuencia de compra", "frecuencia compra", "con que frecuencia compra shampoo"
];

function isRecognizedColumn(header) {
    const hl = header.toLowerCase().trim();
    if (!hl) return false;
    for (let known of KNOWN_BACKEND_COLUMNS) {
        if (hl === known || (hl.length > 3 && known.includes(hl)) || (known.length > 3 && hl.includes(known))) {
            return true;
        }
    }
    return false;
}

function renderPreviewTable() {
    const thead = document.getElementById('previewThead');
    const tbody = document.getElementById('previewTbody');
    const countSpan = document.getElementById('previewCount');
    const colCountSpan = document.getElementById('previewColCount');

    thead.innerHTML = '';
    tbody.innerHTML = '';
    if (countSpan) countSpan.textContent = parsedUploadData.length;
    if (colCountSpan) colCountSpan.textContent = uploadHeaders.length;
    document.getElementById('previewContainer').style.display = 'flex';

    // Headers
    uploadHeaders.forEach((h, i) => {
        const th = document.createElement('th');
        th.style.padding = '8px';
        th.style.border = '1px solid #cbd5e1';
        th.style.textAlign = 'left';
        th.style.color = '#1e293b';
        th.style.verticalAlign = 'top';

        const mapped = columnMappings[i];
        if (mapped === h) {
            th.innerHTML = `<div style="color:#15803d; font-weight:bold;"><i class="fas fa-check-circle"></i> ${h}</div>`;
        } else if (mapped !== "" && mapped !== "ignorar") {
            const label = STANDARD_FIELDS.find(f => f.id === mapped)?.label || mapped;
            th.innerHTML = `
                <div style="color:#2563eb; font-weight:bold;"><i class="fas fa-link"></i> ${h}</div>
                <div style="font-size:0.75rem; color:#475569;">&rarr; ${label}</div>
                <select style="width:100%; padding:2px; font-size:0.75rem; margin-top:4px; max-width: 150px;" onchange="window.updateColumnMapping(${i}, this.value)">
                    <option value="">-- Cambiar --</option>
                    ${STANDARD_FIELDS.map(s => `<option value="${s.id}">${s.label}</option>`).join('')}
                </select>
            `;
        } else if (mapped === "ignorar") {
            th.innerHTML = `<div style="color:#94a3b8; text-decoration:line-through;"><i class="fas fa-ban"></i> ${h}</div>
                <select style="width:100%; padding:2px; font-size:0.75rem; margin-top:4px; max-width: 150px;" onchange="window.updateColumnMapping(${i}, this.value)">
                    <option value="">-- Ignorar --</option>
                    ${STANDARD_FIELDS.map(s => `<option value="${s.id}">${s.label}</option>`).join('')}
                </select>
            `;
        } else {
            // Unrecognized
            const hl = h.toLowerCase();
            let suggestions = STANDARD_FIELDS.filter(f => {
                if (f.id === 'ignorar') return false;
                const fl = f.label.toLowerCase();
                return hl.includes(f.id) || f.id.includes(hl) || fl.includes(hl) || hl.includes(fl) ||
                    (Math.abs(hl.length - f.id.length) <= 3 && hl.substring(0, 4) === f.id.substring(0, 4));
            });

            let html = `<div style="color:#b45309; font-weight:bold; margin-bottom:4px;"><i class="fas fa-exclamation-triangle"></i> ${h}</div>
                <select style="width:100%; padding:4px; font-size:0.75rem; border:1px solid #f59e0b; border-radius:4px; max-width: 150px;" onchange="window.updateColumnMapping(${i}, this.value)">
                    <option value="">-- Mapear Columna --</option>
                    <option value="ignorar">❌ Ignorar</option>
            `;
            if (suggestions.length > 0) {
                html += `<optgroup label="Sugerencias">`;
                suggestions.forEach(s => html += `<option value="${s.id}">${s.label}</option>`);
                html += `</optgroup>`;
            }
            html += `<optgroup label="Todas las columnas">`;
            STANDARD_FIELDS.filter(f => f.id !== 'ignorar').forEach(s => html += `<option value="${s.id}">${s.label}</option>`);
            html += `</optgroup></select>`;
            th.innerHTML = html;
        }
        thead.appendChild(th);
    });

    // Rows (max 50 for preview performance)
    const previewRows = parsedUploadData.slice(0, 50);
    previewRows.forEach(row => {
        const tr = document.createElement('tr');
        uploadHeaders.forEach((h, i) => {
            const td = document.createElement('td');
            td.style.padding = '4px 8px';
            td.style.border = '1px solid #cbd5e1';
            td.style.color = '#334155';

            if (columnMappings[i] === "ignorar" || columnMappings[i] === "") {
                td.style.color = '#cbd5e1';
                td.style.fontStyle = 'italic';
            }
            td.textContent = row[h] || '';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

function validateParsedData() {
    const cat = document.getElementById('uploadCategory').value;
    const rules = CATEGORY_RULES[cat];
    const alertBox = document.getElementById('uploadAlertBox');
    const btnSubmit = document.getElementById('btnFinalUpload');

    // Identify mapped headers
    let activeHeaders = columnMappings.filter(m => m !== "" && m !== "ignorar");
    const normHeaders = activeHeaders.map(h => h.toLowerCase().trim());

    let missing = [];
    let forbiddenFound = [];
    let recognizedCols = [];
    let unrecognizedCols = [];
    let ignoredColsCount = 0;

    uploadHeaders.forEach((h, i) => {
        if (!h.trim()) return;
        const mapped = columnMappings[i];
        if (mapped === "ignorar" || mapped === "") {
            unrecognizedCols.push(h);
            if (mapped === "ignorar") ignoredColsCount++;
        } else {
            recognizedCols.push(mapped);
        }
    });

    // Check expected (based on category rules)
    rules.expected.forEach(exp => {
        let found = false;
        for (let h of normHeaders) {
            if (h.includes(exp) || exp.includes(h) || (exp === 'telefono' && h.includes('celular')) || (exp === 'nombre' && h.includes('cliente'))) {
                found = true; break;
            }
        }
        if (!found) missing.push(exp);
    });

    // Check forbidden
    rules.forbidden.forEach(forb => {
        let found = false;
        for (let h of normHeaders) {
            if (h.includes(forb) || forb.includes(h)) {
                found = true; break;
            }
        }
        if (found) forbiddenFound.push(forb);
    });

    let msgs = [];

    // Database mapping count info
    const unmappedCount = unrecognizedCols.length - ignoredColsCount;

    if (unmappedCount > 0) {
        msgs.push(`Se detectaron <b>${uploadHeaders.length} columnas</b>. Base de datos recibirá ${recognizedCols.length}. <br><span style="color:#b45309;">⚠️ Tienes <b>${unmappedCount}</b> columna(s) sin mapear. Por favor ignóralas o mapealas usando los selectores en la tabla de abajo: <i>${unrecognizedCols.filter(x => !columnMappings.includes(x)).join(', ')}</i>.</span>`);
        alertBox.style.background = '#fffbeb'; // Yellowish warning
        alertBox.style.borderColor = '#fde68a';
    } else if (ignoredColsCount > 0) {
        msgs.push(`Se detectaron <b>${uploadHeaders.length} columnas</b>. Base de datos recibirá ${recognizedCols.length} mapeadas correctamente. Se ignorarán ${ignoredColsCount} columna(s).`);
        alertBox.style.background = '#f8fafc'; // Gray 
        alertBox.style.borderColor = '#cbd5e1';
    } else {
        msgs.push(`<span style="color:#15803d; font-weight:bold;">¡Excelente! Todas las ${uploadHeaders.length} columnas están mapeadas y listas para cargar.</span>`);
        alertBox.style.background = '#ecfdf5'; // Greenish success
        alertBox.style.borderColor = '#a7f3d0';
    }

    if (missing.length > 0) {
        msgs.push(`<b style="color:#b45309">Atención:</b> Tu categoría es <b>${cat}</b> y parece faltar: <i>${missing.join(', ')}</i>.`);
    }
    if (forbiddenFound.length > 0) {
        msgs.push(`<b style="color:#dc2626">Cuidado:</b> Tu categoría es <b>${cat}</b> pero incluiste columnas de: <i>${forbiddenFound.join(', ')}</i>.`);
        alertBox.style.background = '#fef2f2'; // Reddish danger
        alertBox.style.borderColor = '#fecaca';
    }

    if (msgs.length > 0) {
        alertBox.innerHTML = msgs.join('<br><br>');
        alertBox.style.display = 'block';
    } else {
        alertBox.style.display = 'none';
    }

    const isExisting = uploadMode === 'existing';
    const studyName = document.getElementById('uploadStudyName').value.trim();
    const existingStudyId = document.getElementById('uploadExistingStudySelect') ? document.getElementById('uploadExistingStudySelect').value : '';

    const hasTarget = isExisting ? !!existingStudyId : !!studyName;

    if (parsedUploadData.length > 0 && unmappedCount === 0 && hasTarget) {
        btnSubmit.disabled = false;
        btnSubmit.style.opacity = '1';
        document.getElementById('uploadError').style.display = 'none';
    } else {
        btnSubmit.disabled = true;
        btnSubmit.style.opacity = '0.5';
        if (unmappedCount > 0 && parsedUploadData.length > 0) {
            document.getElementById('uploadError').textContent = 'Debe mapear o ignorar todas las columnas pendientes.';
            document.getElementById('uploadError').style.display = 'inline';
        } else if (parsedUploadData.length > 0 && unmappedCount === 0 && !hasTarget) {
            document.getElementById('uploadError').textContent = isExisting
                ? 'Seleccione un estudio destino.'
                : 'Debe asignar un nombre al estudio.';
            document.getElementById('uploadError').style.display = 'inline';
        }
    }
}

// Ensure button state strictly listens to Study Name typing as well
document.getElementById('uploadStudyName').addEventListener('input', () => {
    if (parsedUploadData.length > 0) {
        validateParsedData();
    }
});

async function uploadParsedData() {
    const isExisting = uploadMode === 'existing';
    const studyName = document.getElementById('uploadStudyName').value.trim();
    const studyType = document.getElementById('uploadStudyType').value;
    const studyStage = document.getElementById('uploadStudyStage').value;
    const existingStudyId = document.getElementById('uploadExistingStudySelect') ? document.getElementById('uploadExistingStudySelect').value : '';

    if (isExisting) {
        if (!existingStudyId) {
            document.getElementById('uploadError').textContent = 'Seleccione un estudio destino.';
            document.getElementById('uploadError').style.display = 'inline';
            return;
        }
    } else {
        if (!studyName) {
            document.getElementById('uploadError').textContent = 'Debe asignar un nombre al estudio.';
            document.getElementById('uploadError').style.display = 'inline';
            return;
        }
    }
    document.getElementById('uploadError').style.display = 'none';

    if (parsedUploadData.length === 0) {
        alert("No hay datos para cargar.");
        return;
    }

    // Build mapped data
    const finalData = parsedUploadData.map(row => {
        let newRow = {};
        uploadHeaders.forEach((h, i) => {
            const mapped = columnMappings[i];
            if (mapped && mapped !== "ignorar") {
                newRow[mapped] = row[h];
            }
        });
        return newRow;
    });

    // Repack JSON to Excel Blob using SheetJS
    const ws = XLSX.utils.json_to_sheet(finalData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Base");

    // Write to array buffer
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([wbout], { type: "application/octet-stream" });

    const formData = new FormData();
    formData.append('file', blob, 'base_pegada.xlsx');
    if (isExisting) {
        formData.append('study_id', existingStudyId);
    } else {
        formData.append('study_name', studyName);
        formData.append('study_type', studyType);
        formData.append('study_stage', studyStage);
    }

    document.getElementById('btnFinalUpload').disabled = true;
    document.getElementById('btnFinalUpload').innerHTML = 'Cargando...';

    try {
        const res = await fetch('/upload-calls', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            const actionWord = (uploadMode === 'existing') ? 'anexados' : 'creados';
            alert(`Carga exitosa: ${data.count} registros ${actionWord} en el estudio '${data.study_name}'.`);
            closeUploadModal();
            enterCRM();
        } else {
            const err = await res.json();
            alert("Error: " + err.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Error de red");
    } finally {
        document.getElementById('btnFinalUpload').disabled = false;
        document.getElementById('btnFinalUpload').innerHTML = '<i class="fas fa-upload" style="margin-right: 5px;"></i> Cargar Datos';
    }
}

// --- STUDY MANAGEMENT (Active/Inactive) ---
async function showManageStudies() {
    document.getElementById('manageStudiesModal').style.display = 'flex';
    loadManageStudiesTable();
}

function closeManageStudies() {
    document.getElementById('manageStudiesModal').style.display = 'none';
}

async function loadManageStudiesTable() {
    const tbody = document.getElementById('manageStudiesBody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Cargando...</td></tr>';

    try {
        // Admin fetches all, including inactive
        const res = await fetch('/studies?include_inactive=true', { headers });
        if (res.ok) {
            const studies = await res.json();
            tbody.innerHTML = '';

            if (studies.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No hay bases de datos.</td></tr>';
                return;
            }

            studies.forEach(s => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #eee';

                const statusColor = s.is_active ? '#22c55e' : '#94a3b8';
                const statusText = s.is_active ? 'Activa' : 'Inactiva';

                tr.innerHTML = `
                    <td style="padding:0.5rem; color: #334155;">${s.id}</td>
                    <td style="padding:0.5rem; color: #334155;"><strong>${s.name}</strong><br><span style="font-size:0.8rem; color:#64748b;">${s.code}</span></td>
                    <td style="padding:0.5rem; color: #334155;">${s.study_type || '-'} <span style="font-size:0.8rem; color:#f59e0b;">[${s.stage || '-'}]</span></td>
                    <td style="padding:0.5rem;"><span style="color:white; background:${statusColor}; padding:2px 8px; border-radius:10px; font-size:0.8rem;">${statusText}</span></td>
                    <td style="padding:0.5rem; display:flex; gap:5px;">
                         <button onclick="toggleStudyStatus(${s.id})" style="cursor:pointer; background: ${s.is_active ? '#ef4444' : '#22c55e'}; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:0.75rem;">
                            ${s.is_active ? 'Desactivar' : 'Activar'}
                         </button>
                         <button onclick="duplicateStudyR2(${s.id}, '${s.name}')" style="cursor:pointer; background: #8b5cf6; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:0.75rem;" title="Crear Siguiente Etapa (R+)">
                            <i class="fas fa-copy"></i> Sig. Etapa (R+)
                         </button>
                         <button onclick="openAssignAux(${s.id}, '${s.name}')" style="cursor:pointer; background: #6366f1; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:0.75rem;">
                            <i class="fas fa-users-cog"></i> Asignar
                         </button>
                         <button onclick="deleteStudy(${s.id})" style="cursor:pointer; background: #991b1b; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:0.75rem;" title="Eliminar Permanentemente">
                            <i class="fas fa-trash"></i>
                         </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="5" style="color:red; text-align:center;">Error al cargar bases.</td></tr>';
    }
}

async function toggleStudyStatus(id) {
    if (!confirm("¿Cambiar estado de la base de datos? Esto afectará su visibilidad para los agentes.")) return;

    try {
        const res = await fetch(`/studies/${id}/toggle`, {
            method: 'PUT',
            headers
        });

        if (res.ok) {
            loadManageStudiesTable(); // Refresh table
            loadStudies(); // Refresh dropdown in background
        } else {
            alert("Error al cambiar estado");
        }
    } catch (e) { console.error(e); }
}

async function deleteStudy(id) {
    if (!confirm("ADVERTENCIA: ¿Estás seguro de que deseas ELIMINAR PERMANENTEMENTE este estudio y TODAS sus llamadas? Esta acción no se puede deshacer.")) return;

    // Double confirmation for safety
    if (!confirm("Confirmación final: Se borrarán todos los datos asociados. ¿Proceder?")) return;

    try {
        const res = await fetch(`/studies/${id}`, {
            method: 'DELETE',
            headers
        });

        if (res.ok) {
            alert("Estudio eliminado correctamente.");
            loadManageStudiesTable(); // Refresh table
            loadStudies(); // Refresh dropdown
        } else {
            alert("Error al eliminar el estudio.");
        }
    } catch (e) { console.error(e); }
}

async function duplicateStudyR2(id, currentName) {
    if (!confirm(`¿Generar siguiente visita (R+) para "${currentName}"?\nSe duplicarán SOLO las llamadas EFECTIVAS.`)) return;

    try {
        const res = await fetch(`/studies/${id}/duplicate-r2`, {
            method: 'POST',
            headers
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Estudio duplicado exitosamente: ${data.new_study_name}\n${data.count} registros copiados.`);
            loadManageStudiesTable();
            loadStudies();
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "Error al duplicar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}

let currentDuplicateExcelData = null;

function showDuplicateValidatorModal() {
    document.getElementById('duplicateValidatorModal').style.display = 'flex';
    document.getElementById('duplicatePasteArea').value = '';
    document.getElementById('duplicateResults').style.display = 'none';
    const btn = document.getElementById('btnDownloadDuplicateExcel');
    if(btn) btn.style.display = 'none';
}

function closeDuplicateValidatorModal() {
    document.getElementById('duplicateValidatorModal').style.display = 'none';
    currentDuplicateExcelData = null;
}

async function runDuplicateValidation() {
    const text = document.getElementById('duplicatePasteArea').value.trim();
    if (!text) {
        alert("Por favor, pega algunos datos primero.");
        return;
    }

    const rows = text.split('\n').map(row => row.split('\t'));
    const items = rows.map(row => {
        let name = null;
        let number = null;
        if (row.length >= 2) {
            name = row[0].trim();
            number = row[1].trim();
        } else {
            number = row[0].trim();
        }
        return { name, number };
    }).filter(item => item.number);

    if (items.length === 0) {
        alert("No se detectaron números válidos.");
        return;
    }

    try {
        const res = await fetch('/calls/check-duplicates', {
            method: 'POST',
            headers,
            body: JSON.stringify({ items })
        });

        if (res.ok) {
            const data = await res.json();
            renderDuplicateResults(data);
        } else {
            const err = await res.json();
            alert("Error al validar: " + err.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}

function renderDuplicateResults(data) {
    const resultsDiv = document.getElementById('duplicateResults');
    const summaryDiv = document.getElementById('duplicateSummary');
    const dupsList = document.getElementById('duplicatesList');
    const lengthList = document.getElementById('invalidLengthList');
    const btnDownload = document.getElementById('btnDownloadDuplicateExcel');

    resultsDiv.style.display = 'block';
    
    currentDuplicateExcelData = data.excel_data;
    if (currentDuplicateExcelData && currentDuplicateExcelData.length > 0 && btnDownload) {
        btnDownload.style.display = 'block';
    } else if (btnDownload) {
        btnDownload.style.display = 'none';
    }

    const { total_input, duplicate_count, invalid_length_count } = data.summary;
    summaryDiv.style.background = (duplicate_count > 0 || invalid_length_count > 0) ? '#fffbeb' : '#ecfdf5';
    summaryDiv.style.border = (duplicate_count > 0 || invalid_length_count > 0) ? '1px solid #fde68a' : '1px solid #a7f3d0';
    summaryDiv.innerHTML = `
        <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 5px;">Resultado de Validación</div>
        <div>Total revisados: <b>${total_input}</b></div>
        <div style="color: #ef4444;">Duplicados encontrados: <b>${duplicate_count}</b></div>
        <div style="color: #f59e0b;">Errores de formato (10 dígitos): <b>${invalid_length_count}</b></div>
    `;

    if (data.duplicates.length === 0) {
        dupsList.innerHTML = '<div style="opacity: 0.5; font-style: italic; margin-top: 10px;">No se encontraron duplicados.</div>';
    } else {
        dupsList.innerHTML = data.duplicates.map(d => `
            <div style="margin-top: 10px; padding: 8px; background: #fef2f2; border-radius: 4px; border-left: 3px solid #ef4444;">
                <b>${d.input_name || 'Sin nombre'}</b> (${d.input_number})<br>
                <span style="font-size: 0.8rem; color: #64748b;">
                    Encontrado en: <b>${d.study_name}</b><br>
                    Creado el: ${d.created_at}
                </span>
            </div>
        `).join('');
    }

    if (data.invalid_length.length === 0) {
        lengthList.innerHTML = '<div style="opacity: 0.5; font-style: italic; margin-top: 10px;">Todos los números tienen 10 dígitos.</div>';
    } else {
        lengthList.innerHTML = data.invalid_length.map(i => `
            <div style="margin-top: 10px; padding: 8px; background: #fffbeb; border-radius: 4px; border-left: 3px solid #f59e0b;">
                <b>${i.input_name || 'Sin nombre'}</b> (${i.input_number})<br>
                <span style="font-size: 0.8rem; color: #b45309;">
                    Tiene ${i.length} dígitos (se esperaban 10)
                </span>
            </div>
        `).join('');
    }
}

function downloadDuplicateExcel() {
    if (!currentDuplicateExcelData || currentDuplicateExcelData.length === 0) {
        alert("No hay datos para descargar");
        return;
    }
    
    // Check if XLSX is available (SheetJS)
    if (typeof XLSX === 'undefined') {
        alert("La librería para exportar a Excel no está cargada en esta página.");
        return;
    }

    try {
        const worksheet = XLSX.utils.json_to_sheet(currentDuplicateExcelData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Resultados");
        XLSX.writeFile(workbook, "Resultados_Validacion_Duplicados.xlsx");
    } catch (e) {
        console.error("Error al exportar a Excel:", e);
        alert("Hubo un error al generar el archivo Excel.");
    }
}

async function loadStudies(showClosed = false) {
    const sel = document.getElementById('studySelect');
    if (!sel) return;

    // Destroy existing TomSelect instance if it exists
    if (studySelectTS) {
        studySelectTS.destroy();
        studySelectTS = null;
    }

    // SIMPLIFIED LOGIC: Always fetch all studies, filter in frontend
    let url = '/studies';
    try {
        const res = await fetch(url, { headers });
        if (!res.ok) throw new Error('Failed to fetch studies');
        let studies = await res.json();

        if (showClosed) {
            // Filter for inactive (false, 0, null)
            studies = studies.filter(s => s.is_active === false || s.is_active === 0 || s.is_active === null);
        } else {
            // Filter for ACTIVE (true)
            studies = studies.filter(s => s.is_active === true || s.is_active === 1);
        }

        // Change default option text based on mode
        const defaultText = showClosed ? 'Todos (Estudios Cerrados)...' : 'Seleccione Estudio...';
        sel.innerHTML = `<option value="">${defaultText}</option>`;

        studies.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.code} - ${s.name}`;
            if (showClosed) {
                opt.style.color = 'red'; // Visual cue
            }
            sel.appendChild(opt);
        });

        // Initialize TomSelect
        studySelectTS = new TomSelect(sel, {
            create: false,
            placeholder: defaultText,
            maxOptions: 1000,
            onChange: (value) => {
                // Allow loading null (global) if value is empty
                loadStudyData(value || null);
            }
        });

        // Prevent auto-loading all closed studies by default to save memory
        // User must explicitly search and select a study from the TomSelect dropdown
        if (showClosed) {
            studySelectTS.setValue("", true); // Select "Todos" silently without triggering onChange
        }

    } catch (e) {
        console.error("Error loading studies", e);
        sel.innerHTML = `<option value="">Error cargando estudios</option>`;
    }
}

// Add Enter key listener for column search
// Add Enter key listener for column search
// Add Enter key listener for column search
['colFilterPhone', 'colFilterName', 'colFilterCensus'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') applyColumnFilters();
        });
    }
});

// Sort State
let currentSort = { column: null, direction: 'asc' }; // 'asc' means oldest first (9am then 2pm)

function toggleSort(column) {
    if (currentSort.column === column) {
        // Toggle direction
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    // Re-render (sorting happens in render or before render? Better to sort the filtered list)
    applyColumnFilters();
}


['colFilterDateStart', 'colFilterDateEnd', 'colFilterRealizationStart', 'colFilterRealizationEnd'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('change', function () {
            applyColumnFilters();
        });
    }
});

function applyColumnFilters() {
    const phoneTerm = document.getElementById('colFilterPhone').value.toLowerCase().trim();
    const nameTerm = document.getElementById('colFilterName').value.toLowerCase().trim();
    // const cityTerm = document.getElementById('colFilterCity').value.toLowerCase().trim(); // Removed single select
    const censusTerm = document.getElementById('colFilterCensus') ? document.getElementById('colFilterCensus').value.toLowerCase().trim() : '';
    const dateStart = document.getElementById('colFilterDateStart') ? document.getElementById('colFilterDateStart').value : '';
    const dateEnd = document.getElementById('colFilterDateEnd') ? document.getElementById('colFilterDateEnd').value : '';
    const realStart = document.getElementById('colFilterRealizationStart') ? document.getElementById('colFilterRealizationStart').value : '';
    const realEnd = document.getElementById('colFilterRealizationEnd') ? document.getElementById('colFilterRealizationEnd').value : '';

    // New Filters
    // const studyTerm = document.getElementById('colFilterStudy').value.toLowerCase().trim(); // Removed single select
    // Agents & Status are now multi-selects handled by checking checkboxes in their containers

    // Helper to get checked values from a container
    const getMultiSelectValues = (containerId) => {
        const container = document.getElementById(containerId);
        if (!container) return [];
        return Array.from(container.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value.toLowerCase());
    };

    const selectedAgents = getMultiSelectValues('colFilterAgentContainer');
    const selectedStatuses = getMultiSelectValues('colFilterStatusContainer');
    const selectedPrevAgents = getMultiSelectValues('colFilterPreviousAgentContainer');
    const selectedCities = getMultiSelectValues('colFilterCityContainer'); // New Multi-Select
    const selectedStudies = getMultiSelectValues('colFilterStudyContainer'); // New Multi-Select
    const selectedShampoos = getMultiSelectValues('colFilterShampooContainer'); // New Multi-Select

    // Helper Checks
    const checkPhone = (c) => !phoneTerm || (
        (c.phone_number || '').toString().toLowerCase().includes(phoneTerm) ||
        (c.whatsapp || '').toString().toLowerCase().includes(phoneTerm) ||
        (c.corrected_phone || '').toString().toLowerCase().includes(phoneTerm)
    );
    const checkName = (c) => !nameTerm || (c.person_name || '').toString().toLowerCase().includes(nameTerm);
    const checkCensus = (c) => !censusTerm || (c.census || '').toString().toLowerCase().includes(censusTerm);

    const checkCity = (c) => {
        if (selectedCities.length === 0) return true;
        const val = (c.city || '').trim().toLowerCase();
        // Compare with lowercase selected values
        return selectedCities.includes(val);
    };

    const checkDate = (c) => {
        if (!dateStart && !dateEnd) return true;

        let dateStr = '';

        // Normalize whatever date field is present
        // Grid uses: c.collection_date || c.created_at
        const rawDate = c.collection_date || c.created_at;

        if (!rawDate) return false;

        const dateString = rawDate.toString().trim();

        // Normalize to YYYY-MM-DD using Regex to avoid Timezone shifts

        // 1. ISO-like YYYY-MM-DD
        // Matches "2026-01-23" or "2026-01-23T..." or "2026-01-23 00:00:00"
        if (dateString.match(/^\d{4}-\d{2}-\d{2}/)) {
            dateStr = dateString.substring(0, 10);
        }
        // 2. DD/MM/YYYY
        else if (dateString.match(/^\d{1,2}\/\d{1,2}\/\d{4}/)) {
            const parts = dateString.split('/');
            // parts[0] = DD, parts[1] = MM, parts[2] = YYYY
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }
        // 3. DD-MM-YYYY
        else if (dateString.match(/^\d{1,2}-\d{1,2}-\d{4}/)) {
            const parts = dateString.split('-');
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }

        if (!dateStr || dateStr.length !== 10) return false;

        if (dateStart && dateStr < dateStart) return false;
        if (dateEnd && dateStr > dateEnd) return false;

        return true;
    };

    const checkRealizationDate = (c) => {
        if (!realStart && !realEnd) return true;
        const rawDate = c.realization_date;
        if (!rawDate) return false;

        let dateStr = '';
        const dateString = rawDate.toString().trim();
        // 1. ISO-like YYYY-MM-DD
        if (dateString.match(/^\d{4}-\d{2}-\d{2}/)) {
            dateStr = dateString.substring(0, 10);
        }
        // 2. DD/MM/YYYY
        else if (dateString.match(/^\d{1,2}\/\d{1,2}\/\d{4}/)) {
            const parts = dateString.split('/');
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }
        // 3. DD-MM-YYYY
        else if (dateString.match(/^\d{1,2}-\d{1,2}-\d{4}/)) {
            const parts = dateString.split('-');
            dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
        }

        if (!dateStr) return false;

        if (realStart && dateStr < realStart) return false;
        if (realEnd && dateStr > realEnd) return false;

        return true;
    };

    // Selects
    const checkStudy = (c) => {
        if (selectedStudies.length === 0) return true;
        const val = (c.study_name || '').toString().toLowerCase().trim();
        return selectedStudies.includes(val);
    };

    const checkShampoo = (c) => {
        if (selectedShampoos.length === 0) return true;
        const val = (c.shampoo_quantity || '').toString().toLowerCase().trim();
        return selectedShampoos.includes(val);
    };

    const checkAgent = (c) => {
        if (selectedAgents.length === 0) return true; // If none checked, it implies ALL or nothing filtered? "Todos" logic. 
        // Based on UI, usually unchecked means "All" in this context? 
        // Wait, my updateButtonText says "Todos" if ALL checked or NONE checked.
        // Let's assume if NONE checked, we show ALL.

        const agentDisplay = c.agent_name || (c.agent_id ? `Agente ${c.agent_id}` : 'Sin Asignar');
        const val = agentDisplay.toLowerCase().trim();

        return selectedAgents.includes(val);
    };

    const checkPrevAgent = (c) => {
        if (selectedPrevAgents.length === 0) return true;
        const prevAgentDisplay = c.previous_agent_name || '-';
        const val = prevAgentDisplay.toLowerCase().trim();
        return selectedPrevAgents.includes(val);
    };

    const checkStatus = (c) => {
        if (selectedStatuses.length === 0) return true; // Show all if none selected

        const s = (c.status || 'pending').toLowerCase().trim();
        const translated = translateStatus(c.status || 'pending').toLowerCase().trim();

        // Check if ANY of the selected statuses matches this call
        // The values in selectedStatuses come from the options we populated.
        // Since we populate with both raw? No, populate usually does display text?
        // Let's see how we populate. We should populate with consistent values.

        // We will populate with Display Values (Translated). So we should compare translated.
        return selectedStatuses.includes(translated) || selectedStatuses.includes(s);
    };


    // 1. Filter Grid (Intersection of ALL)
    filteredCalls = allCalls.filter(c =>
        checkPhone(c) && checkName(c) && checkCity(c) && checkCensus(c) &&
        checkStudy(c) && checkAgent(c) && checkPrevAgent(c) && checkStatus(c) && checkDate(c) && checkRealizationDate(c) && checkShampoo(c)
    );

    // 2. Sort Logic
    if (currentSort.column) {
        filteredCalls.sort((a, b) => {
            let valA = a[currentSort.column];
            let valB = b[currentSort.column];

            // Handle Nulls: always last regardless of direction? 
            // User request: "9 am, 2 pm and then unassigned" -> Values first (Asc), Unassigned last.
            // If direction Desc: Unassigned last? Or first? Usually unassigned last is preferred.

            if (!valA && valB) return 1; // A is null, put at end
            if (valA && !valB) return -1; // B is null, A comes first
            if (!valA && !valB) return 0;

            if (currentSort.column === 'appointment_time' || currentSort.column === 'second_collection_date') {
                // Date comparison
                valA = valA ? new Date(valA) : null;
                valB = valB ? new Date(valB) : null;
            } else if (currentSort.column === 'shampoo_quantity') {
                // Numeric comparison if possible, else string
                const numA = parseFloat(valA);
                const numB = parseFloat(valB);
                if (!isNaN(numA) && !isNaN(numB)) {
                    valA = numA;
                    valB = numB;
                }
            }

            if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
            if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
            return 0;
        });
    }

    renderCallGrid(filteredCalls);





}

function resetFilters() {
    ['colFilterPhone', 'colFilterName', 'colFilterCensus', 'colFilterDateStart', 'colFilterDateEnd', 'colFilterRealizationStart', 'colFilterRealizationEnd'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reset Multi-Selects
    ['colFilterAgentContainer', 'colFilterStatusContainer', 'colFilterPreviousAgentContainer', 'colFilterCityContainer', 'colFilterStudyContainer', 'colFilterShampooContainer'].forEach(id => {
        const c = document.getElementById(id);
        if (c) {
            c.querySelectorAll('input').forEach(chk => chk.checked = false);
            const btn = c.querySelector('.multiselect-btn');
            if (btn) btn.textContent = 'Todos';
        }
    });

    applyColumnFilters();
}


// MULTI-SELECT HELPER
function createMultiSelect(containerId, options, onChangeCallback) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = ''; // Clear

    // 1. Button
    const btn = document.createElement('button');
    btn.className = 'multiselect-btn';
    btn.textContent = 'Todos';
    btn.onclick = (e) => {
        e.stopPropagation();
        // Toggle visibility
        const content = container.querySelector('.multiselect-content');
        if (content) {
            // Close others
            document.querySelectorAll('.multiselect-content').forEach(el => {
                if (el !== content) el.classList.remove('show');
            });
            content.classList.toggle('show');
        }
    };
    container.appendChild(btn);

    // 2. Content Div
    const content = document.createElement('div');
    content.className = 'multiselect-content';
    container.appendChild(content);

    // 3. Options
    // Add "Select All" / "All" logic implicity or explicitly?
    // Let's have a "Todos" option or just start with all unchecked = All?
    // User wants "escoger uno o varios".
    // Let's add explicit "Deselect All" / "Select All" at top?
    // For simplicity: List all options with checkboxes. If none checked, or "Todos" checked, it means all.

    // Let's add a "Todos" checkbox at top
    // const allLabel = document.createElement('label');
    // allLabel.innerHTML = `<input type="checkbox" value="ALL" checked> <b>Todos</b>`;
    // content.appendChild(allLabel);

    options.forEach(optVal => {
        const label = document.createElement('label');
        // If we want to support value/label pairs, options could be objects. 
        // For now options are strings.
        const val = optVal;
        const txt = optVal; // Or translate status?

        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.value = val;
        // chk.checked = true; // Default all checked? Or none? 
        // Usually filters start with "All" (none checked effectively or special logic)

        chk.onchange = () => {
            updateButtonText();
            onChangeCallback();
        }

        label.appendChild(chk);
        label.appendChild(document.createTextNode(' ' + txt));
        content.appendChild(label);
    });

    // Helper to update button text
    function updateButtonText() {
        const checked = Array.from(content.querySelectorAll('input[type="checkbox"]:checked'));
        if (checked.length === 0 || checked.length === options.length) {
            btn.textContent = 'Todos';
        } else {
            if (checked.length <= 2) {
                btn.textContent = checked.map(c => c.parentElement.textContent.trim()).join(', ');
            } else {
                btn.textContent = `${checked.length} seleccionados`;
            }
        }
    }
}

// Global listener for closing multi-selects
window.addEventListener('click', (e) => {
    if (!e.target.matches('.multiselect-btn') && !e.target.closest('.multiselect-content')) {
        document.querySelectorAll('.multiselect-content').forEach(el => el.classList.remove('show'));
    }
    // Existing popup logic
    if (!e.target.closest('#filterPopup')) {
        const fp = document.getElementById('filterPopup');
        if (fp) fp.style.display = 'none';
    }
});

function populateSelectFilter(elementId, values) {
    const sel = document.getElementById(elementId);
    if (!sel) return;

    // Save current selection
    const current = sel.value;

    // Clear (keep first option 'Todos')
    sel.innerHTML = '<option value="">Todos</option>';

    const unique = [...new Set(values)].sort();

    unique.forEach(val => {
        const opt = document.createElement('option');
        opt.value = val;
        opt.textContent = val;
        sel.appendChild(opt);
    });

    if (unique.includes(current)) {
        sel.value = current;
    }
}

function searchCalls() {
    const term = document.getElementById('searchPhone').value.toLowerCase().trim();
    // Dates removed as requested
    const status = document.getElementById('filterStatus').value;

    filteredCalls = allCalls.filter(c => {
        const phone = (c.phone_number || '').toString().toLowerCase();
        const name = (c.person_name || '').toString().toLowerCase();
        const city = (c.city || '').toString().toLowerCase();
        const census = (c.census || '').toString().toLowerCase();
        const callStatus = c.status || 'pending';

        // Date Logic Removed

        let matchStatus = true;
        if (status && status !== '') {
            matchStatus = (callStatus === status);
        }

        const matchTerm = !term || (phone.includes(term) || name.includes(term) || city.includes(term) || census.includes(term));

        return matchTerm && matchStatus;
    });

    renderCallGrid(filteredCalls);
}

// VIEW SWITCHING
function showGridView() {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('callsGridView').style.display = 'block';
    document.getElementById('callDetailView').style.display = 'none';

    // Restore sidebar only for superusers/coordinators/auxiliars
    if (currentUserRole === 'superuser' || currentUserRole === 'coordinator' || currentUserRole === 'auxiliar') {
        document.querySelector('.sidebar').style.display = 'flex';
        document.getElementById('crmInterface').style.gridTemplateColumns = '300px 1fr';
    } else {
        document.querySelector('.sidebar').style.display = 'none';
        document.getElementById('crmInterface').style.gridTemplateColumns = '1fr';
    }
}

function closeDetailView() {
    showGridView();
}

function showDetailView() {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('callsGridView').style.display = 'none';
    document.getElementById('callDetailView').style.display = 'block';

    // Hide sidebar always in detail view
    document.querySelector('.sidebar').style.display = 'none';
    document.getElementById('crmInterface').style.gridTemplateColumns = '1fr';
}

// Filter State
let allCalls = []; // Store all fetched calls
let filteredCalls = [];
let activeFilters = {}; // { key: Set(values) }
let currentFilterColumn = null;

async function loadStudyData(studyId) {
    // Fetch calls
    try {
        let url = '/calls';
        const params = new URLSearchParams();
        if (studyId) {
            params.append('study_id', studyId);
        } else {
            // Global Load: Check if we are in Closed View
            // Use local variable isClosedView (not window property)
            if (isClosedView) {
                params.append('study_is_active', 'false');
            } else {
                params.append('study_is_active', 'true');
            }
        }

        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;

        const res = await fetch(url, { headers });
        const calls = await res.json();

        // Enhance calls with 'observation_text' for easier filtering
        // Assuming observation is simple text or latest one. 
        // If API returns array, we take latest. If string (legacy), use it.
        // Also map 'census' if needed.
        allCalls = calls.map(c => {
            // Flatten observations for table display if needed, or just use initial/latest
            // For now, let's assume 'initial_observation' or we add a field in backend response
            // If backend doesn't send 'census', it will be undefined.
            return {
                ...c,
                // Prioritize collection_time (for the "swapped" data case) or initial_observation
                observation_text: c.collection_time || c.initial_observation || (c.observations && c.observations.length > 0 ? c.observations[0].text : '') || '-'
            };
        });

        // Populate City Dropdown (Dynamic Multi-Select)
        const possibleCities = allCalls.map(c => (c.city || '').trim());
        const uniqueCities = [...new Set(possibleCities)].filter(x => x).sort();
        createMultiSelect('colFilterCityContainer', uniqueCities, applyColumnFilters);

        // Populate Study Dropdown (Dynamic Multi-Select)
        const possibleStudies = allCalls.map(c => (c.study_name || '').trim());
        const uniqueStudies = [...new Set(possibleStudies)].filter(x => x).sort();
        createMultiSelect('colFilterStudyContainer', uniqueStudies, applyColumnFilters);

        // Populate Status Dropdown (Dynamic Multi-Select)
        const uniqueStatuses = [...new Set(allCalls.map(c => translateStatus(c.status || 'pending').trim()))].sort();
        createMultiSelect('colFilterStatusContainer', uniqueStatuses, applyColumnFilters);

        // Populate Agent Dropdown (Dynamic Multi-Select)
        const possibleAgents = allCalls.map(c => c.agent_name || (c.agent_id ? `Agente ${c.agent_id}` : 'Sin Asignar'));
        // Add current user if agent? No, list all agents in data.
        const uniqueAgents = [...new Set(possibleAgents)].filter(x => x).sort();

        createMultiSelect('colFilterAgentContainer', uniqueAgents, applyColumnFilters);

        // Populate Previous Agent Dropdown (Dynamic Multi-Select)
        const possiblePrevAgents = allCalls.map(c => c.previous_agent_name || '-');
        const uniquePrevAgents = [...new Set(possiblePrevAgents)].sort();
        createMultiSelect('colFilterPreviousAgentContainer', uniquePrevAgents, applyColumnFilters);

        // Populate Shampoo Dropdown (Dynamic Multi-Select)
        const possibleShampoos = allCalls.map(c => (c.shampoo_quantity || '').trim());
        const uniqueShampoos = [...new Set(possibleShampoos)].filter(x => x).sort();
        createMultiSelect('colFilterShampooContainer', uniqueShampoos, applyColumnFilters);


        // Helper to restore selections? 
        // For now, simple re-population clears selection. 
        // If improvement needed, make populateSelectFilter smarter.


        applyColumnFilters(); // Apply new column filters

        // showGridView will calculate layout based on role
        showGridView();
    } catch (e) { console.error(e); }
}

function renderCallGrid(calls) {
    // Update Counter
    const counter = document.getElementById('callCounter');
    if (counter) {
        counter.textContent = `(${calls.length} registros)`;
    }



    const tbody = document.getElementById('callsGridBody');
    tbody.innerHTML = '';

    if (calls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;">No hay llamadas (Filtros aplicados)</td></tr>';
        return;
    }


    // Color Palette for Studies (Blue, Green, Purple, etc.)
    const studyColors = [
        'rgba(219, 234, 254, 0.4)', // Blue
        'rgba(220, 252, 231, 0.4)', // Green
        'rgba(243, 232, 255, 0.4)', // Purple
        'rgba(254, 243, 199, 0.4)', // Amber
        'rgba(255, 228, 230, 0.4)', // Rose
        'rgba(224, 242, 254, 0.4)'  // Light Blue
    ];

    calls.forEach(call => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.style.borderBottom = '1px solid #dae1e7'; // Slightly darker border for contrast

        // DETERMINE ROW COLOR BASED ON STUDY ID
        // unique color per study using modulus
        const colorIndex = (call.study_id || 0) % studyColors.length;
        const rowColor = studyColors[colorIndex];

        tr.style.background = rowColor;

        // Hover Effect using JS (since we use inline styles for base color)
        tr.onmouseover = () => {
            // Darken slightly by overlaying a semi-transparent black
            tr.style.background = `linear-gradient(rgba(0,0,0,0.05), rgba(0,0,0,0.05)), ${rowColor}`;
        };
        tr.onmouseout = () => {
            tr.style.background = rowColor;
        };

        // Format appointment time if exists
        let alertTime = '-';
        if (call.appointment_time) {
            const dateObj = new Date(call.appointment_time);
            alertTime = `<span style="color:#d97706; font-weight:bold;">${dateObj.toLocaleDateString()} ${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
        }

        tr.innerHTML = `
            <td onclick="event.stopPropagation()"><input type="checkbox" class="call-checkbox" value="${call.id}"></td>
            <td>
                <i class="fas fa-phone"></i> ${call.phone_number}
                ${(call.corrected_phone && call.corrected_phone !== call.phone_number)
                ? `<br><span style="color:#059669; font-size:0.75rem; font-weight:bold;">➡ ${call.corrected_phone}</span>`
                : ''}
            </td>
            <td style="font-size: 0.8rem; color: #555;">${call.collection_date || '-'}</td>
            
            <!-- NEW COLUMN: Realization Date (Correct Position) -->
            <td style="font-size: 0.8rem;">${call.realization_date ? new Date(call.realization_date).toLocaleString() : '-'}</td>

            <!-- NEW COLUMN: Second Collection Date -->
            <td style="font-size: 0.8rem;">${call.second_collection_date || '-'}</td>

            <td>
                <span style="font-size:0.8rem; color:#666; font-weight:bold;">${call.study_name || '-'}</span>
                ${call.study_type ? `<br><span style="font-size:0.7rem; color:#1a73e8; font-weight:600;">${call.study_type.toUpperCase()}</span>` : ''}
                ${call.study_stage ? `<span style="font-size:0.7rem; color:#f59e0b; font-weight:600; margin-left:0.3rem;">[${call.study_stage}]</span>` : ''}
            </td>
            <td><span style="font-size:0.8rem; color:${call.agent_name ? '#4caf50' : '#f44336'}; font-weight:bold;">${call.agent_name || 'Sin Asignar'}</span></td>
            <td><span style="font-size:0.8rem; color:#888;">${call.previous_agent_name || '-'}</span></td>
            <td>${call.person_name || '-'}</td>
            <td>${call.city || '-'}</td>
            <td>${alertTime}</td>
            <!-- Old Obs Cell Removed -->
            
            <td><span style="background:${call.status === 'pending' ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.6)'}; border: 1px solid rgba(0,0,0,0.1); padding:2px 6px; border-radius:4px; font-size:0.8rem;">${translateStatus(call.status)}</span></td>
            
            <td>${call.census || '-'}</td>
            
            <!-- Dog Columns Removed -->
            <!-- <td>${call.dog_breed || '-'}</td> -->
            <!-- <td>${call.dog_size || '-'}</td> -->

            <td>${call.collection_time || call.initial_observation || '-'}</td> <!-- This serves as Hora Original now -->
            
            <!-- New Requested Columns -->
            <td>${call.shampoo_quantity || '-'}</td>
            <!-- Removed Columns: Purchase Freq, Pollster, Supervisor, Implantation Date -->
            <!-- <td>${call.purchase_frequency || '-'}</td> -->
            <!-- <td>${call.implantation_pollster || '-'}</td> -->
            <!-- <td>${call.supervisor || '-'}</td> -->
            <!-- <td>${call.implantation_date || '-'}</td> -->
            
            <!-- Temp Armando -->
            <td class="col-temp-armando" style="display: ${currentUserRole === 'superuser' ? 'table-cell' : 'none'};">
                ${currentUserRole === 'superuser'
                ? `<input type="text" value="${call.temp_armando || ''}" onclick="event.stopPropagation()" onchange="updateTempInfo(${call.id}, 'temp_armando', this.value)" style="width:100%; border:1px solid #ddd; background:rgba(255,255,255,0.7);">`
                : ''}
            </td>
            
            <!-- Temp Auxiliar -->
            <td class="col-temp-auxiliar" style="display: ${currentUserRole === 'superuser' || currentUserRole === 'auxiliar' ? 'table-cell' : 'none'};">
                ${(currentUserRole === 'superuser' || currentUserRole === 'auxiliar')
                ? `<input type="text" value="${call.temp_auxiliar || ''}" onclick="event.stopPropagation()" onchange="updateTempInfo(${call.id}, 'temp_auxiliar', this.value)" style="width:100%; border:1px solid #ddd; background:rgba(255,255,255,0.7);">`
                : ''}
            </td>
 
            <td style="font-size:0.75rem; color:#334155;">
                ${(call.last_observations && call.last_observations.length > 0)
                ? call.last_observations.join('<br>')
                : '-'}
            </td>
        `;

        // Store call data for the inline onclick handler to work simply
        tr.callData = call;

        tr.onclick = (e) => {
            // Prevent opening if clicking checkbox or buttons
            if (e.target.type !== 'checkbox' && !e.target.closest('button')) openCallDetail(call);
        };
        tbody.appendChild(tr);
    });
}

// FILTER LOGIC
function openFilter(column, event) {
    event.stopPropagation();
    currentFilterColumn = column;

    // Get unique values
    const uniqueValues = new Set(allCalls.map(c => c[column] || '-'));
    const sortedValues = Array.from(uniqueValues).sort();

    const container = document.getElementById('filterOptions');
    container.innerHTML = '';

    // Check if already filtered
    const currentSelection = activeFilters[column] || uniqueValues; // If not filtered, all selected

    // Add "Select All"
    const divAll = document.createElement('div');
    divAll.innerHTML = `<label><input type="checkbox" id="filterSelectAll" checked> (Seleccionar Todo)</label>`;
    container.appendChild(divAll);
    divAll.querySelector('input').onclick = (e) => {
        const boxes = container.querySelectorAll('.filter-val');
        boxes.forEach(b => b.checked = e.target.checked);
    };

    sortedValues.forEach(val => {
        const div = document.createElement('div');
        const isChecked = activeFilters[column] ? activeFilters[column].has(val) : true;
        div.innerHTML = `<label><input type="checkbox" class="filter-val" value="${val}" ${isChecked ? 'checked' : ''}> ${val}</label>`;
        container.appendChild(div);
    });

    // Position Popup
    const popup = document.getElementById('filterPopup');
    popup.style.display = 'block';
    popup.style.top = event.clientY + 'px';
    popup.style.left = event.clientX + 'px';

    // Search Listener
    document.getElementById('filterSearch').value = '';
    document.getElementById('filterSearch').onkeyup = (e) => {
        const term = e.target.value.toLowerCase();
        const labels = container.querySelectorAll('label');
        labels.forEach(l => {
            if (l.innerText.toLowerCase().includes(term) || l.querySelector('#filterSelectAll')) {
                l.style.display = 'block';
            } else {
                l.style.display = 'none';
            }
        });
    };
}

// Global listener
// Global listener merged above
// window.addEventListener('click', (e) => {
//     // Prevent closing if clicking inside the popup
//     if (e.target.closest('#filterPopup')) return;
//     closeFilter();
// });

function applyFilter() {
    if (currentFilterColumn) {
        const container = document.getElementById('filterOptions');
        const checked = Array.from(container.querySelectorAll('.filter-val:checked')).map(c => c.value);

        // If all checked (or none unchecked), maybe remove filter? 
        // For simplicity, just set activeFilters
        if (checked.length > 0) {
            activeFilters[currentFilterColumn] = new Set(checked);
        } else {
            // If nothing selected, show nothing? Or clear filter? Usually show nothing.
            activeFilters[currentFilterColumn] = new Set([]);
        }
        closeFilter();
    }

    // Apply Logic
    filteredCalls = allCalls.filter(call => {
        return Object.keys(activeFilters).every(key => {
            const val = call[key] || '-';
            return activeFilters[key].has(val.toString()); // Ensure string comparison
        });
    });

    renderCallGrid(filteredCalls);
}

function closeFilter() {
    document.getElementById('filterPopup').style.display = 'none';
    currentFilterColumn = null;
}
// ...
// Scroll lower for other functions


function openCallDetail(call) {
    currentCallId = call.id;
    renderObservationShortcuts();

    const cleanFloatStr = (val) => {
        if (!val) return '';
        let s = val.toString().trim();
        if (s.endsWith('.0')) return s.slice(0, -2);
        return s;
    };

    // Standard Info
    document.getElementById('phoneNumber').value = cleanFloatStr(call.phone_number);
    document.getElementById('correctedPhone').value = cleanFloatStr(call.corrected_phone);

    // UPDATE TITLE
    const titleEl = document.getElementById('callDetailTitle');
    if (titleEl) {
        // Requested: Study Name - Type/Stage of R. "Nombre del Estudio - R(Stage)"
        titleEl.textContent = `${call.study_name || 'Sin Estudio'} - ${call.study_stage || ''}`;
    }
    document.getElementById('personCC').value = call.person_cc || '';

    // New Fields
    document.getElementById('personName').value = call.person_name || '';
    document.getElementById('personCity').value = call.city || '';
    document.getElementById('personBrand').value = call.product_brand || '';
    // Apply same swap logic: show collection_time if available as it likely holds the time
    document.getElementById('initialObs').value = call.collection_time || call.initial_observation || '';
    
    // Appointment Time - Parsing for the new split fields
    const scheduleDateEl = document.getElementById('scheduleDate');
    const scheduleTimeSelectEl = document.getElementById('scheduleTimeSelect');
    if (call.appointment_time) {
        // appointment_time is ISO like "2026-03-03T06:39:00"
        const parts = call.appointment_time.split('T');
        if (parts.length === 2) {
            scheduleDateEl.value = parts[0];
            // Format time to HH:mm for simpler matching with select values
            const timePart = parts[1].substring(0, 5); 
            scheduleTimeSelectEl.value = timePart;
        }
    } else {
        scheduleDateEl.value = '';
        scheduleTimeSelectEl.value = '';
    }
    document.getElementById('extraPhone').value = cleanFloatStr(call.extra_phone);

    // POPULATE CENSUS SECTION
    document.getElementById('censusId').value = call.census || '';
    document.getElementById('censusNSE').value = call.nse || '';
    document.getElementById('censusAge').value = call.age || '';
    document.getElementById('censusAgeRange').value = call.age_range || '';
    document.getElementById('censusNeighborhood').value = call.neighborhood || '';
    document.getElementById('censusAddress').value = call.address || '';
    document.getElementById('censusHousing').value = call.housing_description || '';
    document.getElementById('censusChildren').value = call.children_age || '';

    // POPULATE HEADER (ID/CODE)
    const idDisp = document.getElementById('callIdDisplay');
    if (idDisp) idDisp.textContent = call.id;
    // Removed Code Badge Logic

    // Update personBrand to show CODE
    document.getElementById('personBrand').value = call.code || '';

    // POPULATE HAIR STUDY FIELDS
    const setTxt = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val || '-';
    };
    setTxt('hairShampooBrand', call.shampoo_brand);
    setTxt('hairShampooVar', call.shampoo_variety);
    setTxt('hairCondBrand', call.conditioner_brand);
    setTxt('hairCondVar', call.conditioner_variety);
    setTxt('hairTreatBrand', call.treatment_brand);
    setTxt('hairTreatVar', call.treatment_variety);
    setTxt('hairFreq', call.wash_frequency);
    setTxt('hairPurchaseFreq', call.purchase_frequency); // New
    setTxt('hairType', call.hair_type);
    setTxt('hairShape', call.hair_shape);
    setTxt('hairLength', call.hair_length);

    // POPULATE IMPLANTATION DATA
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
    };
    setVal('implantationDate', call.implantation_date);
    setVal('implantationPollster', call.implantation_pollster);
    setVal('implantationSupervisor', call.supervisor);

    // POPULATE DOG DATA SECTION
    const dogSection = document.getElementById('dogSection');
    if (call.dog_name) {
        dogSection.style.display = 'block';
        document.getElementById('dogName').value = call.dog_name || '';
        document.getElementById('dogBreed').value = call.dog_breed || '';
        document.getElementById('dogSize').value = call.dog_size || '';
        document.getElementById('dogUserType').value = call.dog_user_type || '';
        document.getElementById('stoolTexture').value = call.stool_texture || '';
        document.getElementById('healthStatus').value = call.health_status || '';
    } else {
        dogSection.style.display = 'none';
    }

    // WhatsApp field
    const whatsappField = document.getElementById('whatsappNumber');
    if (whatsappField) whatsappField.value = cleanFloatStr(call.whatsapp);

    // NEW FIELDS POPULATION
    document.getElementById('secondDate').value = call.second_collection_date || '';
    document.getElementById('secondTime').value = call.second_collection_time || '';
    
    // Shampoo Quantity with "Otros" handle
    const shampooQtySelect = document.getElementById('shampooQty');
    const shampooQtyOtros = document.getElementById('shampooQtyOtros');
    const standardShampooOpts = ['para 1 lavada', 'para 2 lavadas', 'para 3 lavadas', 'para 4 lavadas', 'ya no tiene shampo', ''];
    
    const qty = call.shampoo_quantity || '';
    if (standardShampooOpts.includes(qty)) {
        shampooQtySelect.value = qty;
        shampooQtyOtros.style.display = 'none';
        shampooQtyOtros.value = '';
    } else {
        shampooQtySelect.value = 'Otros';
        shampooQtyOtros.style.display = 'block';
        shampooQtyOtros.value = qty;
    }

    // Status Badge
    const badge = document.getElementById('callStatusBadge');
    badge.textContent = translateStatus(call.status);
    badge.style.display = 'inline-block';
    if (call.status === 'pending') badge.style.background = '#ffc107';
    else badge.style.background = '#4caf50';

    // Show Sections
    document.getElementById('obsSection').style.display = 'block';
    document.getElementById('scheduleSection').style.display = 'block';

    // ADMIN CONTROLS
    if (currentUserRole === 'superuser' || currentUserRole === 'coordinator') {
        document.getElementById('adminControls').style.display = 'block';
        document.getElementById('currentAgentName').textContent = call.agent_name || 'Sin Asignar';
        // Select logic
        const select = document.getElementById('agentSelect');
        if (call.agent_name) {
            // Find option with text... 
            // Actually better to have user_id, but current API returns agent_name.
            // We will match by text for now or just let them select new.
            select.value = ""; // Reset
        }
    } else {
        document.getElementById('adminControls').style.display = 'none';
    }

    // Load existing obs?
    loadObservations();

    // Show/Hide Close Button based on status
    const btnClose = document.getElementById('btnCloseCall');
    if (call.status === 'closed') {
        btnClose.style.display = 'none';
    } else {
        btnClose.style.display = 'none'; // We use dynamic buttons now
    }

    // Role-Based Actions
    const actionsDiv = document.getElementById('actionButtons');
    actionsDiv.innerHTML = `<button onclick="closeDetailView()" style="background: #94a3b8; border: none; padding: 0.8rem 1.5rem; border-radius: 6px; color: white; cursor: pointer;">Volver</button>`;

    // Helper to create button
    const createBtn = (label, color, statusVal) => {
        const btn = document.createElement('button');
        btn.textContent = label;
        btn.style = `background: ${color}; border: none; padding: 0.8rem 1.5rem; border-radius: 6px; color: white; cursor: pointer;`;
        btn.onclick = () => updateCallStatus(statusVal);
        actionsDiv.appendChild(btn);
    };

    // SUPERUSER: All Access
    if (currentUserRole === 'superuser') {
        createBtn("Revertir a Pendiente", "#64748b", "pending"); // Grey for neutral/back
        createBtn("En Campo", "#3b82f6", "en_campo"); // Blue
        createBtn("Efectiva Presencial", "#22c55e", "efectiva_campo"); // Green - RENAMED
        createBtn("Desempeño", "#ef4444", "caida_desempeno"); // Red - RENAMED
        createBtn("Logístico", "#ef4444", "caida_logistica"); // Red - RENAMED
        createBtn("Caída", "#ef4444", "caida"); // Red - New Generic Caída
        createBtn("Caída Desempeño Campo", "#ef4444", "caida_desempeno_campo"); // Red
        createBtn("Caída Logístico", "#ef4444", "caida_logistico_campo"); // Red - RENAMED
        createBtn("Efectiva", "#22c55e", "managed"); // Green - RENAMED
        createBtn("Agendado", "#3b82f6", "scheduled"); // Blue
    }
    // AUXILIAR: En Campo and Efectiva options
    else if (currentUserRole === 'auxiliar') {
        createBtn("En Campo", "#3b82f6", "en_campo"); // Blue
        createBtn("Efectiva Presencial", "#22c55e", "efectiva_campo"); // Green - RENAMED
        createBtn("Caída Desempeño Campo", "#ef4444", "caida_desempeno_campo"); // Red
        createBtn("Caída Logístico", "#ef4444", "caida_logistico_campo"); // Red - RENAMED
    }
    // AGENT: Standard Flow with new caída options
    else {
        createBtn("Efectiva", "#22c55e", "managed"); // Green - RENAMED
        createBtn("Agendado", "#3b82f6", "scheduled"); // Blue
        createBtn("Desempeño", "#ef4444", "caida_desempeno"); // Red - RENAMED
        createBtn("Logístico", "#ef4444", "caida_logistica"); // Red - RENAMED
        createBtn("Caída", "#ef4444", "caida"); // Red - New Generic Caída
    }

    showDetailView();
}

// --- Bonus Modal Helper ---
let bonusResolve = null;

function promptBonusStatus() {
    return new Promise((resolve) => {
        bonusResolve = resolve;
        document.getElementById('bonusModal').style.display = 'block';
    });
}

window.resolveBonusSelection = (val) => {
    document.getElementById('bonusModal').style.display = 'none';
    if (bonusResolve) bonusResolve(val);
};

async function updateCallStatus(newStatus) {
    if (!currentCallId) return;

    let surveyId = null;
    let bonusStatus = null;

    // If marking as "Gestionado", prompt for survey ID and bonus status
    if (newStatus === 'managed') {
        const stage = (typeof allCalls !== 'undefined' && allCalls) 
            ? (allCalls.find(c => c.id === currentCallId)?.study_stage || "").toUpperCase() 
            : "";

        if (stage !== 'RF') {
            const secondDate = document.getElementById('secondDate').value;
            const secondTime = document.getElementById('secondTime').value;

            if (!secondDate || !secondTime) {
                alert("No has guardado fecha de segunda recogida, por favor agrégala y luego guarda como efectiva.");
                return;
            }
        }

        surveyId = prompt("Ingrese el ID de la encuesta (alfanumérico):");
        if (surveyId === null) return; // User cancelled
        surveyId = surveyId.trim();

        if (!surveyId) {
            alert("El ID de la encuesta es obligatorio para marcar como Gestionado");
            return;
        }

        // Prompt for bonus status using Custom Modal
        bonusStatus = await promptBonusStatus();
        if (bonusStatus === null) return; // User cancelled
    }

    if (!confirm(`¿Cambiar estado a "${newStatus}"?`)) return;

    try {
        const body = { status: newStatus };

        // Add survey fields if provided
        if (surveyId !== null && bonusStatus !== null) {
            body.survey_id = surveyId;
            body.bonus_status = bonusStatus;
        }

        const res = await fetch(`/calls/${currentCallId}/status`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body)
        });

        if (res.ok) {
            alert("Estado actualizado");

            // LOCAL UPDATE ONLY
            const callIndex = allCalls.findIndex(c => c.id === currentCallId);
            if (callIndex !== -1) {
                allCalls[callIndex].status = newStatus;

                // VISIBILITY FIX: 
                // If user is restricted (Agent/Supervisor) AND status is NOT pending/scheduled, remove from view immediately.
                // Allowed roles to see everything: superuser, coordinator, auxiliar
                const allowedRoles = ['superuser', 'coordinator', 'auxiliar'];

                if (!allowedRoles.includes(currentUserRole)) {
                    // Restricted User
                    if (newStatus !== 'pending' && newStatus !== 'scheduled') {
                        // Remove from array so it disappears from grid
                        allCalls.splice(callIndex, 1);
                    }
                }
            }

            // Re-apply filters to update view (e.g. if filtering by status, call might disappear from view)
            applyColumnFilters();

            showGridView();
        } else if (res.status === 401) {
            // Handle session expiration specifically
            alert("Tu sesión ha expirado por inactividad. Serás redirigido para iniciar sesión nuevamente.");
            localStorage.removeItem('token');
            window.location.href = '/login';
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "Error al actualizar"));
        }
    } catch (e) { console.error(e); alert("Error de conexión"); }
}

async function finishCall() {
    // Legacy function - redirected to updateCallStatus('closed') if called directly?
    // But we hid the button.
    updateCallStatus('closed');
}

async function loadAgents() {
    if (currentUserRole !== 'superuser' && currentUserRole !== 'coordinator' && currentUserRole !== 'auxiliar') return;
    try {
        const res = await fetch('/users', { headers });
        if (res.ok) {
            const users = await res.json();
            const sel = document.getElementById('agentSelect');
            const bulkSel = document.getElementById('bulkAgentSelect');

            // Destroy existing TomSelect instances if they exist
            if (sel.tomselect) sel.tomselect.destroy();
            if (bulkSel.tomselect) bulkSel.tomselect.destroy();

            sel.innerHTML = '<option value="">Seleccionar Agente...</option>';
            bulkSel.innerHTML = '<option value="">Asignar a...</option>';

            users.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                // Use Full Name if available, fallback to username
                opt.textContent = u.full_name || u.username;
                sel.appendChild(opt.cloneNode(true));
                bulkSel.appendChild(opt);
            });

            // Add "Unassign" option for Superusers
            const unassignOpt = document.createElement('option');
            unassignOpt.value = "UNASSIGN";
            unassignOpt.textContent = "Desasignar / Liberar";
            // TomSelect handles styling via classes/data attributes better, but we will leave this logic
            bulkSel.appendChild(unassignOpt);

            // Show Bulk Actions
            document.getElementById('bulkActions').style.display = 'block';

            // Initialize TomSelect
            new TomSelect(sel, {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });

            new TomSelect(bulkSel, {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });
        }
    } catch (e) { console.error("Error loading users", e); }
}

// Replaces loadAgents (which was higher up in previous view range, but let's redefine it or find it. Wait, I missed it in view. It was around 270-300?)
// Ah, `loadAgents` was in the snippet I viewed at step 387? No.
// Let's assume it was deleted or I missed it.
// I see `assignAgent` at 302.

async function assignAgent() {
    if (!currentCallId) return;
    const userId = document.getElementById('agentSelect').value;
    if (!userId) {
        alert("Seleccione un agente");
        return;
    }

    const select = document.getElementById('agentSelect');
    const agentName = select.options[select.selectedIndex].text;

    if (!confirm(`¿Seguro que va a asignar esta llamada a ${agentName}?`)) return;

    // REFACTORED UPDATE LOGIC TO PREVENT FILTER RESET
    try {
        const res = await fetch(`/calls/${currentCallId}/assign`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ user_id: parseInt(userId) })
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Llamada asignada a: ${data.agent}`);

            // LOCAL UPDATE ONLY
            const callIndex = allCalls.findIndex(c => c.id === currentCallId);
            if (callIndex !== -1) {
                // Update fields
                allCalls[callIndex].agent_id = parseInt(userId);
                // We need the agent name. The API returns it, or we find it in the list.
                // data.agent contains the name according to backend response used in alert?
                // The backend response for assign usually returns {"status":..., "agent": "Name"}
                allCalls[callIndex].agent_name = data.agent;
                allCalls[callIndex].status = 'pending'; // Reset status on assignment? Usually yes, or keeps 'pending'.
            }

            // Re-apply filters and render without reloading whole study
            applyFilter(); // or searchCalls() if using search
            // If using the new column filters:
            applyColumnFilters();

            showGridView();
        } else {
            let errorMsg = "Error al asignar";
            try {
                const err = await res.json();
                if (err.detail) errorMsg += ": " + err.detail;
            } catch (e) {}
            alert(errorMsg);
        }
    } catch (e) {
        console.error(e);
        alert("Error de red al asignar");
    }
}

// BULK ACTIONS
function toggleSelectAll() {
    const main = document.getElementById('selectAll');
    const checks = document.querySelectorAll('.call-checkbox');
    checks.forEach(c => c.checked = main.checked);
}

async function bulkAssign() {
    const checks = document.querySelectorAll('.call-checkbox:checked');
    if (checks.length === 0) {
        alert("Seleccione al menos una llamada");
        return;
    }

    const userId = document.getElementById('bulkAgentSelect').value;
    if (!userId) {
        alert("Seleccione un agente para asignar");
        return;
    }

    const select = document.getElementById('bulkAgentSelect');
    const agentName = select.options[select.selectedIndex].text;

    if (userId !== "UNASSIGN") {
        if (!confirm(`¿Seguro que va a asignar ${checks.length} llamadas a ${agentName}?`)) return;
    }

    // Check for explicit "UNASSIGN" value or valid ID
    let finalUserId = null;
    if (userId === "UNASSIGN") {
        if (!confirm("¿Está seguro de desasignar estas llamadas? Quedarán libres.")) return;
        finalUserId = null;
    } else {
        finalUserId = parseInt(userId);
    }

    const ids = Array.from(checks).map(c => parseInt(c.value));

    try {
        const res = await fetch('/calls/assign-bulk', {
            method: 'PUT',
            headers,
            body: JSON.stringify({ call_ids: ids, user_id: finalUserId })
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Asignadas ${data.count} llamadas exitosamente.`);
            // Refresh
            const sel = document.getElementById('studySelect');
            if (sel.value) loadStudyData(sel.value);
            else loadStudyData(null);
        } else {
            let errorMsg = "Error en asignación masiva";
            try {
                const err = await res.json();
                if (err.detail) errorMsg += ": " + err.detail;
            } catch (e) {}
            alert(errorMsg);
        }
    } catch (e) {
        console.error(e);
        alert("Error de red en asignación masiva");
    }
}

async function createStudy() {
    const code = prompt("Código del Estudio:");
    const name = prompt("Nombre del Estudio:");
    if (code && name) {
        await fetch('/studies', {
            method: 'POST',
            headers,
            body: JSON.stringify({ code, name })
        });
        loadStudies();
    }
}

async function saveCallHeader() {
    const studyId = document.getElementById('studySelect').value;
    const phone = document.getElementById('phoneNumber').value;
    const corrected = document.getElementById('correctedPhone').value;
    const cc = document.getElementById('personCC').value;
    const extraPhone = document.getElementById('extraPhone').value;

    // Check if we are UPDATING an existing call
    if (currentCallId) {
        if (!phone) {
            alert("El número de celular es obligatorio.");
            return;
        }

        const body = {
            // phone_number: phone, // Removed to prevent primary phone update
            corrected_phone: corrected,
            person_cc: cc,
            extra_phone: extraPhone,
            // New Fields
            second_collection_date: document.getElementById('secondDate').value,
            second_collection_time: document.getElementById('secondTime').value,
            shampoo_quantity: (document.getElementById('shampooQty').value === 'Otros') 
                ? document.getElementById('shampooQtyOtros').value 
                : document.getElementById('shampooQty').value
        };

        try {
            const res = await fetch(`/calls/${currentCallId}/contact`, {
                method: 'PUT',
                headers,
                body: JSON.stringify(body)
            });

            if (res.ok) {
                alert("Datos de contacto actualizados");
            } else {
                const err = await res.json();
                alert("Error: " + (err.detail || "Error al actualizar"));
            }
        } catch (e) { console.error(e); alert("Error de conexión"); }

        return;
    }

    // CREATION MODE (Legacy)
    if (!studyId || !phone) {
        alert("Debe seleccionar un estudio y digitar un número.");
        return;
    }

    alert("Datos de cabecera guardados (Simulado)");
}

async function saveSecondPickup() {
    if (!currentCallId) return;

    // We reuse the same endpoint but specifically for these fields
    const body = {
        // phone_number: document.getElementById('phoneNumber').value, // Removed to prevent primary phone update
        corrected_phone: document.getElementById('correctedPhone').value,
        person_cc: document.getElementById('personCC').value,
        extra_phone: document.getElementById('extraPhone').value,

        // Target Fields
        second_collection_date: document.getElementById('secondDate').value,
        second_collection_time: document.getElementById('secondTime').value,
        shampoo_quantity: (document.getElementById('shampooQty').value === 'Otros') 
            ? document.getElementById('shampooQtyOtros').value 
            : document.getElementById('shampooQty').value
    };

    try {
        const res = await fetch(`/calls/${currentCallId}/contact`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body)
        });

        if (res.ok) {
            alert("Información de Segunda Recogida Guardada");
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "Error al actualizar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}


async function loadObservations() {
    if (!currentCallId) return;
    try {
        const res = await fetch(`/calls/${currentCallId}/observations`, { headers });
        const obs = await res.json();
        renderObservations(obs);
    } catch (e) { console.error(e); }
}

function renderObservations(obs) {
    const feed = document.getElementById('obsFeed');
    if (!feed) return;
    feed.innerHTML = '';
    
    try {
        const sorted = [...obs].sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
        sorted.forEach(o => {
            const el = document.createElement('div');
            el.className = 'obs-item';
            
            let dateStr = "Fecha desconocida";
            if (o.created_at) {
                const d = new Date(o.created_at);
                if (d.getFullYear() > 1970) {
                    dateStr = d.toLocaleString();
                }
            }

            el.innerHTML = `
                <div style="margin-bottom: 4px; font-size: 0.95rem;">${o.text}</div>
                <div class="obs-meta" style="display: flex; align-items: center; justify-content: space-between; color: #64748b;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                         <span style="background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: flex; align-items: center;">
                            <i class="fas fa-user" style="margin-right: 4px; font-size: 0.7rem;"></i>
                            ${o.user_name || 'Sistema'}
                         </span>
                    </div>
                    <span style="font-size: 0.75rem;">${dateStr}</span>
                </div>
            `;
            feed.appendChild(el);
        });
    } catch (e) { console.error(e); }
}

function renderObservationShortcuts() {
    const container = document.getElementById('observation-shortcuts');
    if (!container) return;
    container.innerHTML = '';

    obsCategories.forEach(cat => {
        const group = document.createElement('div');
        group.className = 'shortcut-group';
        
        const label = document.createElement('div');
        label.className = 'shortcut-group-label';
        label.textContent = cat.label;
        group.appendChild(label);

        const chipsContainer = document.createElement('div');
        chipsContainer.className = 'shortcut-chips';

        cat.options.forEach(opt => {
            const optText = typeof opt === 'string' ? opt : opt.text;
            const isPositive = typeof opt !== 'string' && opt.type === 'positive';
            const isNoContesta = optText.toLowerCase().includes('no contesta') || 
                               optText.toLowerCase().includes('no tiene') ||
                               optText.toLowerCase().includes('ocupado') ||
                               optText.toLowerCase().includes('buzón');

            const chip = document.createElement('div');
            chip.className = 'opt-chip';
            chip.dataset.category = cat.category;
            chip.dataset.text = optText;
            if (isPositive) chip.dataset.type = 'positive';
            if (isNoContesta) chip.dataset.exclusion = 'negative';
            
            chip.innerHTML = optText;
            chip.onclick = () => handleShortcutClick(chip, cat.category, optText, isPositive, isNoContesta);
            chipsContainer.appendChild(chip);
        });

        group.appendChild(chipsContainer);
        container.appendChild(group);
    });
}

function handleShortcutClick(chip, category, text, isPositive, isNoContesta) {
    const chips = document.querySelectorAll('.opt-chip');
    const wasActive = chip.classList.contains('active');

    // EXCLUSION LOGIC (Intra-category): Deselect others in the same group
    if (!wasActive) {
        document.querySelectorAll(`.opt-chip[data-category="${category}"]`).forEach(c => {
            c.classList.remove('active');
        });
    }

    // EXCLUSION LOGIC (Cross-category): Positive vs Negative
    if (!wasActive && isPositive) {
        chips.forEach(c => {
            if (c.dataset.exclusion === 'negative') c.classList.remove('active');
        });
    }
    if (!wasActive && isNoContesta) {
        chips.forEach(c => {
            if (c.dataset.type === 'positive') c.classList.remove('active');
        });
    }

    if (wasActive) {
        chip.classList.remove('active');
    } else {
        chip.classList.add('active');
    }

    updateObservationTextFromShortcuts();
}


function updateObservationTextFromShortcuts() {
    const activeChips = document.querySelectorAll('.opt-chip.active');
    const textarea = document.getElementById('newObs');
    
    const groups = {};
    activeChips.forEach(c => {
        const cat = c.dataset.category;
        const text = c.dataset.text;
        const catObj = obsCategories.find(oc => oc.category === cat);
        const displayCat = catObj ? catObj.label : cat;
        if (!groups[displayCat]) groups[displayCat] = [];
        groups[displayCat].push(text);
    });

    let finalStr = '';
    for (const [cat, texts] of Object.entries(groups)) {
        finalStr += `[${cat}: ${texts.join(', ')}] `;
    }
    textarea.value = finalStr.trim();
}

async function addObservation() {
    if (!currentCallId) return;
    const text = document.getElementById('newObs').value;
    if (!text) return;

    const res = await fetch(`/calls/${currentCallId}/observation`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ text })
    });

    if (res.ok) {
        document.getElementById('newObs').value = '';
        loadObservations();
        // Clear active shortcuts
        document.querySelectorAll('.opt-chip.active').forEach(chip => chip.classList.remove('active'));
    }
}



async function scheduleAlert() {
    if (!currentCallId) return;
    
    const date = document.getElementById('scheduleDate').value;
    const timeVal = document.getElementById('scheduleTimeSelect').value;
    
    if (!date || !timeVal) {
        alert("Debe seleccionar Fecha y Hora para programar la alerta.");
        return;
    }

    let finalTime = timeVal;
    // Mapping for text-based options
    if (timeVal === "En la mañana" || timeVal === "Durante el día" || timeVal === "Escribir antes") {
        finalTime = "10:00";
    } else if (timeVal === "En la tarde") {
        finalTime = "14:00";
    }
    
    const isoDateTime = `${date}T${finalTime}:00`;

    const res = await fetch(`/calls/${currentCallId}/schedule`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ scheduled_time: isoDateTime })
    });

    if (res.ok) {
        alert("Alerta Programada");

        // Clear existing alarm flags for this call so it can ring again if rescheduled
        if (typeof alertedCallIds !== 'undefined') {
            alertedCallIds.delete(currentCallId);
        }
        if (typeof pendingTriggerTimeouts !== 'undefined' && pendingTriggerTimeouts[currentCallId]) {
            clearTimeout(pendingTriggerTimeouts[currentCallId]);
            delete pendingTriggerTimeouts[currentCallId];
        }

        // Refresh Grid to show new status and time
        const sel = document.getElementById('studySelect');
        if (sel.value) loadStudyData(sel.value);
        else loadStudyData(null);

        // Instantly poll to register the new alarm locally without waiting 10 mins
        if (typeof pollUpcomingCalls === 'function') {
            pollUpcomingCalls();
        }
    }
}

// EXPORT TO EXCEL (XLSX)
function exportToExcel() {
    const dataToExport = (typeof filteredCalls !== 'undefined' && filteredCalls && filteredCalls.length > 0) ? filteredCalls : allCalls;

    if (!dataToExport || dataToExport.length === 0) {
        alert("No hay datos para exportar");
        return;
    }

    // Map to Spanish headers
    const exportData = dataToExport.map(row => ({
        "Telefono": row.phone_number || '',
        "Fecha": row.collection_date || (row.created_at ? new Date(row.created_at).toLocaleDateString() : ''),
        "Estudio": row.study_name || '',
        "Agente": row.agent_name || 'Sin Asignar',
        "Nombre": row.person_name || '',
        "Ciudad": row.city || '',
        "Estado": translateStatus(row.status),
        "Censo": row.census || '',
        "NSE": row.nse || '',
        "Edad": row.age || '',
        "Barrio": row.neighborhood || '',
        "Fecha 2 Recogida": row.second_collection_date || '',
        "Hora 2 Recogida": row.second_collection_time || '',
        "Encuestador": row.implantation_pollster || '',
        "Shampoo": row.shampoo_quantity || '',
        "Observaciones Iniciales": row.initial_observation || '',
        "Observaciones": row.concatenated_observations || 'no tiene'
    }));

    // Create Worksheet
    const ws = XLSX.utils.json_to_sheet(exportData);

    // Create Workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Llamadas");

    // Generate filename
    const dateStr = new Date().toISOString().split('T')[0];
    const fileName = `llamadas_export_${dateStr}.xlsx`;

    // Download
    XLSX.writeFile(wb, fileName);
}

// --- AUXILIAR ASSIGNMENT ---
let currentAssignStudyId = null;

async function openAssignAux(studyId, studyName) {
    currentAssignStudyId = studyId;
    document.getElementById('assignAuxTitle').textContent = "Estudio: " + studyName;
    document.getElementById('assignAuxList').innerHTML = 'Cargando...';
    document.getElementById('assignAuxModal').style.display = 'flex';

    try {
        // 1. Get All Users (to filter Auxiliaries)
        const uRes = await fetch('/users', { headers });
        if (!uRes.ok) throw new Error("Error loading users");
        const allUsers = await uRes.json();
        const auxiliaries = allUsers.filter(u => u.role === 'auxiliar');

        // 2. Get Assigned Users
        const aRes = await fetch(`/studies/${studyId}/assistants`, { headers });
        if (!aRes.ok) throw new Error("Error loading assignments");
        const assigned = await aRes.json();
        const assignedIds = new Set(assigned.map(u => u.id));

        // 3. Render
        const container = document.getElementById('assignAuxList');
        container.innerHTML = '';

        if (auxiliaries.length === 0) {
            container.innerHTML = '<p style="color:red;">No hay usuarios con rol "auxiliar" en el sistema.</p>';
            return;
        }

        auxiliaries.forEach(aux => {
            const isChecked = assignedIds.has(aux.id) ? 'checked' : '';
            const div = document.createElement('div');
            div.innerHTML = `
                <label style="display:flex; align-items:center; gap:10px; cursor:pointer; padding:5px; border-radius:4px; border:1px solid #eee;">
                    <input type="checkbox" class="aux-check" value="${aux.id}" ${isChecked}>
                    <div>
                        <span style="font-weight:bold; display:block; color: #1e293b;">${aux.full_name || aux.username}</span>
                        <span style="font-size:0.8rem; color:#666;">${aux.username}</span>
                    </div>
                </label>
            `;
            container.appendChild(div);
        });

    } catch (e) {
        console.error(e);
        document.getElementById('assignAuxList').textContent = "Error al cargar datos.";
    }
}

function closeAssignAux() {
    document.getElementById('assignAuxModal').style.display = 'none';
    currentAssignStudyId = null;
}

async function saveStudyAssistants() {
    if (!currentAssignStudyId) return;

    const checks = document.querySelectorAll('.aux-check:checked');
    const userIds = Array.from(checks).map(c => parseInt(c.value));

    try {
        const res = await fetch(`/studies/${currentAssignStudyId}/assistants`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ user_ids: userIds })
        });

        if (res.ok) {
            alert("Asignaciones guardadas");
            closeAssignAux();
        } else {
            alert("Error al guardar");
        }
    } catch (e) { console.error(e); alert("asigna error"); }
}



// --- DAILY REPORT FEATURE ---
let dailyReportFpInstance = null;
let dailyReportStudyTS = null;
let dailyReportAgentTS = null;
let dailyReportCityTS = null;

async function showDailyReport() {
    const modal = document.getElementById('dailyReportModal');
    const dateInput = document.getElementById('dailyReportDate');

    modal.style.display = 'flex';

    // Initialize Flatpickr if not already done
    if (dateInput && !dailyReportFpInstance) {
        dateInput.type = 'text';
        dailyReportFpInstance = flatpickr(dateInput, {
            mode: "range",
            dateFormat: "Y-m-d",
            locale: "es",
            conjunction: " to ",
            defaultDate: new Date(),
            onChange: async function (selectedDates, dateStr, instance) {
                if (selectedDates.length === 1 || selectedDates.length === 2) {
                    await initDailyReportAgentSelect();
                    await initDailyReportCitySelect();
                    refreshDailyReport();
                }
            }
        });
    }

    // Initialize/Refresh Selects
    await initDailyReportStudySelect();
    await initDailyReportAgentSelect();
    await initDailyReportCitySelect();

    // Initial load
    refreshDailyReport();
}

async function initDailyReportStudySelect() {
    const sel = document.getElementById('dailyReportStudySelect');
    if (!sel) return;

    try {
        const openOnly = document.getElementById('dailyReportOpenOnly').checked;
        const res = await fetch('/studies', { headers });
        let studies = await res.json();

        if (openOnly) {
            studies = studies.filter(s => (s.is_active === true || s.is_active === 1) && s.status === 'open');
        }

        if (dailyReportStudyTS) dailyReportStudyTS.destroy();

        sel.innerHTML = '';
        studies.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.code} - ${s.name}`;
            sel.appendChild(opt);
        });

        dailyReportStudyTS = new TomSelect(sel, {
            plugins: ['remove_button'],
            create: false,
            placeholder: "Todos los estudios...",
            onBlur: () => refreshDailyReport()
        });

    } catch (e) {
        console.error("Error loading studies for report", e);
    }
}

async function initDailyReportAgentSelect() {
    const sel = document.getElementById('dailyReportAgentSelect');
    if (!sel) return;

    try {
        const openOnly = document.getElementById('dailyReportOpenOnly').checked;
        const res = await fetch(`/reports/active-agents?open_only=${openOnly}`, { headers });
        let users = await res.json();

        if (dailyReportAgentTS) dailyReportAgentTS.destroy();

        sel.innerHTML = '';
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = `${u.full_name || u.username}`;
            sel.appendChild(opt);
        });

        dailyReportAgentTS = new TomSelect(sel, {
            plugins: ['remove_button'],
            create: false,
            placeholder: "Todos los agentes...",
            onBlur: () => refreshDailyReport()
        });

    } catch (e) {
        console.error("Error loading agents for report", e);
    }
}

async function initDailyReportCitySelect() {
    const sel = document.getElementById('dailyReportCitySelect');
    if (!sel) return;

    try {
        const res = await fetch(`/reports/active-cities`, { headers });
        if (!res.ok) throw new Error("Could not fetch active cities");
        let payload = await res.json();

        let uniqueCities = [];
        if (Array.isArray(payload)) {
            uniqueCities = payload;
        }

        if (dailyReportCityTS) dailyReportCityTS.destroy();

        sel.innerHTML = '<option value="">(Sin agrupar)</option>';
        uniqueCities.forEach(city => {
            if (!city) return;
            const opt = document.createElement('option');
            opt.value = city;
            opt.textContent = city;
            sel.appendChild(opt);
        });

        dailyReportCityTS = new TomSelect(sel, {
            create: false,
            placeholder: "Agrupar por...",
            onChange: () => refreshDailyReport()
        });

    } catch (e) {
        console.error("Error loading cities for report", e);
    }
}

let dailyReportTimeout = null;

function refreshDailyReport() {
    if (dailyReportTimeout) {
        clearTimeout(dailyReportTimeout);
    }
    
    dailyReportTimeout = setTimeout(() => {
        const dateInput = document.getElementById('dailyReportDate');
        const dateStr = dateInput ? dateInput.value : '';
        const openOnly = document.getElementById('dailyReportOpenOnly') ? document.getElementById('dailyReportOpenOnly').checked : false;

        let studyIds = null;
        if (dailyReportStudyTS) {
            studyIds = dailyReportStudyTS.getValue();
            if (Array.isArray(studyIds)) studyIds = studyIds.join(',');
        }

        let agentIds = null;
        if (dailyReportAgentTS) {
            agentIds = dailyReportAgentTS.getValue();
            if (Array.isArray(agentIds)) agentIds = agentIds.join(',');
        }

        let cityFilter = null;
        if (dailyReportCityTS) {
            cityFilter = dailyReportCityTS.getValue() || null;
        }

        fetchDailyReportData(dateStr, openOnly, studyIds, agentIds, cityFilter);
    }, 300); // 300ms de retraso para evitar múltiples recargas seguidas
}

async function fetchDailyReportData(dateStr, openOnly = false, studyIds = null, agentIds = null, cityFilter = null) {
    const content = document.getElementById('dailyReportContent');
    content.innerHTML = '<div style="text-align:center; padding: 2rem;">Cargando...</div>';

    try {
        let params = new URLSearchParams();
        if (dateStr) params.append('date', dateStr);
        if (openOnly) params.append('open_only', 'true');
        if (studyIds) params.append('study_ids', studyIds);
        if (agentIds) params.append('agent_ids', agentIds);
        if (cityFilter) params.append('group_by_city', cityFilter);

        let url = '/reports/daily-effectives';
        const qs = params.toString();
        if (qs) url += '?' + qs;

        const res = await fetch(url, { headers });
        if (res.ok) {
            const data = await res.json();

            if (data.length === 0) {
                content.innerHTML = '<div style="text-align:center; padding: 2rem; color: #64748b;">No hay efectividad registrada hoy.</div>';
                return;
            }

            let html = '';

            data.forEach(study => {
                let tableRows = '';
                if (study.agents.length === 0) {
                    tableRows = `<div style="padding: 0.5rem; color: #94a3b8; font-style: italic;">Sin productividad hoy</div>`;
                } else {
                    // Agrupar agentes y recolectar ciudades únicas
                    const agentsMap = {};
                    const citiesSet = new Set();

                    study.agents.forEach(a => {
                        const cityName = (a.city && a.city.trim() !== "") ? a.city : 'Sin Asignar';
                        citiesSet.add(cityName);

                        if (!agentsMap[a.name]) {
                            agentsMap[a.name] = { 
                                name: a.name || 'Desconocido', 
                                totals: { effective: 0, desempeno: 0, logistico: 0 },
                                cities: {} 
                            };
                        }

                        if (!agentsMap[a.name].cities[cityName]) {
                            agentsMap[a.name].cities[cityName] = { effective: 0, desempeno: 0, logistico: 0 };
                        }

                        agentsMap[a.name].cities[cityName].effective += a.count_effective;
                        agentsMap[a.name].cities[cityName].desempeno += a.count_desempeno;
                        agentsMap[a.name].cities[cityName].logistico += a.count_logistico;

                        agentsMap[a.name].totals.effective += a.count_effective;
                        agentsMap[a.name].totals.desempeno += a.count_desempeno;
                        agentsMap[a.name].totals.logistico += a.count_logistico;
                    });

                    const sortedCities = Array.from(citiesSet).sort();

                    // Construir cabeceras dinámicas
                    let theadHtml = `<th style="padding: 0.5rem;">Agente</th>`;

                    if (sortedCities.length > 0 && !cityFilter) {
                        // Varias ciudades (o sin filtro)
                        sortedCities.forEach(c => {
                            theadHtml += `<th style="padding: 0.5rem; text-align: center; font-size: 0.75rem;">Efectivas<br>${c}</th>`;
                        });
                        theadHtml += `<th style="padding: 0.5rem; text-align: center; font-weight: bold; border-right: 2px solid #e2e8f0; background: #f8fafc;">Total Efe</th>`;

                        sortedCities.forEach(c => {
                            theadHtml += `<th style="padding: 0.5rem; text-align: center; font-size: 0.75rem;">Desempeño<br>${c}</th>`;
                        });
                        theadHtml += `<th style="padding: 0.5rem; text-align: center; font-weight: bold; border-right: 2px solid #e2e8f0; background: #f8fafc;">Total Des</th>`;

                        sortedCities.forEach(c => {
                            theadHtml += `<th style="padding: 0.5rem; text-align: center; font-size: 0.75rem;">Logístico<br>${c}</th>`;
                        });
                        theadHtml += `<th style="padding: 0.5rem; text-align: center; font-weight: bold; background: #f8fafc;">Total Log</th>`;
                    } else {
                        // Vista clásica / unificando solo totales si cityFilter existe
                        theadHtml += `<th style="padding: 0.5rem; text-align: center;">Efectivas</th>
                                    <th style="padding: 0.5rem; text-align: center;">Desempeño</th>
                                    <th style="padding: 0.5rem; text-align: center;">Logístico</th>
                                    ${cityFilter ? '<th style="padding: 0.5rem; text-align: center;">Ciudad</th>' : ''}`;
                    }

                    tableRows = `<table style="width: 100%; border-collapse: collapse; text-align: left; white-space: nowrap;">
                        <thead>
                            <tr style="border-bottom: 2px solid #e2e8f0; color: #64748b; font-size: 0.85rem;">
                                ${theadHtml}
                            </tr>
                        </thead>
                        <tbody>`;

                    // Llenar datos, order by efectivas desc
                    const sortedAgents = Object.values(agentsMap).sort((a, b) => b.totals.effective - a.totals.effective);

                    sortedAgents.forEach(agent => {
                        tableRows += `<tr style="border-bottom: 1px solid #f1f5f9;">
                            <td style="padding: 0.5rem; color: #475569;">${agent.name}</td>`;

                        if (sortedCities.length > 0 && !cityFilter) {
                            // Efectivas
                            sortedCities.forEach(c => {
                                const val = agent.cities[c] ? agent.cities[c].effective : 0;
                                tableRows += `<td style="padding: 0.5rem; text-align: center; color: #22c55e;">${val}</td>`;
                            });
                            tableRows += `<td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #16a34a; border-right: 2px solid #e2e8f0; background: #f8fafc;">${agent.totals.effective}</td>`;

                            // Desempeño
                            sortedCities.forEach(c => {
                                const val = agent.cities[c] ? agent.cities[c].desempeno : 0;
                                tableRows += `<td style="padding: 0.5rem; text-align: center; color: #ef4444;">${val}</td>`;
                            });
                            tableRows += `<td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #dc2626; border-right: 2px solid #e2e8f0; background: #f8fafc;">${agent.totals.desempeno}</td>`;

                            // Logístico
                            sortedCities.forEach(c => {
                                const val = agent.cities[c] ? agent.cities[c].logistico : 0;
                                tableRows += `<td style="padding: 0.5rem; text-align: center; color: #f59e0b;">${val}</td>`;
                            });
                            tableRows += `<td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #d97706; background: #f8fafc;">${agent.totals.logistico}</td>`;

                        } else {
                            // Classic visual if filtered
                            tableRows += `<td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #22c55e;">${agent.totals.effective}</td>
                                        <td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #ef4444;">${agent.totals.desempeno}</td>
                                        <td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #f59e0b;">${agent.totals.logistico}</td>
                                        ${cityFilter ? `<td style="padding: 0.5rem; text-align: center; font-weight: bold; color: #334155;">${sortedCities[0] || cityFilter}</td>` : ''}`;
                        }
                        
                        tableRows += `</tr>`;
                    });

                    tableRows += `</tbody></table>`;
                }

                html += `
                    <div style="margin-bottom: 1.5rem; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                        <div style="background: #f8fafc; padding: 0.8rem; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #334155; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.5rem;">
                            <span>${study.study_name} ${cityFilter ? ` - [${cityFilter}]` : ''}</span>
                            <div style="display: flex; gap: 0.5rem;">
                                <span style="background: #22c55e; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem;">Efec: ${study.total_effective}</span>
                                <span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem;">Desp: ${study.total_desempeno}</span>
                                <span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem;">Log: ${study.total_logistico}</span>
                            </div>
                        </div>
                        <div style="padding: 0.5rem; overflow-x: auto;">
                            ${tableRows}
                        </div>
                    </div>
                `;
            });

            // --- GRAN TOTAL AL FINAL ---
            const grandTotalEfe = data.reduce((sum, s) => sum + (s.total_effective || 0), 0);
            const grandTotalDes = data.reduce((sum, s) => sum + (s.total_desempeno || 0), 0);
            const grandTotalLog = data.reduce((sum, s) => sum + (s.total_logistico || 0), 0);

            html += `
                <div style="margin-top: 1rem; border: 2px solid #334155; border-radius: 8px; overflow: hidden;">
                    <div style="background: #1e293b; padding: 0.8rem 1.2rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <span style="color: white; font-weight: bold; font-size: 1rem;">📊 TOTAL GENERAL</span>
                        <div style="display: flex; gap: 1rem; align-items: center;">
                            <span style="background: #22c55e; color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: bold;">Efectivas: ${grandTotalEfe}</span>
                            <span style="background: #ef4444; color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: bold;">Desempeño: ${grandTotalDes}</span>
                            <span style="background: #f59e0b; color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.95rem; font-weight: bold;">Logístico: ${grandTotalLog}</span>
                        </div>
                    </div>
                </div>
            `;

            content.innerHTML = html;

        } else {
            console.error(res);
            content.innerHTML = '<div style="color:red; text-align:center;">Error al cargar reporte.</div>';
        }
    } catch (e) {
        console.error(e);
        content.innerHTML = '<div style="color:red; text-align:center;">Error de conexión.</div>';
    }
}

function closeDailyReport() {
    document.getElementById('dailyReportModal').style.display = 'none';
}

// --- ACTIVE ALARM SYSTEM ---
let alertedCallIds = new Set();
let alarmPollingInterval = null;
let pendingTriggerTimeouts = {}; // Store timeouts so we can clear them if needed

async function pollUpcomingCalls() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const res = await fetch('/calls/upcoming', { headers });
        if (res.ok) {
            const upcomingCalls = await res.json();

            const now = new Date();

            for (const call of upcomingCalls) {
                // If we haven't already processed this call
                if (!alertedCallIds.has(call.id) && call.appointment_time) {

                    // The backend sends ISO string like "2026-03-03T06:39:00" WITHOUT timezone (naive)
                    // new Date() in JS assumes naive strings are local time in most modern browsers, 
                    // BUT if it appends 'Z' it's UTC. Let's explicitly parse it as local.

                    // Replace 'Z' if present to force local evaluation, just in case
                    const cleanTime = call.appointment_time.replace('Z', '');
                    const apptTime = new Date(cleanTime);
                    const diffMs = apptTime - now;

                    console.log("ALARM DEBUG:", {
                        callId: call.id,
                        backendTimeStr: call.appointment_time,
                        parsedApptTime: apptTime.toString(),
                        browserNow: now.toString(),
                        diffMs: diffMs,
                        diffMinutes: diffMs / 60000
                    });

                    // We want to alert EXACTLY 5 minutes before (300,000 ms)
                    // The backend gives us calls up to 12 minutes away

                    // If the difference is less than 5 minutes, alert immediately (we might have just fallen into the window)
                    if (diffMs <= 300000 && diffMs > 0) {
                        alertedCallIds.add(call.id);
                        showAlarmModal(call);
                    }
                    // If it's more than 5 minutes away, schedule a timeout to trigger at exactly 5 mins before
                    else if (diffMs > 300000) {
                        const msUntilFiveMinsBefore = diffMs - 300000;

                        // Prevent scheduling multiple timeouts for the same call if it's fetched again
                        if (!pendingTriggerTimeouts[call.id]) {
                            console.log(`ALARM DEBUG: Scheduling timeout for call ${call.id} to ring in ${msUntilFiveMinsBefore / 1000} seconds`);
                            pendingTriggerTimeouts[call.id] = setTimeout(() => {
                                alertedCallIds.add(call.id);
                                showAlarmModal(call);
                                delete pendingTriggerTimeouts[call.id];
                            }, msUntilFiveMinsBefore);
                        }
                    }
                }
            }
        }
    } catch (e) {
        console.error("Error polling upcoming calls", e);
    }
}

function showAlarmModal(call) {
    document.getElementById('alarmStudy').textContent = call.study_name || '-';
    document.getElementById('alarmCensus').textContent = call.census || '-';
    document.getElementById('alarmCity').textContent = call.city || '-';
    document.getElementById('alarmPhone').textContent = call.phone_number || '-';
    document.getElementById('alarmName').textContent = call.person_name || '-';

    // Play sound
    const audio = document.getElementById('alarmAudio');
    if (audio) {
        audio.play().catch(e => console.log('Audio autoplay prevented by browser', e));
    }

    document.getElementById('alarmModal').style.display = 'block';
}

function closeAlarmModal() {
    document.getElementById('alarmModal').style.display = 'none';
    const audio = document.getElementById('alarmAudio');
    if (audio) {
        audio.pause();
        audio.currentTime = 0; // Reset to beginning
    }
}

// Start polling every 10 minutes (600000 ms), ONLY for agents and auxiliaries
function initAlarmPolling() {
    if (currentUserRole && (currentUserRole === 'agent' || currentUserRole === 'auxiliar')) {
        setTimeout(() => {
            pollUpcomingCalls();
            // Poll every 10 minutes. Since the backend returns calls up to 12 minutes away, 
            // the frontend will calculate and schedule the exact 5-min mark.
            alarmPollingInterval = setInterval(pollUpcomingCalls, 300000); // Poll every 5 minutes
        }, 5000);
    }
}

// Polling is now explicitly started after successful authentication in DOMContentLoaded.

// WhatsApp Integration
function openWhatsAppChat(fieldId = 'whatsappNumber') {
    const phoneNumberField = document.getElementById(fieldId);
    const personNameField = document.getElementById('personName');
    
    if (!phoneNumberField) return;
    
    let phoneNumber = phoneNumberField.value.trim();
    const personName = personNameField ? personNameField.value.trim() : 'Cliente';
    const agentName = currentUserName || 'Encuestador';

    if (!phoneNumber) {
        alert("Por favor, ingrese un número de teléfono.");
        return;
    }

    // Handle Excel ".0" suffix if present
    if (phoneNumber.endsWith('.0')) {
        phoneNumber = phoneNumber.slice(0, -2);
    }

    // Clean phone number (remove non-digits)
    phoneNumber = phoneNumber.replace(/\D/g, '');

    // Format for Colombia (prefix 57 if missing)
    if (phoneNumber.length === 10 && phoneNumber.startsWith('3')) {
        phoneNumber = '57' + phoneNumber;
    }

    if (phoneNumber.length < 10) {
        alert("El número de teléfono parece inválido.");
        return;
    }

    const greeting = `Hola, Sr@ ${personName} mi nombre es ${agentName}, soy la persona que el dia de hoy le va hacer la encuesta, podriamos hacer la encuesta en este momento?`;
    const encodedMessage = encodeURIComponent(greeting);
    const waUrl = `https://wa.me/${phoneNumber}?text=${encodedMessage}`;

    window.open(waUrl, '_blank');
}

/**
 * Copies the value of a field to the clipboard with visual feedback.
 * @param {string} fieldId - The ID of the input field to copy from.
 * @param {Event} event - The click event.
 */
function copyToClipboard(fieldId, event) {
    const field = document.getElementById(fieldId);
    if (!field || !field.value) {
        console.warn(`Field ${fieldId} not found or empty.`);
        return;
    }

    let textToCopy = field.value.trim();

    // Clean common Excel artifacts if present
    if (textToCopy.endsWith('.0')) {
        textToCopy = textToCopy.slice(0, -2);
    }

    // Clean non-digits for cleaner copying if desired, but here we just copy as is (trimmed)
    // textToCopy = textToCopy.replace(/\D/g, ''); 

    navigator.clipboard.writeText(textToCopy).then(() => {
        // Find the button (currentTarget is reliable if onclick is on button, else closest)
        let btn = event.currentTarget;
        if (!btn || !btn.classList.contains('btn-copy')) {
            btn = event.target.closest('.btn-copy');
        }
        
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                const originalClass = icon.className;
                icon.className = 'fas fa-check';
                btn.style.color = '#22c55e';
                btn.style.borderColor = '#22c55e';

                setTimeout(() => {
                    icon.className = originalClass;
                    btn.style.color = '';
                    btn.style.borderColor = '';
                }, 2000);
            }
        }
    }).catch(err => {
        console.error('Error al copiar al portapapeles:', err);
        alert("No se pudo copiar el número automáticamente.");
    });
}

// --- IMPORT FROM OTHER STUDY LOGIC ---
let importList = [];

function openImportModal() {
    const studySelect = document.getElementById('studySelect');
    const targetStudyName = studySelect.options[studySelect.selectedIndex].text;
    
    if (!studySelect.value) {
        alert("Debe seleccionar un estudio activo primero.");
        return;
    }

    document.getElementById('targetStudyLabel').textContent = targetStudyName;
    document.getElementById('importExternalModal').style.display = 'flex';
    document.getElementById('importSearchResults').innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center; color: #64748b;">Seleccione un estudio origen y use el buscador para encontrar personas.</td></tr>';
    document.getElementById('importSearchInput').value = '';
    
    populateImportStudies(); // Fetch all studies for source selection
    
    importList = [];
    updateImportListUI();
}

async function populateImportStudies() {
    const sel = document.getElementById('importSourceStudy');
    sel.innerHTML = '<option value="">Cargando estudios...</option>';
    
    try {
        const res = await fetch('/studies', { headers }); // Assuming /studies returns all
        const data = await res.json();
        
        sel.innerHTML = '<option value="">-- Seleccione un estudio --</option>';
        // Sort studies so newer or active ones appear first? For now just as is.
        data.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = `${s.is_active ? '✅' : '📁'} ${s.code} - ${s.name}`;
            sel.appendChild(opt);
        });
        
        sel.onchange = () => {
            searchExternalPerson(); // Trigger search when study changes
        };
    } catch (e) {
        console.error(e);
        sel.innerHTML = '<option value="">Error al cargar estudios</option>';
    }
}

function closeImportModal() {
    document.getElementById('importExternalModal').style.display = 'none';
}

async function searchExternalPerson() {
    const studySelect = document.getElementById('studySelect');
    const targetStudyId = studySelect.value;
    const sourceStudyId = document.getElementById('importSourceStudy').value;
    const query = document.getElementById('importSearchInput').value.trim();
    
    if (!sourceStudyId && !query) {
        // Don't search if nothing is selected/typed
        return;
    }

    const tbody = document.getElementById('importSearchResults');
    tbody.innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center;">Buscando...</td></tr>';

    try {
        let url = `/calls/search-external?`;
        if (query) url += `query=${encodeURIComponent(query)}&`;
        if (sourceStudyId) url += `source_study_id=${sourceStudyId}&`;
        if (targetStudyId) url += `target_study_id=${targetStudyId}`;
        
        const res = await fetch(url, { headers });
        if (res.ok) {
            const data = await res.json();
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center; color: #ef4444;">No se encontraron personas con ese criterio.</td></tr>';
                return;
            }

            tbody.innerHTML = '';
            data.forEach(p => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #f1f5f9';
                tr.style.color = '#334155'; // Fixed text color (was too light)
                tr.innerHTML = `
                    <td style="padding: 0.75rem;">${p.person_name || 'Sin Nombre'}</td>
                    <td style="padding: 0.75rem;">${p.phone_number}</td>
                    <td style="padding: 0.75rem;">${p.person_cc || 'N/A'}</td>
                    <td style="padding: 0.75rem;">${p.study_name}</td>
                    <td style="padding: 0.75rem;">
                        <button onclick='addToImportList(${JSON.stringify(p).replace(/'/g, "&apos;")})' style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-weight: 500;">Seleccionar</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center; color: #ef4444;">Error de conexión.</td></tr>';
    }
}

function addToImportList(person) {
    if (importList.find(p => p.id === person.id)) {
        alert("Esta persona ya está en la lista.");
        return;
    }
    importList.push({
        ...person,
        new_code: '',
        implantation_date: '',
        collection_date: ''
    });
    updateImportListUI();
}

function updateImportListUI() {
    const container = document.getElementById('importListContainer');
    const tbody = document.getElementById('importListTable');
    
    if (importList.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    tbody.innerHTML = '';
    importList.forEach((p, idx) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid #f1f5f9';
        tr.style.color = '#334155'; // Fixed text color
        tr.innerHTML = `
            <td style="padding: 0.5rem; font-weight: 500;">${p.person_name || p.phone_number}</td>
            <td style="padding: 0.5rem;"><input type="text" value="${p.new_code}" onchange="updateImportItem(${idx}, 'new_code', this.value)" style="width: 80px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px;"></td>
            <td style="padding: 0.5rem;"><input type="text" value="${p.implantation_date}" onchange="updateImportItem(${idx}, 'implantation_date', this.value)" placeholder="DD/MM" style="width: 80px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px;"></td>
            <td style="padding: 0.5rem;"><input type="text" value="${p.collection_date}" onchange="updateImportItem(${idx}, 'collection_date', this.value)" placeholder="DD/MM" style="width: 80px; padding: 4px; border: 1px solid #cbd5e1; border-radius: 4px;"></td>
            <td style="padding: 0.5rem;"><button onclick="removeFromImportList(${p.id})" style="color: #ef4444; background: none; border: none; cursor: pointer; font-size: 1.1rem;"><i class="fas fa-trash"></i></button></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateImportItem(idx, field, value) {
    importList[idx][field] = value;
}

function removeFromImportList(id) {
    importList = importList.filter(p => p.id !== id);
    updateImportListUI();
}

async function confirmImport() {
    if (importList.length === 0) return;

    const studyId = document.getElementById('studySelect').value;
    if (!studyId) {
        alert("Debe seleccionar un estudio activo primero.");
        return;
    }

    // Validate inputs
    for (const p of importList) {
        if (!p.new_code || !p.collection_date || !p.implantation_date) {
            alert(`Debe completar Código, Fecha Implante y Fecha Recogida para ${p.person_name || p.phone_number}`);
            return;
        }
    }

    // Confirmation message with details
    let msg = `¿Está seguro de importar ${importList.length} personas al estudio actual?\n\n`;
    importList.forEach(p => {
        msg += `- ${p.person_name || p.phone_number} (Código: ${p.new_code}, Fecha: ${p.collection_date})\n`;
    });

    if (!confirm(msg)) return;

    try {
        for (const p of importList) {
            const res = await fetch('/calls/import-external', {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    call_id: p.id,
                    target_study_id: parseInt(studyId),
                    new_code: p.new_code,
                    implantation_date: p.implantation_date,
                    collection_date: p.collection_date
                })
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Error al importar ${p.person_name}: ${err.detail || 'Error desconocido'}`);
            }
        }

        alert("Importación completada exitosamente.");
        closeImportModal();
        loadStudyData(studyId); // Refresh grid
    } catch (e) {
        console.error(e);
        alert("Error de red durante la importación.");
    }
}

// --- FILTERS MODULE JS ---
let currentFilterGroupId = null;
let currentFilterLeads = [];
let pendingFilterUploadData = [];

function showFiltersManager() {
    document.getElementById('filterManagerModal').style.display = 'flex';
    loadFilterGroups();
}

function closeFiltersManager() {
    document.getElementById('filterManagerModal').style.display = 'none';
}

async function loadFilterGroups() {
    const res = await fetch('/filters/groups', { headers });
    if (res.ok) {
        const groups = await res.json();
        const list = document.getElementById('filterGroupsList');
        list.innerHTML = groups.map(g => `
            <div onclick="selectFilterGroup(${g.id}, '${g.name}')" 
                 style="padding: 0.8rem; background: ${currentFilterGroupId == g.id ? '#eef2ff' : '#f8fafc'}; 
                        border: 1px solid ${currentFilterGroupId == g.id ? '#6366f1' : '#e2e8f0'}; 
                        border-radius: 6px; cursor: pointer; transition: 0.2s;">
                <div style="font-weight: bold; color: #1e293b;">${g.name}</div>
                <div style="font-size: 0.75rem; color: #64748b;">ID: ${g.id} - ${new Date(g.created_at).toLocaleDateString()}</div>
            </div>
        `).join('');
    }
}

async function selectFilterGroup(id, name) {
    currentFilterGroupId = id;
    document.getElementById('currentFilterName').innerText = `Filtro: ${name}`;
    document.getElementById('filterDetailsPlaceholder').style.display = 'none';
    document.getElementById('filterLeadsView').style.display = 'flex';
    loadFilterGroups(); // Refresh selection visual
    loadFilterLeads(id);
}

async function loadFilterLeads(id) {
    const res = await fetch(`/filters/groups/${id}/leads`, { headers });
    if (res.ok) {
        const leads = await res.json();
        const tbody = document.getElementById('filterLeadsTableBody');
        tbody.innerHTML = leads.map(l => `
            <tr style="border-bottom: 1px solid #f1f5f9;">
                <td style="padding: 0.8rem; font-weight: 500;">${l.phone_number}</td>
                <td style="padding: 0.8rem;">${l.person_name || '-'}</td>
                <td style="padding: 0.8rem;">${l.city || '-'}</td>
                <td style="padding: 0.8rem;">${l.interviewer_name || '-'}</td>
                <td style="padding: 0.8rem;">${l.recruiter_name || '-'}</td>
                <td style="padding: 0.8rem;">
                    <span style="padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
                        background: ${l.status === 'qualified' ? '#dcfce7' : l.status === 'rejected' ? '#fee2e2' : '#f1f5f9'};
                        color: ${l.status === 'qualified' ? '#166534' : l.status === 'rejected' ? '#991b1b' : '#475569'};">
                        ${l.status === 'qualified' ? 'CALIFICA' : l.status === 'rejected' ? 'NO CALIFICA' : 'PENDIENTE'}
                    </span>
                </td>
                <td style="padding: 0.8rem; color: #64748b;">${l.assigned_user_id ? 'Asignado' : 'Sin asignar'}</td>
            </tr>
        `).join('');
    }
}

function showCreateFilter() {
    document.getElementById('filterCreateModal').style.display = 'flex';
}

async function submitCreateFilter() {
    const name = document.getElementById('newFilterGroupName').value;
    if (!name) return alert("Ingrese un nombre");
    
    const res = await fetch('/filters/groups', {
        method: 'POST',
        headers,
        body: JSON.stringify({ name })
    });
    
    if (res.ok) {
        document.getElementById('filterCreateModal').style.display = 'none';
        document.getElementById('newFilterGroupName').value = '';
        loadFilterGroups();
    }
}

function showFilterUpload() {
    document.getElementById('filterUploadModal').style.display = 'flex';
    document.getElementById('filterPasteArea').value = '';
    document.getElementById('filterPreviewContainer').style.display = 'none';
    pendingFilterUploadData = [];
}

async function handleFilterPasteData() {
    const text = document.getElementById('filterPasteArea').value;
    if (!text) return;
    
    const rows = text.trim().split('\n').map(r => r.split('\t'));
    if (rows.length < 2) return;
    
    const headers_row = rows[0].map(h => h.trim().toLowerCase());
    const data = rows.slice(1);
    
    // Attempt mapping
    const colIdx = {
        phone: headers_row.findIndex(h => h.includes('tel') || h.includes('cel') || h.includes('llamada')),
        name: headers_row.findIndex(h => h.includes('nom') || h.includes('person')),
        city: headers_row.findIndex(h => h.includes('ciu') || h.includes('mun')),
        interviewer: headers_row.findIndex(h => h.includes('encue') || h.includes('interv')),
        recruiter: headers_row.findIndex(h => h.includes('reclu'))
    };
    
    if (colIdx.phone === -1) {
        alert("No se encontró columna de teléfono");
        return;
    }

    const leads = data.map(row => {
        const lead = {
            phone_number: row[colIdx.phone],
            person_name: colIdx.name !== -1 ? row[colIdx.name] : '',
            city: colIdx.city !== -1 ? row[colIdx.city] : '',
            interviewer_name: colIdx.interviewer !== -1 ? row[colIdx.interviewer] : '',
            recruiter_name: colIdx.recruiter !== -1 ? row[colIdx.recruiter] : '',
            survey_data: {}
        };
        
        // Put everything else in survey_data
        headers_row.forEach((h, i) => {
            if (!Object.values(colIdx).includes(i)) {
                lead.survey_data[h] = row[i];
            }
        });
        return lead;
    });

    // Check duplicates against backend
    const phoneNumbers = leads.map(l => l.phone_number);
    const dupRes = await fetch(`/filters/check-duplicates?group_id=${currentFilterGroupId}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(phoneNumbers)
    });
    
    let duplicates = { in_group: [], in_global: [] };
    if (dupRes.ok) duplicates = await dupRes.json();
    
    pendingFilterUploadData = leads;
    
    // Show Preview
    const container = document.getElementById('filterPreviewContainer');
    container.style.display = 'flex';
    
    const thead = document.getElementById('filterPreviewThead');
    thead.innerHTML = `<tr>
        <th style="padding: 0.5rem; border:1px solid #ddd;">Validación</th>
        <th style="padding: 0.5rem; border:1px solid #ddd;">Teléfono</th>
        <th style="padding: 0.5rem; border:1px solid #ddd;">Nombre</th>
        <th style="padding: 0.5rem; border:1px solid #ddd;">Reclutador</th>
    </tr>`;
    
    const tbody = document.getElementById('filterPreviewTbody');
    tbody.innerHTML = leads.slice(0, 50).map(l => {
        const isDupGroup = duplicates.in_group.includes(l.phone_number);
        const isDupGlobal = duplicates.in_global.includes(l.phone_number);
        const statusIcon = isDupGlobal ? '❌ GLOBAL' : (isDupGroup ? '⚠️ REPETIDO' : '✅ OK');
        const color = isDupGlobal ? '#ef4444' : (isDupGroup ? '#f59e0b' : '#22c55e');
        
        return `
            <tr>
                <td style="padding: 0.5rem; border:1px solid #ddd; color: ${color}; font-weight: bold;">${statusIcon}</td>
                <td style="padding: 0.5rem; border:1px solid #ddd;">${l.phone_number}</td>
                <td style="padding: 0.5rem; border:1px solid #ddd;">${l.person_name}</td>
                <td style="padding: 0.5rem; border:1px solid #ddd;">${l.recruiter_name}</td>
            </tr>
        `;
    }).join('');
    
    const btn = document.getElementById('btnFinalFilterUpload');
    btn.disabled = false;
    btn.style.opacity = '1';
}

async function submitFilterUpload() {
    if (!pendingFilterUploadData.length) return;
    
    const res = await fetch('/filters/upload', {
        method: 'POST',
        headers,
        body: JSON.stringify({
            group_id: currentFilterGroupId,
            leads: pendingFilterUploadData
        })
    });
    
    if (res.ok) {
        alert("Leads cargados exitosamente");
        document.getElementById('filterUploadModal').style.display = 'none';
        loadFilterLeads(currentFilterGroupId);
    }
}

async function showFilterAssign() {
    const res = await fetch(`/filters/groups/${currentFilterGroupId}/leads`, { headers });
    if (res.ok) {
        const leads = await res.json();
        const available = leads.filter(l => !l.assigned_user_id).length;
        document.getElementById('filterAvailableCount').innerText = available;
        document.getElementById('filterAssignModal').style.display = 'flex';
        
        // Load agents if not loaded
        loadAgentsIntoSelect('filterAssignUser');
    }
}

async function loadAgentsIntoSelect(id) {
    const res = await fetch('/reports/active-agents', { headers }); // Re-using existing agent list endpoint
    if (res.ok) {
        const agents = await res.json();
        const select = document.getElementById(id);
        const currentId = select.value;
        select.innerHTML = agents.map(a => `<option value="${a.id}">${a.name} (${a.role})</option>`).join('');
        if (currentId) select.value = currentId;
    }
}

async function submitFilterAssign() {
    const userId = document.getElementById('filterAssignUser').value;
    const count = document.getElementById('filterAssignCount').value;
    
    const res = await fetch(`/filters/leads/assign?group_id=${currentFilterGroupId}&user_id=${userId}&count=${count}`, {
        method: 'POST',
        headers
    });
    
    if (res.ok) {
        alert("Leads asignados correctamente");
        document.getElementById('filterAssignModal').style.display = 'none';
        loadFilterLeads(currentFilterGroupId);
    }
}

// AGENT WORKFLOW
function showFilterCalling() {
    document.getElementById('superuserLanding').style.display = 'none';
    document.getElementById('crmInterface').style.display = 'none';
    document.getElementById('filterCallingView').style.display = 'flex';
    loadAgentFilterGroups();
}

function backToCRM() {
    document.getElementById('filterCallingView').style.display = 'none';
    if (currentUserRole === 'superuser' || currentUserRole === 'coordinator' || currentUserRole === 'auxiliar') {
        document.getElementById('superuserLanding').style.display = 'flex';
    } else {
        document.getElementById('crmInterface').style.display = 'grid';
    }
}

async function loadAgentFilterGroups() {
    const res = await fetch('/filters/groups', { headers });
    if (res.ok) {
        const groups = await res.json();
        const select = document.getElementById('filterGroupSelectAgent');
        select.innerHTML = '<option value="">Seleccione Listado...</option>' + 
            groups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
    }
}

async function loadAgentFilterLeads() {
    const groupId = document.getElementById('filterGroupSelectAgent').value;
    if (!groupId) return;
    
    const res = await fetch(`/filters/groups/${groupId}/leads`, { headers });
    if (res.ok) {
        const leads = await res.json();
        const list = document.getElementById('filterAgentLeadsList');
        // Filter out those already finished in local if preferred, but usually backend covers it
        list.innerHTML = leads.map(l => `
            <div onclick="showFilterLeadDetail(${l.id})" 
                 style="padding: 1rem; background: white; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; transition: 0.2s; 
                        border-left: 6px solid ${l.status === 'qualified' ? '#22c55e' : l.status === 'rejected' ? '#ef4444' : '#6366f1'};">
                <div style="font-weight: bold;">${l.person_name || l.phone_number}</div>
                <div style="font-size: 0.8rem; color: #64748b;">${l.phone_number} - ${l.city || ''}</div>
                <div style="font-size: 0.7rem; margin-top: 4px; font-weight: bold; color: ${l.status === 'pending' ? '#6366f1' : '#475569'};">
                    ${l.status.toUpperCase()}
                </div>
            </div>
        `).join('');
        
        currentFilterLeads = leads;
    }
}

let activeFilterLead = null;

function showFilterLeadDetail(leadId) {
    const lead = currentFilterLeads.find(l => l.id === leadId);
    if (!lead) return;
    activeFilterLead = lead;
    
    document.getElementById('filterLeadDetail').style.display = 'flex';
    document.getElementById('detFilterName').innerText = `Nombre: ${lead.person_name || 'Sin nombre'}`;
    document.getElementById('detFilterPhone').innerText = lead.phone_number;
    document.getElementById('detFilterCity').innerText = lead.city || '-';
    document.getElementById('detFilterRecruiter').innerText = lead.recruiter_name || '-';
    
    const surveyDiv = document.getElementById('detFilterSurvey');
    try {
        const data = JSON.parse(lead.survey_data || '{}');
        surveyDiv.innerHTML = Object.entries(data).map(([k, v]) => `
            <div style="background: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #f1f5f9;">
                <span style="font-weight: bold; font-size: 0.8rem; color: #64748b; text-transform: capitalize;">${k}:</span>
                <span style="font-size: 0.9rem;">${v}</span>
            </div>
        `).join('');
    } catch (e) { surveyDiv.innerHTML = 'Error al cargar encuesta'; }
}

async function updateFilterStatus(status) {
    if (!activeFilterLead) return;
    if (!confirm(`¿Marcar este lead como ${status.toUpperCase()}?`)) return;
    
    const res = await fetch(`/filters/leads/${activeFilterLead.id}/status?status=${status}`, {
        method: 'PUT',
        headers
    });
    
    if (res.ok) {
        document.getElementById('filterLeadDetail').style.display = 'none';
        loadAgentFilterLeads(); 
    }
}

// UI Helpers for Dynamic Fields
function toggleShampooOtros(val) {
    const input = document.getElementById('shampooQtyOtros');
    if (val === 'Otros') {
        input.style.display = 'block';
        input.focus();
    } else {
        input.style.display = 'none';
        input.value = '';
    }
}
// --- BONOS ESTUDIOS LOGIC ---
let currentBonoCalls = [];

async function showBonosEstudios() {
    console.log("showBonosEstudios called. Role:", currentUserRole);
    const modal = document.getElementById('bonosEstudiosModal');
    if (!modal) {
        console.error("Modal 'bonosEstudiosModal' not found in DOM");
        return;
    }
    modal.style.display = 'flex';
    
    // Load study list (All studies, including inactive ones)
    try {
        const res = await fetch('/studies', { headers });
        if (res.ok) {
            const studies = await res.json();
            const sel = document.getElementById('bonoStudySelect');
            
            // Destroy existing TomSelect instance if it exists
            if (sel.tomselect) sel.tomselect.destroy();

            sel.innerHTML = '<option value="">Seleccione o escriba un estudio...</option>';
            
            // Sort: Active first, then inactive. Alphabetical within groups.
            const sorted = studies.sort((a,b) => {
                if (a.is_active === b.is_active) {
                    return a.name.localeCompare(b.name);
                }
                return a.is_active ? -1 : 1;
            });

            sorted.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.id;
                opt.textContent = s.is_active ? s.name : `${s.name} (Archivado)`;
                sel.appendChild(opt);
            });

            // Initialize TomSelect for searchability
            new TomSelect(sel, {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                },
                placeholder: "Escriba para buscar estudio...",
                allowEmptyOption: true
            });
        }
    } catch (e) {
        console.error("Error loading studies for bonos", e);
    }
}

function closeBonosEstudios() {
    document.getElementById('bonosEstudiosModal').style.display = 'none';
}

async function loadBonoStudyData() {
    const studyId = document.getElementById('bonoStudySelect').value;
    const tbody = document.getElementById('bonoCallsTableBody');
    const btnDown = document.getElementById('btnDownloadBonoExcel');
    const alertDiv = document.getElementById('bonoClosingAlert');
    const infoDiv = document.getElementById('bonoClosingInfo');
    const citySummaryDiv = document.getElementById('bonoCitySummary');
    const studyCodeInput = document.getElementById('bonoStudyCode');
    
    if (!studyId) {
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center; color: #64748b;">Seleccione un estudio para ver los registros.</td></tr>';
        btnDown.disabled = true;
        btnDown.style.opacity = '0.5';
        alertDiv.style.display = 'none';
        infoDiv.textContent = '';
        citySummaryDiv.innerHTML = '';
        studyCodeInput.value = '';
        return;
    }

    try {
        const res = await fetch(`/studies/${studyId}/bonos-data`, { headers });
        if (res.ok) {
            const data = await res.json();
            currentBonoCalls = data.calls;
            
            // Render table
            if (currentBonoCalls.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="padding: 2rem; text-align: center; color: #64748b;">No hay registros efectivos o por desempeño en este estudio.</td></tr>';
                btnDown.disabled = true;
                btnDown.style.opacity = '0.5';
            } else {
                tbody.innerHTML = currentBonoCalls.map((c, i) => `
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 0.8rem;">${i + 1}</td>
                        <td style="padding: 0.8rem;">${c.phone}</td>
                        <td style="padding: 0.8rem;">${c.name || '---'}</td>
                        <td style="padding: 0.8rem;">${c.city || '---'}</td>
                        <td style="padding: 0.8rem;">
                            <span style="padding: 2px 8px; border-radius:12px; font-size: 0.8rem; background: ${c.status === 'managed' ? '#dcfce7' : '#fee2e2'}; color: ${c.status === 'managed' ? '#166534' : '#991b1b'};">
                                ${translateStatus(c.status)}
                            </span>
                        </td>
                    </tr>
                `).join('');
                btnDown.disabled = false;
                btnDown.style.opacity = '1';

                // City Summary Calculation
                const cityCounts = {};
                currentBonoCalls.forEach(c => {
                    const city = c.city ? c.city.toUpperCase().trim() : 'SIN CIUDAD';
                    cityCounts[city] = (cityCounts[city] || 0) + 1;
                });

                citySummaryDiv.innerHTML = Object.entries(cityCounts)
                    .sort((a, b) => b[1] - a[1]) // Sort by count descending
                    .map(([city, count]) => `
                        <div style="background: #eff6ff; color: #1e40af; padding: 4px 10px; border-radius: 20px; border: 1px solid #bfdbfe; font-weight: 600;">
                            ${city}: ${count}
                        </div>
                    `).join('') + `
                        <div style="background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 20px; border: 1px solid #cbd5e1; font-weight: bold; margin-left: auto;">
                            TOTAL: ${currentBonoCalls.length}
                        </div>
                    `;
            }
            
            // Check Closing Date
            if (data.closing_date) {
                const closingDate = new Date(data.closing_date);
                const today = new Date();
                
                infoDiv.textContent = `Fecha de cierre: ${closingDate.toLocaleDateString()}`;
                
                // Alert if it's today
                if (closingDate.toDateString() === today.toDateString()) {
                    alertDiv.style.display = 'block';
                } else {
                    alertDiv.style.display = 'none';
                }
            } else {
                infoDiv.textContent = 'Sin fecha de cierre configurada';
                alertDiv.style.display = 'none';
            }

        }
    } catch (e) {
        console.error("Error loading bono data", e);
        alert("Error al cargar datos del estudio");
    }
}

function showRescheduleModal() {
    const studyId = document.getElementById('bonoStudySelect').value;
    if (!studyId) {
        alert("Primero seleccione un estudio");
        return;
    }
    document.getElementById('rescheduleModal').style.display = 'flex';
}

async function submitReschedule() {
    const studyId = document.getElementById('bonoStudySelect').value;
    const newDate = document.getElementById('newClosingDate').value;
    
    if (!newDate) {
        alert("Seleccione una fecha");
        return;
    }
    
    try {
        // Convert local date to ISO midnight
        const isoDate = new Date(newDate + "T00:00:00").toISOString();
        
        const res = await fetch(`/studies/${studyId}/reschedule`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ closing_date: isoDate })
        });
        
        if (res.ok) {
            alert("Fecha de cierre actualizada exitosamente");
            document.getElementById('rescheduleModal').style.display = 'none';
            loadBonoStudyData(); // Refresh info
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "No se pudo actualizar la fecha"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}

async function finalizeAndDownloadBonos() {
    const studyId = document.getElementById('bonoStudySelect').value;
    const studyCode = document.getElementById('bonoStudyCode').value.trim();
    const auxName = document.getElementById('bonoAuxiliarName').value.trim();
    const bonoValueSel = document.getElementById('bonoValueSelect').value;
    const bonoValueOther = document.getElementById('bonoValueOther').value.trim();
    const studyStage = document.getElementById('bonoStageSelect').value;
    const studyDateText = document.getElementById('bonoStudyDate').value.trim();
    const archive = document.getElementById('bonoArchiveStudy').checked;
    
    // Determine final bonus amount
    let finalBonoValue = bonoValueSel === 'otro' ? bonoValueOther : bonoValueSel;
    
    if (!studyCode) {
        alert("Por favor ingrese el Código del estudio");
        return;
    }
    if (!auxName) {
        alert("Por favor ingrese el nombre del Auxiliar");
        return;
    }
    if (!finalBonoValue) {
        alert("Por favor seleccione o ingrese el valor del bono");
        return;
    }
    if (!studyStage) {
        alert("Por favor seleccione la etapa del estudio");
        return;
    }
    if (!studyDateText) {
        alert("Por favor ingrese la fecha del estudio");
        return;
    }
    
    if (!confirm(`¿Desea validar ${currentBonoCalls.length} registros con el bono de $${parseInt(finalBonoValue).toLocaleString()} y descargar el reporte?`)) return;
    
    try {
        const res = await fetch(`/studies/${studyId}/finalize-bonos`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                codigo_estudio: studyCode,
                auxiliar_name: auxName,
                bonus_amount: parseInt(finalBonoValue),
                etapa: studyStage,
                fecha_estudio: studyDateText,
                archive_study: archive
            })
        });
        
        if (res.ok) {
            alert("Datos guardados. Iniciando descarga del formato oficial...");
            
            // Handle binary response
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const studyName = document.getElementById('bonoStudySelect').options[document.getElementById('bonoStudySelect').selectedIndex].text;
            a.download = `Reporte_Bonos_${studyName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            if (archive) {
                alert("El estudio ha sido archivado.");
                closeBonosEstudios();
                loadStudies(); // Global refresh
            }
        } else {
            const err = await res.json();
            alert("Error al finalizar bonos: " + (err.detail || "Error desconocido"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión al finalizar");
    }
}

function toggleBonoValueOther(val) {
    const otherInput = document.getElementById('bonoValueOther');
    if (otherInput) {
        otherInput.style.display = val === 'otro' ? 'block' : 'none';
        if (val === 'otro') otherInput.focus();
    }
}
