const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

let currentStudyId = null;
let allStudies = []; // Global store for robust access

document.addEventListener('DOMContentLoaded', () => {
    fetchStudies();
    checkUser();
    toggleInHomeOptions();
});

function toggleInHomeOptions() {
    const type = document.getElementById('studyType').value;
    const censusGroup = document.getElementById('groupCensus');

    if (type === 'In Home') {
        group.style.display = 'block';
        if (censusGroup) censusGroup.style.display = 'none';
    } else if (type === 'Ascensor') {
        group.style.display = 'none';
        if (censusGroup) censusGroup.style.display = 'block';
    } else {
        group.style.display = 'none';
        if (censusGroup) censusGroup.style.display = 'none';

        // Reset values
        ['ih_implantacion', 'ih_r1', 'ih_rf', 'ih_caida_des', 'ih_caida', 'ih_nopart'].forEach(id => {
            document.getElementById(id).value = '0';
            document.getElementById(id + '_price').value = '0';
        });
    }
}

async function checkUser() {
    try {
        const res = await fetch('/users/me', { headers: { 'Authorization': 'Bearer ' + token } });
        if (res.ok) {
            const user = await res.json();
            document.getElementById('userInfo').textContent = `Usuario: ${user.username} (${user.role})`;

            // ROLE CONTROL: Agents cannot see "In Home"
            if (user.role === 'agent') {
                const opt = document.getElementById('optInHome');
                if (opt) opt.style.display = 'none'; // Or remove it
                if (document.getElementById('studyType').value === 'In Home') {
                    document.getElementById('studyType').value = 'Ascensor'; // Default to something else
                    toggleInHomeOptions();
                }
            }

            if (user.role !== 'superuser' && user.role !== 'bizage' && user.role !== 'agent') {
                // If generic access logic applies. The requirement says: 
                // "Rol bizage seria como un agente pero con la vista y uso del bizage"
                // "En el rol agente quitar “in Home” solo queda nomina y call center" -> Wait, user said "solo queda nomina y call center" for Agent?
                // Actually the requirement: "En el rol agente quitar “in Home” solo queda nomina y call center" likely means Agent shouldn't see Bizage at all if "nomina y call center" are different modules.
                // BUT "El rol bizage seria como un agente pero con la vista y uso del bizage".
                // Let's assume Agent CAN see this page but restricted, OR Agent is restricted from "In Home".
                // "En el rol agente quitar “in Home”" implies they access Bizage module.
            }
        } else {
            window.location.href = '/login';
        }
    } catch (e) { console.error(e); }
}

async function fetchStudies() {
    try {
        const res = await fetch('/bizage/studies', { headers: { 'Authorization': 'Bearer ' + token } });
        allStudies = await res.json();
        renderTable(allStudies);
    } catch (e) { console.error("Error fetching studies", e); }
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
}

const STATUS_MAP = {
    'registered': 'Registrado',
    'radicated': 'Radicado',
    'number_assigned': 'Asignado',
    'paid': 'Pagado'
};

function renderTable(studies) {
    const tbody = document.getElementById('studiesBody');
    tbody.innerHTML = '';

    studies.forEach(s => {
        const tr = document.createElement('tr');

        const statusSpan = STATUS_MAP[s.status] || s.status;
        let statusBadge = `<span class="status-badge status-${s.status}">${statusSpan}</span>`;

        let costDetails = [];
        if (s.quantity) costDetails.push(`Qty: ${s.quantity}`);
        if (s.price) costDetails.push(`$: ${s.price}`);
        if (s.copies) costDetails.push(`Copia: ${s.copies}`);
        if (s.vinipel) costDetails.push(`Vini: ${s.vinipel}`);
        if (s.other_cost_amount) costDetails.push(`${s.other_cost_description}: ${s.other_cost_amount}`);

        let details = `<div style="font-size:0.85rem">
            ${costDetails.length ? `<div>${costDetails.join(' | ')}</div>` : ''}
            ${s.bizagi_number ? `<div>Bizagi: ${s.bizagi_number}</div>` : ''}
            ${s.invoice_number ? `<div>Factura: ${s.invoice_number}</div>` : ''}
            ${s.survey_no_participa ? `<div style="color:#fbbf24; font-style:italic; white-space: pre-wrap;">${s.survey_no_participa}</div>` : ''}
        </div>`;

        let history = `<div class="history-tooltip">
            <div>Reg: ${s.registered_by} (${formatDate(s.registered_at)})</div>
            ${s.radicated_by ? `<div>Rad: ${s.radicated_by} (${formatDate(s.radicated_at)})</div>` : ''}
            ${s.bizagi_by ? `<div>Biz: ${s.bizagi_by} (${formatDate(s.bizagi_at)})</div>` : ''}
            ${s.paid_by ? `<div>Paid: ${s.paid_by} (${formatDate(s.paid_at)})</div>` : ''}
        </div>`;

        let actions = '';
        if (s.status === 'registered') {
            actions = `<button class="btn-action btn-radicar" onclick="openRadicar(${s.id})">Radicar</button>`;
        } else if (s.status === 'radicated') {
            actions = `<button class="btn-action btn-bizagi" onclick="openBizagi(${s.id})">Bizagi</button>`;
        } else if (s.status === 'number_assigned') {
            actions = `<button class="btn-action btn-pay" onclick="openPay(${s.id})">Pagar</button>`;
        } else {
            actions = `<span style="color: #4ade80"><i class="fas fa-check-circle"></i> Pagado</span>`;
        }

        // Pass ID directly, not object
        actions += ` <button class="btn-action btn-history" onclick="openEdit(${s.id})" style="margin-left:5px" title="Editar"><i class="fas fa-edit"></i></button>`;

        tr.innerHTML = `
            <td>#${s.id}</td>
            <td>${s.study_type}</td>
            <td>${s.study_name}</td>
            <td>${s.n_value}</td>
            <td>${details}</td>
            <td>${statusBadge}</td>
            <td>${history}</td>
            <td class="actions-cell">${actions}</td>
        `;
        tbody.appendChild(tr);
    });
}

// REGISTER
async function registerStudy() {
    const type = document.getElementById('studyType').value;
    const name = document.getElementById('studyName').value;
    const n = document.getElementById('nValue').value;
    const notes = document.getElementById('surveyNotes').value;
    const census = document.getElementById('census') ? document.getElementById('census').value : null;

    let finalNotes = notes;
    if (type === 'In Home') {
        const fields = [
            { id: 'ih_implantacion', label: 'Implantación' },
            { id: 'ih_r1', label: 'R1/Otros' },
            { id: 'ih_rf', label: 'RF' },
            { id: 'ih_caida_des', label: 'Caída Desempeño' },
            { id: 'ih_caida', label: 'Caída' },
            { id: 'ih_nopart', label: 'No Part' }
        ];

        let totalInHome = 0;
        let details = [];

        fields.forEach(f => {
            const qty = parseInt(document.getElementById(f.id).value || 0);
            // Price ID convention: id + "_price"
            const price = parseInt(document.getElementById(f.id + '_price').value || 0);

            if (qty > 0 || price > 0) {
                const subtotal = qty * price;
                totalInHome += subtotal;
                // Format: Label: Qty x $Price ($Subtotal)
                details.push(`${f.label}: ${qty}x$${price}`);
            }
        });

        // Add Total line at the end
        const breakdown = details.join(', ');
        const totalStr = `\n[TOTAL IN HOME: $${totalInHome.toLocaleString()}]`;

        finalNotes = breakdown + totalStr + (notes ? `\nNotas: ${notes}` : '');
    }

    if (!name || !n) { alert("Completa los campos obligatorios"); return; }

    try {
        const res = await fetch('/bizage/studies', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ study_type: type, study_name: name, n_value: parseInt(n), survey_no_participa: finalNotes, census: census })
        });
        if (res.ok) {
            document.getElementById('studyName').value = '';
            document.getElementById('nValue').value = '';
            document.getElementById('surveyNotes').value = '';
            // Reset in home
            toggleInHomeOptions();
            fetchStudies();
        } else alert("Error");
    } catch (e) { }
}

// RADICAR
function openRadicar(id) {
    currentStudyId = id;
    document.getElementById('radQuantity').value = '';
    document.getElementById('radPrice').value = '';
    document.getElementById('radCopies').value = '0';
    document.getElementById('radVinipel').value = '0';
    document.getElementById('radOtherDesc').value = '';
    document.getElementById('radOtherDesc').value = '';
    document.getElementById('radOtherVal').value = '0';
    document.getElementById('radCopiesPrice').value = '';
    document.getElementById('radVinipelPrice').value = '';
    document.getElementById('modalRadicar').style.display = 'flex';
}

async function confirmRadicar() {
    const qty = document.getElementById('radQuantity').value;
    const price = document.getElementById('radPrice').value;
    if (!qty || !price) { alert("Cantidad y Precio requeridos"); return; }

    try {
        const res = await fetch(`/bizage/studies/${currentStudyId}/radicate`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({
                quantity: parseInt(qty), price: parseInt(price),
                copies: parseInt(document.getElementById('radCopies').value || 0),
                vinipel: parseInt(document.getElementById('radVinipel').value || 0),
                other_cost_description: document.getElementById('radOtherDesc').value,
                other_cost_amount: parseInt(document.getElementById('radOtherVal').value || 0),
                copies_price: parseInt(document.getElementById('radCopiesPrice').value || 0),
                vinipel_price: parseInt(document.getElementById('radVinipelPrice').value || 0)
            })
        });
        if (res.ok) { closeModal('modalRadicar'); fetchStudies(); }
    } catch (e) { }
}

// BIZAGI
function openBizagi(id) {
    currentStudyId = id;
    document.getElementById('modalBizagi').style.display = 'flex';
}

async function confirmBizagi() {
    const num = document.getElementById('bizagiNumber').value;
    if (!num) return;
    try {
        const res = await fetch(`/bizage/studies/${currentStudyId}/bizagi`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ bizagi_number: num })
        });
        if (res.ok) { closeModal('modalBizagi'); fetchStudies(); }
    } catch (e) { }
}

// PAY
function openPay(id) {
    currentStudyId = id;
    const now = new Date();
    const local = new Date(now.getTime() - (now.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
    document.getElementById('payDate').value = local;
    document.getElementById('payInvoice').value = '';
    document.getElementById('modalPay').style.display = 'flex';
}

async function confirmPay() {
    const dateVal = document.getElementById('payDate').value;
    const invoice = document.getElementById('payInvoice').value;
    if (!dateVal) { alert("Fecha requerida"); return; }
    const isoDate = new Date(dateVal).toISOString();

    try {
        const res = await fetch(`/bizage/studies/${currentStudyId}/pay`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ paid_at: isoDate, invoice_number: invoice })
        });
        if (res.ok) { closeModal('modalPay'); fetchStudies(); }
    } catch (e) { }
}

// EDIT
function openEdit(id) {
    const study = allStudies.find(s => s.id === id);
    if (!study) return;

    currentStudyId = study.id;
    document.getElementById('editType').value = study.study_type || '';
    document.getElementById('editName').value = study.study_name || '';
    document.getElementById('editN').value = study.n_value || 0;

    document.getElementById('editBizagi').value = study.bizagi_number || '';

    document.getElementById('editQty').value = study.quantity || '';
    document.getElementById('editPrice').value = study.price || '';
    document.getElementById('editCopies').value = study.copies || 0;
    document.getElementById('editCopiesPrice').value = study.copies_price || 0;
    document.getElementById('editVinipel').value = study.vinipel || 0;
    document.getElementById('editVinipelPrice').value = study.vinipel_price || 0;

    document.getElementById('editOtherDesc').value = study.other_cost_description || '';
    document.getElementById('editOtherVal').value = study.other_cost_amount || 0;

    document.getElementById('editNotes').value = study.survey_no_participa || '';
    document.getElementById('editStatus').value = study.status;

    document.getElementById('modalEdit').style.display = 'flex';
}

async function confirmEdit() {
    const data = {
        study_type: document.getElementById('editType').value,
        study_name: document.getElementById('editName').value,
        n_value: parseInt(document.getElementById('editN').value),

        bizagi_number: document.getElementById('editBizagi').value,

        quantity: parseInt(document.getElementById('editQty').value || 0),
        price: parseInt(document.getElementById('editPrice').value || 0),
        copies: parseInt(document.getElementById('editCopies').value || 0),
        copies_price: parseInt(document.getElementById('editCopiesPrice').value || 0),
        vinipel: parseInt(document.getElementById('editVinipel').value || 0),
        vinipel_price: parseInt(document.getElementById('editVinipelPrice').value || 0),

        other_cost_description: document.getElementById('editOtherDesc').value,
        other_cost_amount: parseInt(document.getElementById('editOtherVal').value || 0),

        survey_no_participa: document.getElementById('editNotes').value,
        status: document.getElementById('editStatus').value
    };

    try {
        const res = await fetch(`/bizage/studies/${currentStudyId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify(data)
        });
        if (res.ok) { closeModal('modalEdit'); fetchStudies(); }
    } catch (e) { console.error(e); }
}

function closeModal(id) { document.getElementById(id).style.display = 'none'; }
function logout() { localStorage.removeItem('token'); window.location.href = '/login'; }
