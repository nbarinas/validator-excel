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

const statusMap = {
    'pending': 'Pendiente',
    'management': 'Gestionando',
    'scheduled': 'Agendado',
    'done': 'Terminado',
    'closed': 'Cerrado',
    // New caída options
    'caida_desempeno': 'Caída por Desempeño',
    'caida_logistica': 'Caída Logística',
    'caida_desempeno_campo': 'Caída Desempeño Campo',
    'caida_logistico_campo': 'Caída Logístico Campo',
    // Legacy caídas mapping
    'caidas': 'Caída',
    'caida': 'Caída',
    // En campo statuses
    'en_campo': 'En Campo',
    'en campo': 'En Campo',
    'efectiva_campo': 'Efectiva en Campo',
    'managed': 'Gestionado'
};

const translateStatus = (s) => statusMap[s] || s;

// Init
document.addEventListener('DOMContentLoaded', async () => {
    // Load User Info
    try {
        const uRes = await fetch('/users/me', { headers });
        if (uRes.ok) {
            const user = await uRes.json();
            currentUserRole = user.role;
            const ui = document.getElementById('userInfoDisplay');
            if (ui) {
                const name = user.full_name || user.username;
                ui.innerHTML = `<i class="fas fa-user-circle" style="margin-right: 8px;"></i> ${name} <span style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 4px; margin-left: 10px; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.4);">${user.role.toUpperCase()}</span>`;
            }

            if (currentUserRole === 'superuser') {
                // Show Landing, Hide CRM
                document.getElementById('superuserLanding').style.display = 'block';
                document.getElementById('crmInterface').style.display = 'none';
                // Ensure button is visible if they enter
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = 'inline-block';
            } else {
                // Normal User
                // Hide Create Study Button
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = 'none';
                loadStudies();
            }

            // Auxiliar Role Handling
            if (currentUserRole === 'auxiliar') {
                // Auxiliar can see active calls and manage them, similar to agent but maybe broader visibility?
                // Requirement: "El rol auxiliar puede ver las llamadas activas"
                // They should see the CRM interface.
                document.getElementById('superuserLanding').style.display = 'none';
                document.getElementById('crmInterface').style.display = 'grid';
            }

            // Ensure search is visible for EVERYONE
            const search = document.getElementById('searchPanel');
            if (search) search.style.display = 'block';

            // AUTOMATICALLY LOAD ALL PENDING CALLS
            loadStudyData(null); // Null = all pending from open studies

            // Show Excel Button for Superuser/Auxiliar
            if (currentUserRole === 'superuser' || currentUserRole === 'auxiliar') {
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
function enterCRM() {
    document.getElementById('superuserLanding').style.display = 'none';
    document.getElementById('crmInterface').style.display = 'grid'; // Restore grid
    loadStudies();
    loadStudyData(null); // Load global calls when entering
    loadAgents(); // Load users for assignment
}

function showUploadModal() {
    document.getElementById('uploadModal').style.display = 'flex';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

async function uploadCalls() {
    const fileInput = document.getElementById('uploadFile');
    const studyName = document.getElementById('uploadStudyName').value;
    const studyType = document.getElementById('uploadStudyType').value;
    const studyStage = document.getElementById('uploadStudyStage').value;

    if (!fileInput.files[0]) {
        alert("Selecciona un archivo Excel");
        return;
    }

    if (!studyName) {
        alert("Escribe un nombre para el nuevo estudio");
        return;
    }

    if (!studyType || studyType === "") {
        alert("Por favor selecciona el Tipo de Estudio (Validación o Fatiga)");
        return;
    }

    if (!studyStage || studyStage === "") {
        alert("Por favor selecciona la Etapa (R)");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('study_name', studyName);
    formData.append('study_type', studyType);
    formData.append('study_stage', studyStage);

    alert("Cargando base de datos... Esto puede tomar unos segundos.");

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
            alert(`Carga exitosa: ${data.count} registros creados en estudio '${data.study_name}'.`);
            closeUploadModal();
            enterCRM();
        } else {
            const err = await res.json();
            alert("Error: " + err.detail);
        }
    } catch (e) {
        console.error(e);
        alert("Error de red");
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

async function loadStudies() {
    const res = await fetch('/studies', { headers });
    const studies = await res.json();
    const sel = document.getElementById('studySelect');
    sel.innerHTML = '<option value="">Seleccione Estudio...</option>';
    studies.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = `${s.code} - ${s.name}`;
        sel.appendChild(opt);
    });

    sel.addEventListener('change', () => {
        if (sel.value) {
            loadStudyData(sel.value);
        }
    });
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

['colFilterCity', 'colFilterStudy', 'colFilterDateStart', 'colFilterDateEnd'].forEach(id => {
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
    const cityTerm = document.getElementById('colFilterCity').value.toLowerCase().trim();
    const censusTerm = document.getElementById('colFilterCensus') ? document.getElementById('colFilterCensus').value.toLowerCase().trim() : '';
    const dateStart = document.getElementById('colFilterDateStart') ? document.getElementById('colFilterDateStart').value : '';
    const dateEnd = document.getElementById('colFilterDateEnd') ? document.getElementById('colFilterDateEnd').value : '';

    // New Filters
    const studyTerm = document.getElementById('colFilterStudy').value.toLowerCase().trim();
    // Agents & Status are now multi-selects handled by checking checkboxes in their containers

    // Helper to get checked values from a container
    const getMultiSelectValues = (containerId) => {
        const container = document.getElementById(containerId);
        if (!container) return [];
        return Array.from(container.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value.toLowerCase());
    };

    const selectedAgents = getMultiSelectValues('colFilterAgentContainer');
    const selectedStatuses = getMultiSelectValues('colFilterStatusContainer');

    // Helper Checks
    const checkPhone = (c) => !phoneTerm || (c.phone_number || '').toString().toLowerCase().includes(phoneTerm);
    const checkName = (c) => !nameTerm || (c.person_name || '').toString().toLowerCase().includes(nameTerm);
    const checkCensus = (c) => !censusTerm || (c.census || '').toString().toLowerCase().includes(censusTerm);
    const checkCity = (c) => !cityTerm || (c.city || '').toString().toLowerCase() === cityTerm;

    const checkDate = (c) => {
        if (!dateStart && !dateEnd) return true;

        // Resolve date
        // c.created_at is ISO in DB (YYYY-MM-DD...) usually
        // c.collection_date matches Excel upload. Might be YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY

        let dateStr = '';
        if (c.created_at) {
            dateStr = new Date(c.created_at).toISOString().split('T')[0];
        } else if (c.collection_date) {
            let raw = c.collection_date.toString().substring(0, 10).trim();
            // Try to detect DD/MM/YYYY
            if (raw.includes('/')) {
                const parts = raw.split('/');
                if (parts.length === 3) {
                    // Assume DD/MM/YYYY if year is last
                    if (parts[2].length === 4) {
                        dateStr = `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
                    } else if (parts[0].length === 4) {
                        // YYYY/MM/DD
                        dateStr = `${parts[0]}-${parts[1].padStart(2, '0')}-${parts[2].padStart(2, '0')}`;
                    }
                }
            } else if (raw.includes('-')) {
                // Check if it's DD-MM-YYYY (common in some locales) vs YYYY-MM-DD
                const parts = raw.split('-');
                if (parts.length === 3 && parts[0].length === 2 && parts[2].length === 4) {
                    // DD-MM-YYYY -> Convert to YYYY-MM-DD
                    dateStr = `${parts[2]}-${parts[1]}-${parts[0]}`;
                } else {
                    // Assume YYYY-MM-DD
                    dateStr = raw;
                }
            } else {
                dateStr = raw; // Fallback
            }
        }

        if (!dateStr) return false;

        if (dateStart && dateStr < dateStart) return false;
        if (dateEnd && dateStr > dateEnd) return false;

        return true;
    };

    // Selects
    const checkStudy = (c) => !studyTerm || (c.study_name || '').toString().toLowerCase() === studyTerm;

    const checkAgent = (c) => {
        if (selectedAgents.length === 0) return true; // If none checked, it implies ALL or nothing filtered? "Todos" logic. 
        // Based on UI, usually unchecked means "All" in this context? 
        // Wait, my updateButtonText says "Todos" if ALL checked or NONE checked.
        // Let's assume if NONE checked, we show ALL.

        const agentDisplay = c.agent_name || (c.agent_id ? `Agente ${c.agent_id}` : 'Sin Asignar');
        const val = agentDisplay.toLowerCase().trim();

        return selectedAgents.includes(val);
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
        checkStudy(c) && checkAgent(c) && checkStatus(c) && checkDate(c)
    );
    renderCallGrid(filteredCalls);





}

function resetFilters() {
    ['colFilterPhone', 'colFilterName', 'colFilterCity', 'colFilterStudy', 'colFilterCensus', 'colFilterDateStart', 'colFilterDateEnd'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    // Reset Multi-Selects
    ['colFilterAgentContainer', 'colFilterStatusContainer'].forEach(id => {
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

    // Restore sidebar only for superusers
    if (currentUserRole === 'superuser') {
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
        if (studyId) url += `?study_id=${studyId}`;

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

        // Populate City Dropdown
        populateSelectFilter('colFilterCity', allCalls.map(c => (c.city || '').trim()).filter(x => x));

        // Populate Study Dropdown
        populateSelectFilter('colFilterStudy', allCalls.map(c => (c.study_name || '').trim()).filter(x => x));

        // Populate Status Dropdown (Dynamic Multi-Select)
        const uniqueStatuses = [...new Set(allCalls.map(c => translateStatus(c.status || 'pending').trim()))].sort();
        createMultiSelect('colFilterStatusContainer', uniqueStatuses, applyColumnFilters);

        // Populate Agent Dropdown (Dynamic Multi-Select)
        const possibleAgents = allCalls.map(c => c.agent_name || (c.agent_id ? `Agente ${c.agent_id}` : 'Sin Asignar'));
        // Add current user if agent? No, list all agents in data.
        const uniqueAgents = [...new Set(possibleAgents)].filter(x => x).sort();

        createMultiSelect('colFilterAgentContainer', uniqueAgents, applyColumnFilters);


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

    calls.forEach(call => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.style.borderBottom = '1px solid #eee';
        tr.onmouseover = () => tr.style.background = '#f8f9fa';
        tr.onmouseout = () => tr.style.background = 'white';

        // Format appointment time if exists
        let alertTime = '-';
        if (call.appointment_time) {
            const dateObj = new Date(call.appointment_time);
            alertTime = `<span style="color:#d97706; font-weight:bold;">${dateObj.toLocaleDateString()} ${dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
        }

        tr.innerHTML = `
            <td onclick="event.stopPropagation()"><input type="checkbox" class="call-checkbox" value="${call.id}"></td>
            <td><i class="fas fa-phone"></i> ${call.phone_number}</td>
            <td style="font-size: 0.8rem; color: #555;">${call.collection_date || (call.created_at ? new Date(call.created_at).toLocaleDateString() : '-')}</td>
            <td>
                <span style="font-size:0.8rem; color:#666; font-weight:bold;">${call.study_name || '-'}</span>
                ${call.study_type ? `<br><span style="font-size:0.7rem; color:#1a73e8; font-weight:600;">${call.study_type.toUpperCase()}</span>` : ''}
                ${call.study_stage ? `<span style="font-size:0.7rem; color:#f59e0b; font-weight:600; margin-left:0.3rem;">[${call.study_stage}]</span>` : ''}
            </td>
            <td><span style="font-size:0.8rem; color:${call.agent_name ? '#4caf50' : '#f44336'}; font-weight:bold;">${call.agent_name || 'Sin Asignar'}</span></td>
            <td>${call.person_name || '-'}</td>
            <td>${call.city || '-'}</td>
            <td>${alertTime}</td>
            <!-- Old Obs Cell Removed -->
            <td><span style="background:${call.status === 'pending' ? '#fee2e2' : '#dcfce7'}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${translateStatus(call.status)}</span></td>
            
            <td>${call.census || '-'}</td>
            <td>${call.collection_time || call.initial_observation || '-'}</td>
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

    // Standard Info
    document.getElementById('phoneNumber').value = call.phone_number;
    document.getElementById('correctedPhone').value = call.corrected_phone || '';

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
    document.getElementById('apptTime').value = call.appointment_time || '';
    document.getElementById('apptTime').value = call.appointment_time || '';
    document.getElementById('extraPhone').value = call.extra_phone || '';

    // POPULATE CENSUS SECTION
    document.getElementById('censusId').value = call.census || '';
    document.getElementById('censusNSE').value = call.nse || '';
    document.getElementById('censusAge').value = call.age || '';
    document.getElementById('censusAgeRange').value = call.age_range || '';
    document.getElementById('censusNeighborhood').value = call.neighborhood || '';
    document.getElementById('censusAddress').value = call.address || '';
    document.getElementById('censusHousing').value = call.housing_description || '';
    document.getElementById('censusChildren').value = call.children_age || '';

    // WhatsApp field
    const whatsappField = document.getElementById('whatsappNumber');
    if (whatsappField) whatsappField.value = call.whatsapp || '';

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
    if (currentUserRole === 'superuser') {
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
        createBtn("Efectiva en Campo", "#22c55e", "efectiva_campo"); // Green
        createBtn("Caída Desempeño", "#ef4444", "caida_desempeno"); // Red
        createBtn("Caída Logística", "#ef4444", "caida_logistica"); // Red
        createBtn("Caída Desempeño Campo", "#ef4444", "caida_desempeno_campo"); // Red
        createBtn("Caída Logístico Campo", "#ef4444", "caida_logistico_campo"); // Red
        createBtn("Gestionado", "#22c55e", "managed"); // Green
        createBtn("Agendado", "#3b82f6", "scheduled"); // Blue
    }
    // AUXILIAR: En Campo and Efectiva options
    else if (currentUserRole === 'auxiliar') {
        createBtn("En Campo", "#3b82f6", "en_campo"); // Blue
        createBtn("Efectiva en Campo", "#22c55e", "efectiva_campo"); // Green
        createBtn("Caída Desempeño Campo", "#ef4444", "caida_desempeno_campo"); // Red
        createBtn("Caída Logístico Campo", "#ef4444", "caida_logistico_campo"); // Red
    }
    // AGENT: Standard Flow with new caída options
    else {
        createBtn("Gestionado", "#22c55e", "managed"); // Green
        createBtn("Agendado", "#3b82f6", "scheduled"); // Blue
        createBtn("Caída Desempeño", "#ef4444", "caida_desempeno"); // Red
        createBtn("Caída Logística", "#ef4444", "caida_logistica"); // Red
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
            const sel = document.getElementById('studySelect');
            if (sel.value) loadStudyData(sel.value);
            else loadStudyData(null);
            showGridView();
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
    if (currentUserRole !== 'superuser') return;
    try {
        const res = await fetch('/users', { headers });
        if (res.ok) {
            const users = await res.json();
            const sel = document.getElementById('agentSelect');
            const bulkSel = document.getElementById('bulkAgentSelect');

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

            // Show Bulk Actions
            document.getElementById('bulkActions').style.display = 'block';
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

    try {
        const res = await fetch(`/calls/${currentCallId}/assign`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ user_id: parseInt(userId) })
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Llamada asignada a: ${data.agent}`);
            // Return to grid automatically
            const sel = document.getElementById('studySelect');
            if (sel.value) loadStudyData(sel.value);
            else loadStudyData(null);
            showGridView();
        } else {
            alert("Error al asignar");
        }
    } catch (e) { console.error(e); }
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

    const ids = Array.from(checks).map(c => parseInt(c.value));

    try {
        const res = await fetch('/calls/assign-bulk', {
            method: 'PUT',
            headers,
            body: JSON.stringify({ call_ids: ids, user_id: parseInt(userId) })
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Asignadas ${data.count} llamadas exitosamente.`);
            // Refresh
            const sel = document.getElementById('studySelect');
            if (sel.value) loadStudyData(sel.value);
            else loadStudyData(null);
        } else {
            alert("Error en asignación masiva");
        }
    } catch (e) { console.error(e); }
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
    const whatsapp = document.getElementById('whatsappNumber').value;
    const extraPhone = document.getElementById('extraPhone').value;

    // Check if we are UPDATING an existing call
    if (currentCallId) {
        if (!phone) {
            alert("El número de celular es obligatorio.");
            return;
        }

        const body = {
            phone_number: phone,
            corrected_phone: corrected,
            person_cc: cc,
            whatsapp: whatsapp,
            extra_phone: extraPhone
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

async function loadObservations() {
    if (!currentCallId) return;
    try {
        const res = await fetch(`/calls/${currentCallId}/observations`, { headers });
        const obs = await res.json();
        const feed = document.getElementById('obsFeed');
        feed.innerHTML = '';

        obs.forEach(o => {
            const el = document.createElement('div');
            el.className = 'obs-item';
            // Date handling
            let dateStr = "Fecha desconocida";
            if (o.created_at) {
                const d = new Date(o.created_at);
                if (d.getFullYear() > 1970) {
                    dateStr = d.toLocaleString();
                } else {
                    // Start of epoch or invalid
                    dateStr = "";
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
        // Update status in grid? 
        // Ideally reload grid when going back.
    }
}

async function scheduleAlert() {
    if (!currentCallId) return;
    const time = document.getElementById('scheduleTime').value;
    if (!time) return;

    const res = await fetch(`/calls/${currentCallId}/schedule`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ scheduled_time: time }) // API expects ISO string, input provides something close
    });

    if (res.ok) {
        alert("Alerta Programada");
        // Refresh Grid to show new status and time
        const sel = document.getElementById('studySelect');
        if (sel.value) loadStudyData(sel.value);
        else loadStudyData(null);
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
        "Observacion": row.observation_text || ''
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
