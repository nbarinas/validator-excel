#!/usr/bin/env node
/**
 * Verifica la vista previa de las cuatro plantillas del estudio Sibate 250 / SunTea R1
 * en el modal 1x1, en "Nuevo chat" y en el masivo por estudio.
 *
 * Reglas del pedido (ver odd/tasks/plantillas-250-noviembre.md, L1 y L2):
 *  - suntea_durazno_r1: {{encuestada}}, {{encuestador}} y {{hora}} (hora del registro).
 *  - entrega_sibate_250: solo {{encuestada}}.
 *  - concentrado__producto_semana_16_de_noviembre_250: {{encuestada}}, {{mascota}}, {{censo}}.
 *  - recordatorio_sibate_semana_16_de_noviembre_250: {{dia}}, {{encuestada}}, {{mascota}},
 *    {{censo}}; es la unica de las cuatro que pide el dia.
 *
 * El cuerpo exacto lo fija check_plantillas_250_noviembre.py; aca se evalua la vista previa
 * contra el codigo real de frontend/call_center.js.
 *
 * Uso: node scripts/tests/check_plantillas_250_noviembre_preview.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

const SUNTEA = 'suntea_durazno_r1';
const ENTREGA = 'entrega_sibate_250';
const CONCENTRADO = 'concentrado__producto_semana_16_de_noviembre_250';
const RECORDATORIO = 'recordatorio_sibate_semana_16_de_noviembre_250';
const KEY_SIBATE_1 = 'recordatorio_sibate_1_204';

function extraer(nombre) {
    const inicio = src.indexOf('function ' + nombre + '(');
    if (inicio === -1) throw new Error('no encontre ' + nombre);
    let depth = 0;
    for (let j = src.indexOf('{', inicio); j < src.length; j++) {
        if (src[j] === '{') depth++;
        else if (src[j] === '}' && --depth === 0) return src.slice(inicio, j + 1);
    }
    throw new Error('no pude cerrar ' + nombre);
}

function extraerConst(nombre) {
    const inicio = src.indexOf('const ' + nombre + ' = ');
    if (inicio === -1) throw new Error('no encontre ' + nombre);
    const fin = src.indexOf('\n};', inicio);
    if (fin === -1) throw new Error('no pude cerrar ' + nombre);
    return src.slice(inicio, fin + 3);
}

function extraerLinea(nombre) {
    const prefijo = 'const ' + nombre + ' = ';
    const linea = src.split('\n').find(l => l.startsWith(prefijo));
    if (!linea) throw new Error('no encontre la linea ' + nombre);
    return linea;
}

function cuerpoDelFront(key) {
    const bloque = src.split('const WA_TEMPLATE_BODIES = {', 2)[1].split('\n};', 1)[0];
    const prefijo = '"' + key + '": "';
    if (!bloque.includes(prefijo)) throw new Error('no encontre el cuerpo de ' + key);
    const inicio = bloque.indexOf(prefijo) + prefijo.length;
    return JSON.parse('"' + bloque.slice(inicio, bloque.indexOf('",', inicio)) + '"');
}

const fns = [
    extraerConst('waEsc'),
    extraerConst('BULK_TEMPLATE_VARS'),
    extraerLinea('BULK_DAY_TEMPLATES'),
    [
        'waFormatPreviewHtml',
        'waTemplateLabel',
        'getWhatsAppTemplateHora',
        'waTemplateBody',
        'waRenderInlineTemplatePreview',
        'waUpdateTemplateForm',
        'showWhatsAppTemplatePreview',
        'waToggleNewChatLink',
        'waRenderNewChatPreview',
        'waNewChatTemplateParams',
        'bulkLinkRenderTemplatePreview',
        'bulkLinkOnTemplateChange',
    ].map(extraer).join('\n'),
].join('\n');

function el(id) {
    const e = {
        id, value: '', style: {}, textContent: '', dataset: {},
        querySelector: () => null, addEventListener: () => {},
    };
    let html = '';
    Object.defineProperty(e, 'innerHTML', {
        get: () => html,
        set: v => { html = String(v); e.textContent = html.replace(/<[^>]*>/g, ''); },
    });
    return e;
}

const IDS = [
    'waTemplateCategoryGroup', 'waTemplateHoraGroup', 'waTemplateHora', 'waTemplateCategory',
    'waTemplateDayGroup', 'waTemplateDay', 'waTemplateInlinePreview', 'waTemplateError',
    'waPreviewTemplateName', 'waPreviewBody', 'waPreviewError', 'whatsappSendTemplateModal',
    'whatsappTemplatePreviewModal', 'waNewChatKind', 'waNewChatName', 'waNewChatSubject',
    'waNewChatDay', 'waNewChatDayLabel', 'waNewChatNameLabel', 'waNewChatSubjectLabel',
    'waNewChatLinkLabel', 'waNewChatPreview',
    'bulkLinkTemplate', 'bulkLinkDayLabel', 'bulkLinkFechaLabel', 'bulkLinkTemplatePreview',
];
const els = {};
IDS.forEach(id => { els[id] = el(id); });

const catalogo = {
    [SUNTEA]: {
        key: SUNTEA,
        label: 'SunTea durazno — recordatorio de videollamada (R1)',
        params: ['encuestada', 'encuestador', 'hora'],
        body: cuerpoDelFront(SUNTEA),
    },
    [ENTREGA]: {
        key: ENTREGA,
        label: 'Sibate 250 — confirmación de entrega del producto',
        params: ['encuestada'],
        body: cuerpoDelFront(ENTREGA),
    },
    [CONCENTRADO]: {
        key: CONCENTRADO,
        label: 'Sibate 250 — concentrado + producto (semana 16 de noviembre)',
        params: ['encuestada', 'mascota', 'censo'],
        body: cuerpoDelFront(CONCENTRADO),
    },
    [RECORDATORIO]: {
        key: RECORDATORIO,
        label: 'Sibate 250 — recordatorio diario (semana 16 de noviembre)',
        params: ['dia', 'encuestada', 'mascota', 'censo'],
        body: cuerpoDelFront(RECORDATORIO),
    },
    [KEY_SIBATE_1]: {
        key: KEY_SIBATE_1,
        label: 'Recordatorio Sibate 1 — producto 204',
        params: ['dia', 'entrevistada', 'mascota', 'censo'],
        body: cuerpoDelFront(KEY_SIBATE_1),
    },
};

let radioChecked = { value: SUNTEA };

const ctx = {
    document: {
        getElementById: id => els[id] || el(id),
        querySelector: sel => (sel.includes('waTemplateKey') ? radioChecked : null),
    },
    waTemplateCatalogMap: catalogo,
    currentCallData: {
        person_name: 'Maria', dog_name: 'Firulais', census: 'C250-01', collection_time: '5:00 pm',
    },
    currentUserName: 'Ana',
    waTemplateSourceField: 'chat',
    waChatCallId: 42,
    waPendingTemplatePayload: null,
    bulkLinkContacts: [],
    console,
};
vm.createContext(ctx);
vm.runInContext(fns, ctx);

const fallas = [];
function check(cond, msg) {
    console.log((cond ? '  OK    ' : '  FALLA ') + msg);
    if (!cond) fallas.push(msg);
}

function previewInline(key, dia) {
    radioChecked = { value: key };
    els['waTemplateDay'].value = dia || '';
    ctx.waUpdateTemplateForm();
    return els['waTemplateInlinePreview'].textContent;
}

console.log('[0] Los cuatro cuerpos estan en el front');
check(cuerpoDelFront(SUNTEA).startsWith('Hola, señora {{encuestada}}, ¿cómo está? 😊') &&
      cuerpoDelFront(SUNTEA).includes('videollamada a las {{hora}}.'),
    'suntea_durazno_r1 usa encuestada, encuestador y hora');
check(cuerpoDelFront(ENTREGA).includes('"RECIBIDO"') &&
      cuerpoDelFront(ENTREGA).includes('a partir  de hoy'),
    'entrega_sibate_250 conserva el doble espacio y las comillas del pedido');
check(cuerpoDelFront(CONCENTRADO).startsWith('AZ Marketing Plus\n') &&
      cuerpoDelFront(CONCENTRADO).endsWith('la última encuesta y explicar'),
    'concentrado__producto_semana_16_de_noviembre_250 conserva el corte del pedido');
check(cuerpoDelFront(RECORDATORIO).startsWith('Saludos\n🐶 REGISTRO DIARIO – DÍA {{dia}}/7') &&
      cuerpoDelFront(RECORDATORIO).endsWith('durante los 7 días del estudi'),
    'recordatorio_sibate_semana_16_de_noviembre_250 conserva el corte del pedido');

console.log('[1] Modal 1x1: campos visibles por plantilla');
let inline = previewInline(SUNTEA, '');
check(els['waTemplateHoraGroup'].style.display === 'block', 'suntea muestra el campo Hora');
check(els['waTemplateDayGroup'].style.display === 'none', 'suntea no muestra el campo Dia');
check(inline.startsWith('Hola, señora Maria, ¿cómo está? 😊'),
    'suntea sustituye {{encuestada}} por el nombre');
check(inline.includes('Le saluda Ana, del equipo'), 'suntea sustituye {{encuestador}}');
check(inline.includes('a las 5:00 pm.'), 'suntea sustituye {{hora}} con la hora del registro');
check(!inline.includes('{{'), 'suntea no deja variables sin sustituir');

els['waTemplateHoraGroup'].style.display = 'block';
inline = previewInline(ENTREGA, '');
check(els['waTemplateHoraGroup'].style.display === 'none', 'entrega no muestra el campo Hora');
check(els['waTemplateDayGroup'].style.display === 'none', 'entrega no muestra el campo Dia');
check(inline.startsWith('Hola, Maria 😊'), 'entrega sustituye {{encuestada}}');
check(inline.includes('respóndenos') && inline.includes('RECIBIDO'),
    'entrega conserva el texto literal RECIBIDO');
check(!inline.includes('{{'), 'entrega no deja variables sin sustituir');

inline = previewInline(CONCENTRADO, '');
check(els['waTemplateHoraGroup'].style.display === 'none', 'concentrado no muestra el campo Hora');
check(els['waTemplateDayGroup'].style.display === 'none', 'concentrado no muestra el campo Dia');
check(inline.includes('con tu mascota Firulais! 🐾'), 'concentrado sustituye {{mascota}}');
check(inline.includes('codigo C250-01'), 'concentrado sustituye {{censo}}');
check(!inline.includes('{{'), 'concentrado no deja variables sin sustituir');

inline = previewInline(RECORDATORIO, '3');
check(els['waTemplateDayGroup'].style.display === 'block', 'recordatorio muestra el campo Dia');
check(els['waTemplateHoraGroup'].style.display === 'none', 'recordatorio no muestra el campo Hora');
check(inline.includes('DÍA 3/7'), 'recordatorio sustituye {{dia}}');
check(inline.includes('tu mascota, Firulais,'), 'recordatorio sustituye {{mascota}}');
check(inline.includes('Código de registro: C250-01'), 'recordatorio sustituye {{censo}}');
check(!inline.includes('{{'), 'recordatorio no deja variables sin sustituir');

console.log('[2] Validacion y payload del 1x1');
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
previewInline(SUNTEA, '');
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'none', 'suntea no exige el dia');
const payloadSuntea = ctx.waPendingTemplatePayload || {};
check(payloadSuntea.template_key === SUNTEA && payloadSuntea.dia === undefined,
    'el payload de suntea no manda dia');

els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
previewInline(RECORDATORIO, '3');
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'none', 'recordatorio acepta el dia 3');
const payloadRecordatorio = ctx.waPendingTemplatePayload || {};
check(payloadRecordatorio.template_key === RECORDATORIO && payloadRecordatorio.dia === '3',
    'el payload del recordatorio manda el dia');

els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
previewInline(RECORDATORIO, '');
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display !== 'none',
    'el recordatorio sin dia se rechaza antes de enviar');

console.log('[3] Modal "Nuevo chat"');
els['waNewChatKind'].value = SUNTEA;
let params = ctx.waNewChatTemplateParams();
check(params.needsDia === false, 'suntea no pide el dia en Nuevo chat');
check(params.needsName === true, 'suntea pide el nombre (parametro encuestada)');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'suntea no muestra el campo Dia');
els['waNewChatName'].value = 'Maria';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
const nuevoSuntea = els['waNewChatPreview'].textContent;
check(nuevoSuntea.startsWith('Hola, señora Maria, ¿cómo está? 😊'),
    'suntea sustituye el nombre digitado');
check(nuevoSuntea.includes('Le saluda Ana,'), 'suntea sustituye el agente');
check(!nuevoSuntea.includes('{{'), 'suntea no deja variables sin sustituir');

els['waNewChatKind'].value = RECORDATORIO;
params = ctx.waNewChatTemplateParams();
check(params.needsDia === true, 'recordatorio pide el dia en Nuevo chat');
els['waNewChatDay'].value = '5';
ctx.waToggleNewChatLink();
ctx.waRenderNewChatPreview();
const nuevoRecordatorio = els['waNewChatPreview'].textContent;
check(nuevoRecordatorio.includes('DÍA 5/7'), 'recordatorio sustituye el dia digitado');
check(!nuevoRecordatorio.includes('{{'), 'recordatorio no deja variables sin sustituir');

console.log('[4] Masivo por estudio');
for (const key of [SUNTEA, ENTREGA, CONCENTRADO]) {
    els['bulkLinkTemplate'].value = key;
    els['bulkLinkTemplatePreview'].dataset = {};
    ctx.bulkLinkOnTemplateChange();
    check(els['bulkLinkDayLabel'].style.display === 'none', key + ' no muestra el campo Dia');
    check(els['bulkLinkTemplatePreview'].textContent.includes('{{'),
        key + ' se previsualiza con las variables sin sustituir');
}
els['bulkLinkTemplate'].value = RECORDATORIO;
els['bulkLinkTemplatePreview'].dataset = {};
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'block',
    'recordatorio pide el dia en el masivo');
check(els['bulkLinkTemplatePreview'].textContent.includes('{{dia}}'),
    'recordatorio se previsualiza con {{dia}} sin sustituir');

console.log('[5] Regresion del flujo previo');
check(previewInline(KEY_SIBATE_1, '4').includes('Día 4 de 7') ||
      previewInline(KEY_SIBATE_1, '4').includes('DÍA 4/7'),
    'recordatorio_sibate_1_204 sigue sustituyendo el dia');
check(els['waTemplateDayGroup'].style.display === 'block',
    'recordatorio_sibate_1_204 sigue mostrando el campo Dia');
els['bulkLinkTemplate'].value = KEY_SIBATE_1;
els['bulkLinkTemplatePreview'].dataset = {};
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'block',
    'recordatorio_sibate_1_204 sigue pidiendo el dia en el masivo');

if (fallas.length) {
    console.log(`\n${fallas.length} fallas.`);
    process.exit(1);
}
console.log('\nTodo OK.');
