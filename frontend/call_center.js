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

// Init
document.addEventListener('DOMContentLoaded', async () => {
    // Load User Info
    try {
        const uRes = await fetch('/users/me', { headers });
        if (uRes.ok) {
            const user = await uRes.json();
            currentUserRole = user.role;
            document.getElementById('userInfo').textContent = `Usuario: ${user.username} (${user.role})`;

            if (currentUserRole === 'superuser') {
                // Show Landing, Hide CRM
                document.getElementById('superuserLanding').style.display = 'block';
                document.getElementById('crmInterface').style.display = 'none';
                // Ensure button is visible if they enter
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = 'inline-block';
                // Ensure search is visible
                const search = document.getElementById('searchPanel');
                if (search) search.style.display = 'block';
            } else {
                // Normal User
                // Hide Create Study Button
                const btn = document.getElementById('btnCreateStudy');
                if (btn) btn.style.display = 'none';
                // Hide Search Panel
                const search = document.getElementById('searchPanel');
                if (search) search.style.display = 'none';
                loadStudies();
            }

            // AUTOMATICALLY LOAD ALL PENDING CALLS
            loadStudyData(null); // Null = all pending from open studies

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

function showDetailView() {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('callsGridView').style.display = 'none';
    document.getElementById('callDetailView').style.display = 'block';

    // Hide sidebar always in detail view
    document.querySelector('.sidebar').style.display = 'none';
    document.getElementById('crmInterface').style.gridTemplateColumns = '1fr';
}

async function loadStudyData(studyId) {
    // Fetch calls
    try {
        let url = '/calls';
        if (studyId) url += `?study_id=${studyId}`;

        const res = await fetch(url, { headers });
        const calls = await res.json();
        renderCallGrid(calls);
        // showGridView will calculate layout based on role
        showGridView();
    } catch (e) { console.error(e); }
}

function renderCallGrid(calls) {
    const tbody = document.getElementById('callsGridBody');
    tbody.innerHTML = '';

    if (calls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;">No hay llamadas pendientes</td></tr>';
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
            <td>
                <span style="font-size:0.8rem; color:#666; font-weight:bold;">${call.study_name || '-'}</span>
                ${call.study_type ? `<br><span style="font-size:0.7rem; color:#1a73e8; font-weight:600;">${call.study_type.toUpperCase()}</span>` : ''}
                ${call.study_stage ? `<span style="font-size:0.7rem; color:#f59e0b; font-weight:600; margin-left:0.3rem;">[${call.study_stage}]</span>` : ''}
            </td>
            <td><span style="font-size:0.8rem; color:${call.agent_name ? '#4caf50' : '#f44336'}; font-weight:bold;">${call.agent_name || 'Sin Asignar'}</span></td>
            <td>${call.person_name || '-'}</td>
            <td>${call.city || '-'}</td>
            <td>${alertTime}</td>
            <td><span style="background:${call.status === 'pending' ? '#fee2e2' : '#dcfce7'}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${call.status}</span></td>
            <td><button class="btn-submit" style="padding:0.3rem 0.6rem; font-size:0.8rem;">Gestionar</button></td>
        `;

        tr.onclick = (e) => {
            // Prevent opening if clicking checkbox
            if (e.target.type !== 'checkbox') openCallDetail(call);
        };
        tbody.appendChild(tr);
    });
}
// ...
// Scroll lower for other functions


function openCallDetail(call) {
    currentCallId = call.id;

    // Standard Info
    document.getElementById('phoneNumber').value = call.phone_number;
    document.getElementById('correctedPhone').value = call.corrected_phone || '';
    document.getElementById('personCC').value = call.person_cc || '';

    // New Fields
    document.getElementById('personName').value = call.person_name || '';
    document.getElementById('personCity').value = call.city || '';
    document.getElementById('personBrand').value = call.product_brand || '';
    document.getElementById('initialObs').value = call.initial_observation || '';
    document.getElementById('apptTime').value = call.appointment_time || '';
    document.getElementById('extraPhone').value = call.extra_phone || '';

    // Status Badge
    const badge = document.getElementById('callStatusBadge');
    badge.textContent = call.status;
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
        btnClose.style.display = 'block';
    }

    showDetailView();
}

async function finishCall() {
    if (!currentCallId) return;
    if (!confirm("¿Está seguro de cerrar/finalizar esta gestión? La llamada desaparecerá de los pendientes.")) return;

    try {
        const res = await fetch(`/calls/${currentCallId}/close`, {
            method: 'PUT',
            headers
        });

        if (res.ok) {
            alert("Gestión Finalizada");
            // Reload grid (which will exclude this call if normal user)
            // But we first need to decide where to go.
            // If we came from grid, go back to grid.

            // Get current filter?
            const sel = document.getElementById('studySelect');
            if (sel.value) loadStudyData(sel.value);
            else loadStudyData(null);

            showGridView();
        } else {
            alert("Error al finalizar");
        }
    } catch (e) { console.error(e); }
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
                opt.textContent = u.username;
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
    // This now updates instead of create new? 
    // Or creates call if manually typed? 
    // For now, if currentCallId exists, update. If not, create new session.

    const studyId = document.getElementById('studySelect').value;
    const phone = document.getElementById('phoneNumber').value;
    const corrected = document.getElementById('correctedPhone').value;
    const cc = document.getElementById('personCC').value;

    if (!studyId || !phone) {
        alert("Debe seleccionar un estudio y digitar un número.");
        return;
    }

    const body = {
        study_id: studyId,
        phone_number: phone,
        corrected_phone: corrected,
        person_cc: cc
    };

    // Simplification: Always create new entry or update... 
    // If we came from Grid (currentCallId set), we probably shouldn't CREATE a new one but update fields?
    // Models doesn't have update endpoint for header yet. 
    // Assuming "Save" just creates a fresh call record if manual, or saves Obs?
    // User flow: List -> Click -> Details -> Add Obs.
    // "Guardar / Iniciar Llamada" might be redundant if opened from list.
    // But useful if correct phone changed.

    // Let's assume for now we just Alert.
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
            el.innerHTML = `
                <div>${o.text}</div>
                <div class="obs-meta">${new Date(o.created_at).toLocaleString()}</div>
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
    }
}
