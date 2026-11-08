#!/usr/bin/env node
/**
 * Verifica las vistas previas de las plantillas del 9 de noviembre (Sibate):
 * `plantilla_inicio_semana_9_de_noviembre_sibate` y `registro_noviembre_9_2026`
 * (la segunda es la que Meta aprobo despues de rechazar el primer nombre).
 *
 * Reglas del pedido (ver odd/tasks/plantillas-noviembre-9-sibate.md):
 *  - Las dos tienen que verse en la vista previa del 1x1, en "Nuevo chat" y en el masivo.
 *  - La de inicio NO usa dia (entrevistada, mascota, censo).
 *  - La de registro pide el dia digitado antes de enviar (DÍA {{dia}}/7) y lo manda en
 *    el payload; sin dia no se pasa a la confirmacion. Usa {{encuestada}} y
 *    {{mascotica}} (nombre de parametro aprobado en Meta, con t).
 *
 * El cuerpo concreto de cada plantilla lo fija el check de contenido
 * (check_noviembre_9_sibate_templates.py); aca se evalua el comportamiento de la
 * vista previa contra el codigo real de frontend/call_center.js, con un DOM minimo.
 *
 * Regresion: `recordatorio_sibate_1_204` y una plantilla sin dia (`in_home_beta_385`)
 * conservan su flujo.
 *
 * Uso: node scripts/tests/check_noviembre_9_sibate_preview.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

const KEY_INICIO = 'plantilla_inicio_semana_9_de_noviembre_sibate';
const KEY_REGISTRO = 'registro_noviembre_9_2026';
const KEY_204 = 'recordatorio_sibate_1_204';

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
    const m = bloque.match(new RegExp('"' + key + '":\\s*"((?:[^"\\\\]|\\\\.)*)"'));
    if (!m) throw new Error('no encontre el cuerpo de ' + key);
    return JSON.parse('"' + m[1] + '"');
}

const BODY_INICIO = cuerpoDelFront(KEY_INICIO);
const BODY_REGISTRO = cuerpoDelFront(KEY_REGISTRO);
const BODY_204 = cuerpoDelFront(KEY_204);

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
    [KEY_INICIO]: {
        key: KEY_INICIO,
        label: 'Inicio semana 9 de noviembre (Sibate) — encuesta diaria',
        params: ['entrevistada', 'mascota', 'censo'],
        body: BODY_INICIO,
    },
    [KEY_REGISTRO]: {
        key: KEY_REGISTRO,
        label: 'Registro diario 9 de noviembre (Sibate)',
        params: ['dia', 'encuestada', 'mascotica', 'censo'],
        body: BODY_REGISTRO,
    },
    [KEY_204]: {
        key: KEY_204,
        label: 'Recordatorio Sibate 1 — producto 204',
        params: ['dia', 'entrevistada', 'mascota', 'censo'],
        body: BODY_204,
    },
    in_home_beta_385: {
        key: 'in_home_beta_385',
        label: 'In Home Beta 385',
        params: ['encuestada', 'encuestador', 'hora_asignada'],
        body: 'Hola {{encuestada}}, le saluda {{encuestador}} a las {{hora_asignada}}.',
    },
};

let radioChecked = { value: KEY_INICIO };

const ctx = {
    document: {
        getElementById: id => els[id] || el(id),
        querySelector: sel => (sel.includes('waTemplateKey') ? radioChecked : null),
    },
    waTemplateCatalogMap: catalogo,
    currentCallData: {
        person_name: 'Maria', dog_name: 'Luna', census: '8877', collection_time: '5:00 pm',
    },
    currentUserName: 'Luis',
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
check(BODY_INICIO.includes('ENCUESTA DIARIA – 7 DÍAS') &&
      BODY_INICIO.includes('https://forms.gle/cedqXEt1zPQXZcRt6'),
    'el front tiene el cuerpo de la plantilla de inicio');
check(BODY_REGISTRO.startsWith('REGISTRO DIARIO\nDÍA {{dia}}/7') &&
      BODY_REGISTRO.includes('https://forms.gle/HAtyTHjKxLYmtinz5'),
    'el front tiene el cuerpo de la plantilla de registro');

// 1. Modal 1x1 de la plantilla de inicio: no pide dia.
console.log('[1] Modal 1x1 de la plantilla de inicio');
const inlineInicio = previewInline(KEY_INICIO, '');
check(els['waTemplateDayGroup'].style.display === 'none',
    'la plantilla de inicio no muestra el campo Dia (no usa dia)');
check(inlineInicio.startsWith('ENCUESTA DIARIA – 7 DÍAS'),
    'la vista previa arranca con el encabezado aprobado');
check(inlineInicio.includes('¡Hola, Maria👋'), 'sustituye {{entrevistada}} por el nombre');
check(inlineInicio.includes('perrito  Luna  tarda'), 'sustituye {{mascota}}');
check(inlineInicio.includes('8877'), 'sustituye {{censo}}');
check(!inlineInicio.includes('{{'), 'no deja variables sin sustituir');

// 2. Modal 1x1 de la plantilla de registro: pide dia y lo muestra.
console.log('[2] Modal 1x1 de la plantilla de registro');
const inlineSinDia = previewInline(KEY_REGISTRO, '');
check(inlineSinDia.startsWith('REGISTRO DIARIO') && inlineSinDia.includes('DÍA [día]/7') &&
      els['waTemplateDayGroup'].style.display === 'block',
    'sin dia digitado muestra el campo Dia y el marcador [día]');
const inlineRec = previewInline(KEY_REGISTRO, '3');
check(inlineRec.startsWith('REGISTRO DIARIO') && inlineRec.includes('DÍA 3/7'),
    'la vista previa muestra el dia digitado (3)');
check(inlineRec.includes('¡Hola, Maria! 👋'), 'sustituye {{encuestada}} por el nombre');
check(inlineRec.includes('perro Luna.'), 'sustituye {{mascotica}} por el nombre del perro');
check(inlineRec.includes('8877') && inlineRec.includes('https://forms.gle/HAtyTHjKxLYmtinz5'),
    'muestra el censo y el link de la encuesta');
check(!inlineRec.includes('{{'), 'no deja variables sin sustituir');

// 3. Validacion y payload del 1x1.
console.log('[3] Validacion y payload del 1x1');
radioChecked = { value: KEY_REGISTRO };
els['waTemplateDay'].value = '';
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'block', 'la de registro sin dia muestra un error');
check(els['waTemplateError'].textContent === 'Indica el día del registro antes de enviar.',
    'el error pide el dia del registro');
check(ctx.waPendingTemplatePayload === null, 'sin dia no queda payload pendiente de envio');

els['waTemplateDay'].value = '5';
els['waTemplateError'].style.display = 'none';
ctx.showWhatsAppTemplatePreview();
const payloadRec = ctx.waPendingTemplatePayload || {};
check(payloadRec.dia === '5', 'el payload de registro manda dia = 5');
check(payloadRec.template_key === KEY_REGISTRO, 'el payload conserva la plantilla elegida');
check(els['waPreviewBody'].textContent.startsWith('REGISTRO DIARIO') &&
      els['waPreviewBody'].textContent.includes('DÍA 5/7'),
    'la confirmacion muestra el dia digitado');

radioChecked = { value: KEY_INICIO };
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
ctx.showWhatsAppTemplatePreview();
const payloadInicio = ctx.waPendingTemplatePayload || {};
check(els['waTemplateError'].style.display === 'none', 'la plantilla de inicio no exige dia');
check(payloadInicio.template_key === KEY_INICIO, 'el payload de inicio conserva la plantilla');
check(payloadInicio.dia === undefined, 'el payload de inicio no manda dia');

// 4. "Nuevo chat": nombre y dia segun la plantilla.
console.log('[4] Modal "Nuevo chat"');
els['waNewChatKind'].value = KEY_REGISTRO;
let params = ctx.waNewChatTemplateParams();
check(params.needsDia === true, 'la de registro pide el dia en "Nuevo chat"');
check(params.needsName === true, 'la de registro pide el nombre (parametro encuestada)');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'block', 'se muestra el campo Dia');
els['waNewChatDay'].value = '6';
els['waNewChatName'].value = 'Maria';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.startsWith('REGISTRO DIARIO') && nuevo.includes('DÍA 6/7'),
    'la vista previa de "Nuevo chat" muestra el dia digitado (6)');
check(nuevo.includes('¡Hola, Maria! 👋') && !nuevo.includes('{{'),
    'la vista previa de "Nuevo chat" sustituye encuestada sin dejar variables');

els['waNewChatKind'].value = KEY_INICIO;
params = ctx.waNewChatTemplateParams();
check(params.needsDia === false, 'la plantilla de inicio no pide el dia en "Nuevo chat"');
check(params.needsName === true, 'la plantilla de inicio pide el nombre');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'no se muestra el campo Dia');
ctx.waRenderNewChatPreview();
const nuevoInicio = els['waNewChatPreview'].textContent;
check(nuevoInicio.startsWith('ENCUESTA DIARIA – 7 DÍAS'), 'la vista previa de inicio arranca bien');
check(!nuevoInicio.includes('{{'), 'la vista previa de inicio no deja variables');

// 5. Masivo por estudio: el campo Dia aparece solo para el recordatorio.
console.log('[5] Masivo por estudio (campo Dia y vista previa)');
els['bulkLinkTemplate'].value = KEY_REGISTRO;
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'block',
    'la de registro muestra el campo Dia en el masivo');
check(els['bulkLinkTemplatePreview'].textContent.includes('DÍA {{dia}}/7') &&
      els['bulkLinkTemplatePreview'].textContent.includes('¡Hola, {{encuestada}}!'),
    'el masivo previsualiza la de registro con sus variables sin sustituir');

els['bulkLinkTemplate'].value = KEY_INICIO;
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'none',
    'la plantilla de inicio no muestra el campo Dia en el masivo');
check(els['bulkLinkTemplatePreview'].textContent.includes('ENCUESTA DIARIA – 7 DÍAS'),
    'el masivo previsualiza la plantilla de inicio');

// 6. Regresion: las plantillas previas conservan su flujo.
console.log('[6] Regresion del flujo previo');
check(previewInline(KEY_204, '4').startsWith('🐶 REGISTRO DIARIO – DÍA 4/7') &&
      els['waTemplateDayGroup'].style.display === 'block',
    'recordatorio_sibate_1_204 sigue pidiendo y mostrando el dia');
check(previewInline(KEY_204, '4').includes('¡Hola, Maria!'),
    'recordatorio_sibate_1_204 sigue sustituyendo entrevistada');
check(previewInline('in_home_beta_385', '3') && els['waTemplateDayGroup'].style.display === 'none',
    'in_home_beta_385 sigue sin campo Dia');
els['bulkLinkTemplate'].value = KEY_204;
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'block',
    'recordatorio_sibate_1_204 sigue pidiendo el dia en el masivo');
els['bulkLinkTemplate'].value = 'in_home_beta_385';
ctx.bulkLinkOnTemplateChange();
check(els['bulkLinkDayLabel'].style.display === 'none',
    'in_home_beta_385 sigue sin campo Dia en el masivo');

if (fallas.length) {
    console.log(`\n${fallas.length} fallas.`);
    process.exit(1);
}
console.log('\nTodo OK.');
