#!/usr/bin/env node
/**
 * Regresion del filtro multi-estado del envio multiple ("Envio de links multiple").
 *
 * Cubre dos defectos reales:
 *  R1: el filtro ofrecia 8 estados escritos a mano en el HTML y no ofrecia
 *      "Enviado" (bulk_send_status = 'sent'), aunque ese estado existe en el
 *      select de cada fila. Ahora las opciones salen de BULK_LINK_STATUSES.
 *  R2: la opcion "Pendiente" filtraba por 'pending', pero un contacto pendiente
 *      guarda bulk_send_status = null. La comparacion contra '' nunca coincidia,
 *      asi que tildar "Pendiente" no mostraba ningun contacto.
 *
 * Evalua el codigo real de frontend/call_center.js, sin dependencias.
 * Uso: node scripts/tests/check_bulk_status_filter.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

let fallos = 0;
function check(ok, msg) {
    if (ok) {
        console.log('  ok  ' + msg);
    } else {
        fallos++;
        console.log('  MAL ' + msg);
    }
}

function extraerFuncion(nombre) {
    const inicio = src.indexOf('function ' + nombre + '(');
    if (inicio === -1) throw new Error('no encontre la funcion ' + nombre);
    let depth = 0;
    for (let j = src.indexOf('{', inicio); j < src.length; j++) {
        if (src[j] === '{') depth++;
        else if (src[j] === '}' && --depth === 0) return src.slice(inicio, j + 1);
    }
    throw new Error('no pude cerrar ' + nombre);
}

function extraerArray(nombre) {
    const inicio = src.indexOf('const ' + nombre + ' = [');
    if (inicio === -1) throw new Error('no encontre el array ' + nombre);
    let depth = 0;
    for (let j = src.indexOf('[', inicio); j < src.length; j++) {
        if (src[j] === '[') depth++;
        else if (src[j] === ']' && --depth === 0) return src.slice(inicio, j + 2);
    }
    throw new Error('no pude cerrar ' + nombre);
}

const codigo = [
    extraerArray('BULK_LINK_STATUSES'),
    extraerFuncion('bulkLinkStatusFilterOptions'),
    extraerFuncion('bulkLinkMatchesStatusFilter'),
    extraerFuncion('bulkLinkStatusBadgeHTML'),
    // 'const' no se cuelga del global del contexto: hay que exportarlo a mano.
    'this.__exports = { BULK_LINK_STATUSES, bulkLinkStatusFilterOptions, bulkLinkMatchesStatusFilter, bulkLinkStatusBadgeHTML };',
].join('\n');

const sandbox = { console };
vm.createContext(sandbox);
vm.runInContext(codigo, sandbox);
const { BULK_LINK_STATUSES, bulkLinkStatusFilterOptions, bulkLinkMatchesStatusFilter, bulkLinkStatusBadgeHTML } = sandbox.__exports;

// Contactos de prueba: el backend manda bulk_send_status null para "pendiente".
const contactos = [
    { id: 1, bulk_send_status: null, blocked: false },      // pendiente
    { id: 2, bulk_send_status: '', blocked: false },        // pendiente (string vacio)
    { id: 3, bulk_send_status: 'sent', blocked: false },    // enviado
    { id: 4, bulk_send_status: 'read', blocked: false },    // visto
    { id: 5, bulk_send_status: 'sent', blocked: true },     // enviado pero bloqueado
    { id: 6, bulk_send_status: 'pending', blocked: false }, // estado guardado como 'pending'
];

const ids = (estados) => contactos.filter(c => bulkLinkMatchesStatusFilter(c, estados)).map(c => c.id);

console.log('[1] Las opciones del filtro salen de una sola fuente (BULK_LINK_STATUSES)');
const opciones = bulkLinkStatusFilterOptions();
const valores = opciones.map(o => o.value);
// Un contacto pendiente se guarda como NULL/'' en la base: el filtro lo llama 'pending'.
const esperado = BULK_LINK_STATUSES.map(s => (s.value === '' ? 'pending' : s.value)).concat(['blocked']);
check(JSON.stringify(valores) === JSON.stringify(esperado),
    'opciones = estados reales + blocked: ' + valores.join(', '));
check(valores.includes('sent'), "ofrece 'sent' (Enviado)");
check(opciones.filter(o => o.value !== 'blocked').every(o => o.emoji && o.short),
    'cada opcion trae emoji y etiqueta corta para el chip');
const chipEnviado = bulkLinkStatusBadgeHTML(opciones.find(o => o.value === 'sent'), 7);
check(chipEnviado.includes('data-status="sent"') && chipEnviado.includes('data-count-for="sent"')
    && chipEnviado.includes('>7<') && chipEnviado.includes('bulk-status-check'),
    'el chip de Enviado es clickeable y lleva su contador: ' + chipEnviado.trim());
console.log('');

console.log('[2] Un estado tildado muestra solo ese estado');
check(JSON.stringify(ids(['sent'])) === JSON.stringify([3]), "['sent'] -> solo el enviado no bloqueado (3): " + ids(['sent']));
check(JSON.stringify(ids(['read'])) === JSON.stringify([4]), "['read'] -> solo el visto (4): " + ids(['read']));
console.log('');

console.log('[3] Pendiente incluye a los contactos sin estado guardado');
check(JSON.stringify(ids(['pending'])) === JSON.stringify([1, 2, 6]),
    "['pending'] -> null, '' y 'pending' (1, 2, 6): " + ids(['pending']));
console.log('');

console.log('[4] Varios estados tildados muestran la union');
check(JSON.stringify(ids(['sent', 'read'])) === JSON.stringify([3, 4]),
    "['sent','read'] -> 3 y 4: " + ids(['sent', 'read']));
check(JSON.stringify(ids(['pending', 'sent'])) === JSON.stringify([1, 2, 3, 6]),
    "['pending','sent'] -> 1, 2, 3, 6: " + ids(['pending', 'sent']));
console.log('');

console.log('[5] Sin estados tildados se ven todos (incluidos los bloqueados)');
check(ids([]).length === contactos.length, 'filtro vacio = todos: ' + ids([]).join(', '));
console.log('');

console.log('[6] Bloqueado es excluyente');
check(JSON.stringify(ids(['blocked'])) === JSON.stringify([5]), "['blocked'] -> solo el bloqueado (5): " + ids(['blocked']));
check(JSON.stringify(ids(['blocked', 'sent'])) === JSON.stringify([5]),
    "['blocked','sent'] -> gana bloqueado (5): " + ids(['blocked', 'sent']));
check(!ids(['sent']).includes(5), "['sent'] no arrastra contactos bloqueados");
console.log('');

if (fallos) {
    console.log('FALLARON ' + fallos + ' verificaciones');
    process.exit(1);
}
console.log('[7] La tabla y el contador respetan lo que esta tildado');
// Se evalua el codigo real de renderTable/updateCount/updateDashboard con un DOM minimo.
const els = {};
function makeEl(id) {
    if (!els[id]) {
        els[id] = {
            id, innerHTML: '', textContent: '', value: '', checked: false,
            style: {}, dataset: {}, querySelector: () => null, addEventListener: () => {},
        };
    }
    return els[id];
}

const dom = {
    getElementById: (id) => makeEl(id),
    querySelectorAll: (sel) => (sel === '.bulk-link-check:checked' ? [] : []),
};

const tildados = [];
const codigoTabla = [
    extraerArray('BULK_LINK_STATUSES'),
    extraerFuncion('bulkLinkStatusFilterOptions'),
    extraerFuncion('bulkLinkMatchesStatusFilter'),
    extraerFuncion('bulkLinkUpdateDashboard'),
    extraerFuncion('bulkLinkRenderTable'),
    extraerFuncion('bulkLinkUpdateCount'),
    // Dependencias de la tabla que no hacen al filtro: se reemplazan por stubs.
    'function bulkLinkActiveStatuses() { return tildadosRef.lista; }',
    'function bulkLinkStatusSelect() { return "<sel>"; }',
    'function waEsc(s) { return s == null ? "" : String(s); }',
    'function bulkLinkTimeAgo() { return ""; }',
    'function bulkLinkUpdateSelectAllState() { }',
    'function waTemplateBody() { return ""; }',
    'let bulkLinkContacts = contactosRef.lista;',
    "let bulkLinkFilter = 'all';",
    'let bulkLinkVisibleCount = 0;',
    'this.__exports = { bulkLinkRenderTable, bulkLinkUpdateCount };',
].join('\n');

const contactosRef = { lista: [
    { id: 11, person_name: 'ENVIADO-A', bulk_send_status: 'sent', blocked: false, phone_number: '1' },
    { id: 12, person_name: 'PENDIENTE-B', bulk_send_status: null, blocked: false, phone_number: '2' },
    { id: 13, person_name: 'VISTO-C', bulk_send_status: 'read', blocked: false, phone_number: '3' },
] };
const tildadosRef = { lista: [] };

const ctxTabla = vm.createContext({ console, document: dom, contactosRef, tildadosRef });
vm.runInContext(codigoTabla, ctxTabla);
const { bulkLinkRenderTable, bulkLinkUpdateCount } = ctxTabla.__exports;

tildadosRef.lista = ['sent'];
bulkLinkRenderTable();
bulkLinkUpdateCount();
const conEnviado = els.bulkLinkTableBody.innerHTML;
check(conEnviado.includes('ENVIADO-A'), 'con Enviado tildado se ve el contacto enviado');
check(!conEnviado.includes('PENDIENTE-B') && !conEnviado.includes('VISTO-C'),
    'con Enviado tildado no se ven pendientes ni vistos');
check(els.bulkLinkCount.textContent.includes('1 visibles'),
    'el contador avisa cuantos quedaron visibles: ' + els.bulkLinkCount.textContent);

tildadosRef.lista = ['sent', 'pending'];
bulkLinkRenderTable();
bulkLinkUpdateCount();
const conDos = els.bulkLinkTableBody.innerHTML;
check(conDos.includes('ENVIADO-A') && conDos.includes('PENDIENTE-B') && !conDos.includes('VISTO-C'),
    'con Enviado + Pendiente se ve la union y nada mas');

tildadosRef.lista = [];
bulkLinkRenderTable();
bulkLinkUpdateCount();
const sinFiltro = els.bulkLinkTableBody.innerHTML;
check(sinFiltro.includes('ENVIADO-A') && sinFiltro.includes('PENDIENTE-B') && sinFiltro.includes('VISTO-C'),
    'sin tildar nada se ven todos');
check(!els.bulkLinkCount.textContent.includes('visibles'),
    'sin filtro el contador no habla de visibles: ' + els.bulkLinkCount.textContent);
console.log('');

if (fallos) {
    console.log('FALLARON ' + fallos + ' verificaciones');
    process.exit(1);
}
console.log('Todo el filtro multi-estado del envio multiple quedo verificado.');
