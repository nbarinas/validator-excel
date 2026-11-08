#!/usr/bin/env node
/**
 * Verifica las vistas previas de las plantillas del estudio de freidoras de aire:
 * `inicia_avatar` (encuestada, encuestador, censo) y `recordatorio_avatar`
 * (entrevistado, censo).
 *
 * Reglas del pedido (ver odd/tasks/plantillas-avatar.md):
 *  - Las dos tienen que verse en la vista previa del 1x1, en "Nuevo chat" y en el masivo.
 *  - Ninguna usa dia: no muestran el campo Dia ni lo mandan en el payload.
 *  - `recordatorio_avatar` saluda con {{entrevistado}}, asi que "Nuevo chat" tiene que
 *    pedir el nombre igual que con {{encuestado}}/{{entrevistada}}.
 *
 * El cuerpo concreto lo fija check_avatar_templates.py; aca se evalua el comportamiento
 * de la vista previa contra el codigo real de frontend/call_center.js, con un DOM minimo.
 *
 * Uso: node scripts/tests/check_avatar_preview.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

const KEY_INICIA = 'inicia_avatar';
const KEY_RECORDATORIO = 'recordatorio_avatar';
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

/** Cuerpo del respaldo de vista previa (WA_TEMPLATE_BODIES) tal como esta en el fuente. */
function cuerpoDelFront(key) {
    const bloque = src.split('const WA_TEMPLATE_BODIES = {', 2)[1].split('\n};', 1)[0];
    const prefijo = '"' + key + '": "';
    if (!bloque.includes(prefijo)) throw new Error('no encontre el cuerpo de ' + key);
    const inicio = bloque.indexOf(prefijo) + prefijo.length;
    return JSON.parse('"' + bloque.slice(inicio, bloque.indexOf('",', inicio)) + '"');
}

const BODY_INICIA = cuerpoDelFront(KEY_INICIA);
const BODY_RECORDATORIO = cuerpoDelFront(KEY_RECORDATORIO);
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
        id,
        value: '',
        style: {},
        textContent: '',
        dataset: {},
        querySelector: () => null,
        addEventListener: () => {},
    };
    let html = '';
    Object.defineProperty(e, 'innerHTML', {
        get: () => html,
        set: v => {
            html = String(v);
            e.textContent = html.replace(/<[^>]*>/g, '');
        },
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
    [KEY_INICIA]: {
        key: KEY_INICIA,
        label: 'Avatar — inicio del estudio (Air Fryer)',
        params: ['encuestada', 'encuestador', 'censo'],
        body: BODY_INICIA,
    },
    [KEY_RECORDATORIO]: {
        key: KEY_RECORDATORIO,
        label: 'Avatar — recordatorio diario (Air Fryer)',
        params: ['entrevistado', 'censo'],
        body: BODY_RECORDATORIO,
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

let radioChecked = { value: KEY_INICIA };

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

// 0. Guardas del cuerpo del front (el contenido exacto lo fija el check .py).
console.log('[0] Cuerpos de vista previa presentes');
check(BODY_INICIA.includes('freidoras de aire (Air Fryer)') &&
      BODY_INICIA.includes('/formResponse') && BODY_INICIA.endsWith('confiar en AZ MARKETING'),
    'el front tiene el cuerpo de inicia_avatar (cortado tal cual)');
check(BODY_RECORDATORIO.includes('freidora de aire (Air Fryer). 🍟') &&
      BODY_RECORDATORIO.includes('/viewform') &&
      BODY_RECORDATORIO.endsWith('continuar participando con'),
    'el front tiene el cuerpo de recordatorio_avatar (cortado tal cual)');

// 1. Modal 1x1 de inicia_avatar.
console.log('[1] Modal 1x1 de inicia_avatar');
const inlineInicia = previewInline(KEY_INICIA, '');
check(els['waTemplateDayGroup'].style.display === 'none', 'no muestra el campo Dia');
check(inlineInicia.startsWith('Hola, Maria! 😊'), 'sustituye {{encuestada}} por el nombre');
check(inlineInicia.includes('Mi nombre es Ana.'), 'sustituye {{encuestador}} por el agente');
check(inlineInicia.includes('Tu número de registro es: 8877.'), 'sustituye {{censo}}');
check(!inlineInicia.includes('{{'), 'no deja variables sin sustituir');

// 2. Modal 1x1 de recordatorio_avatar.
console.log('[2] Modal 1x1 de recordatorio_avatar');
const inlineRec = previewInline(KEY_RECORDATORIO, '');
check(els['waTemplateDayGroup'].style.display === 'none', 'no muestra el campo Dia');
check(inlineRec.startsWith('¡Hola, Maria! 😊'), 'sustituye {{entrevistado}} por el nombre');
check(inlineRec.includes('registro es: 8877.'), 'sustituye {{censo}}');
check(!inlineRec.includes('{{'), 'no deja variables sin sustituir');

// 3. Validacion y payload del 1x1: sin dia y sin pedirlo.
console.log('[3] Validacion y payload del 1x1');
for (const key of [KEY_INICIA, KEY_RECORDATORIO]) {
    radioChecked = { value: key };
    els['waTemplateDay'].value = '';
    els['waTemplateError'].style.display = 'none';
    ctx.waPendingTemplatePayload = null;
    ctx.showWhatsAppTemplatePreview();
    check(els['waTemplateError'].style.display === 'none', `${key} no exige el dia`);
    const payload = ctx.waPendingTemplatePayload || {};
    check(payload.template_key === key && payload.dia === undefined,
        `${key} el payload no manda dia`);
    check(els['waPreviewBody'].textContent.includes('AZ MARKETING PLUS'),
        `${key} la confirmacion muestra el cuerpo`);
}

// 4. "Nuevo chat": el nombre se pide tambien con {{entrevistado}}.
console.log('[4] Modal "Nuevo chat"');
els['waNewChatKind'].value = KEY_RECORDATORIO;
let params = ctx.waNewChatTemplateParams();
check(params.needsDia === false, 'recordatorio_avatar no pide el dia');
check(params.needsName === true, 'recordatorio_avatar pide el nombre (parametro entrevistado)');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'no se muestra el campo Dia');
check(els['waNewChatNameLabel'].style.display === 'block', 'se muestra el campo Nombre');
els['waNewChatDay'].value = '';
els['waNewChatName'].value = 'Maria';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.startsWith('¡Hola, Maria! 😊'), 'sustituye entrevistado con el nombre digitado');
check(!nuevo.includes('{{'), 'no deja variables sin sustituir');

els['waNewChatKind'].value = KEY_INICIA;
params = ctx.waNewChatTemplateParams();
check(params.needsDia === false, 'inicia_avatar no pide el dia');
check(params.needsName === true, 'inicia_avatar pide el nombre');
ctx.waToggleNewChatLink();
ctx.waRenderNewChatPreview();
const nuevoInicia = els['waNewChatPreview'].textContent;
check(nuevoInicia.includes('Mi nombre es Ana.'), 'sustituye el encuestador en "Nuevo chat"');
check(!nuevoInicia.includes('{{'), 'no deja variables en "Nuevo chat"');

// 5. Masivo por estudio.
console.log('[5] Masivo por estudio');
for (const key of [KEY_INICIA, KEY_RECORDATORIO]) {
    els['bulkLinkTemplate'].value = key;
    ctx.bulkLinkOnTemplateChange();
    check(els['bulkLinkDayLabel'].style.display === 'none', `${key} no muestra el campo Dia`);
    check(els['bulkLinkTemplatePreview'].textContent.includes('AZ MARKETING PLUS'),
        `${key} se previsualiza en el masivo`);
}

// 6. Regresion: la de registro sigue pidiendo el dia y la sin variables sigue igual.
console.log('[6] Regresion del flujo previo');
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
