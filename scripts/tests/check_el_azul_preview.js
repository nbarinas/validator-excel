#!/usr/bin/env node
/**
 * Verifica la vista previa de `el_azul` en el 1x1, en "Nuevo chat" y en el masivo por estudio.
 *
 * Reglas del pedido (ver odd/tasks/plantillas-avatar.md, L6):
 *  - El cuerpo arranca con "Saludos" y sigue "¡Hola, {{encuestada}}! 😊 ...".
 *  - Usa {{censo}} y no usa dia.
 *  - El cierre va tal cual, cortado en "...participando con", y el link es
 *    https://forms.gle/jhwUsEbh1Bf6rMG79.
 *
 * El cuerpo exacto lo fija check_el_azul.py; aca se evalua el comportamiento de la
 * vista previa contra el codigo real de frontend/call_center.js.
 *
 * Uso: node scripts/tests/check_el_azul_preview.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

const KEY = 'el_azul';
const KEY_REGISTRO = 'registro_noviembre_9_2026';

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

const BODY = cuerpoDelFront(KEY);
const BODY_REGISTRO = cuerpoDelFront(KEY_REGISTRO);

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
    [KEY]: {
        key: KEY,
        label: 'Recordatorio Avatar — noviembre (Air Fryer)',
        params: ['encuestada', 'censo'],
        body: BODY,
    },
    [KEY_REGISTRO]: {
        key: KEY_REGISTRO,
        label: 'Registro diario 9 de noviembre (Sibate)',
        params: ['dia', 'encuestada', 'mascotica', 'censo'],
        body: BODY_REGISTRO,
    },
    in_home_beta_385: {
        key: 'in_home_beta_385',
        label: 'In Home Beta 385',
        params: ['encuestada', 'encuestador', 'hora_asignada'],
        body: 'Hola {{encuestada}}, le saluda {{encuestador}} a las {{hora_asignada}}.',
    },
};

let radioChecked = { value: KEY };

const ctx = {
    document: {
        getElementById: id => els[id] || el(id),
        querySelector: sel => (sel.includes('waTemplateKey') ? radioChecked : null),
    },
    waTemplateCatalogMap: catalogo,
    currentCallData: {
        person_name: 'Maria', dog_name: 'Luna', census: '8877', collection_time: '5:00 pm',
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

// 0. Guarda del cuerpo del front.
console.log('[0] Cuerpo de vista previa presente');
check(BODY.startsWith('Saludos\n¡Hola, {{encuestada}}! 😊') &&
      BODY.includes('https://forms.gle/jhwUsEbh1Bf6rMG79') &&
      BODY.endsWith('continuar participando con'),
    'el front tiene el cuerpo con Saludos, el link corto y el cierre cortado');

// 1. Modal 1x1.
console.log('[1] Modal 1x1');
const inline = previewInline(KEY, '');
check(els['waTemplateDayGroup'].style.display === 'none', 'no muestra el campo Dia');
check(inline.startsWith('Saludos\n¡Hola, Maria! 😊'),
    'arranca con Saludos y sustituye {{encuestada}} por el nombre');
check(inline.includes('registro es: 8877.'), 'sustituye {{censo}}');
check(inline.includes('freidora de aire (Air Fryer). 🍟'), 'conserva el cuerpo aprobado');
check(!inline.includes('{{'), 'no deja variables sin sustituir');

// 2. Validacion y payload: sin dia y sin pedirlo.
console.log('[2] Validacion y payload del 1x1');
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'none', 'no exige el dia');
const payload = ctx.waPendingTemplatePayload || {};
check(payload.template_key === KEY, 'el payload conserva la plantilla');
check(payload.dia === undefined, 'el payload no manda dia');
check(els['waPreviewBody'].textContent.includes('AZ MARKETING PLUS'),
    'la confirmacion muestra el cuerpo');

// 3. "Nuevo chat".
console.log('[3] Modal "Nuevo chat"');
els['waNewChatKind'].value = KEY;
const params = ctx.waNewChatTemplateParams();
check(params.needsDia === false, 'no pide el dia');
check(params.needsName === true, 'pide el nombre (parametro encuestada)');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'no se muestra el campo Dia');
check(els['waNewChatNameLabel'].style.display === 'block', 'se muestra el campo Nombre');
els['waNewChatName'].value = 'Maria';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.startsWith('Saludos\n¡Hola, Maria! 😊'), 'sustituye el nombre digitado');
check(!nuevo.includes('{{'), 'no deja variables sin sustituir');

// 4. Masivo por estudio.
console.log('[4] Masivo por estudio');
els['bulkLinkTemplate'].value = KEY;
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'none', 'no muestra el campo Dia');
check(els['bulkLinkTemplatePreview'].textContent.includes('Saludos\n¡Hola, {{encuestada}}! 😊'),
    'se previsualiza con las variables sin sustituir');

// 5. Regresion.
console.log('[5] Regresion del flujo previo');
check(previewInline(KEY_REGISTRO, '4').includes('DÍA 4/7') &&
      els['waTemplateDayGroup'].style.display === 'block',
    'registro_noviembre_9_2026 sigue pidiendo y mostrando el dia');
els['bulkLinkTemplate'].value = KEY_REGISTRO;
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'block',
    'registro_noviembre_9_2026 sigue pidiendo el dia en el masivo');
els['waNewChatKind'].value = 'in_home_beta_385';
check(ctx.waNewChatTemplateParams().needsDia === false, 'in_home_beta_385 sigue sin pedir el dia');

if (fallas.length) {
    console.log(`\n${fallas.length} fallas.`);
    process.exit(1);
}
console.log('\nTodo OK.');
