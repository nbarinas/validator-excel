#!/usr/bin/env node
/**
 * Verifica el dia digitado en las plantillas que lo piden (p. ej. `sibate_90mas15_dias`):
 * el encabezado no es fijo, se digita antes de enviar y viaja en el payload, tanto en
 * el modal 1x1 como en "Nuevo chat".
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Regresion: las plantillas con dia que ya existian (sibate_2) y las que no lo piden
 * (r2_729) siguen igual.
 *
 * Uso: node scripts/tests/check_template_day_preview.js [ruta/call_center.js]
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

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

const KEY = 'sibate_90mas15_dias';

// Cuerpo real de la plantilla en Meta (respaldo de la vista previa del masivo).
const BODY = 'REGISTRO DIARIO – DÍA {{dia}}/7\n\n¡Hola, {{encuestado}}! 👋\n' +
    'Te saluda el equipo de AZ Marketing Plus.\n\n' +
    '📅 Hoy corresponde realizar el registro del consumo de tu perro {{perro}}.\n\n' +
    '🍽️ Registra una sola comida al día, procurando mantener el mismo alimento y horario durante toda la semana.\n\n' +
    '⏱️ Mide el tiempo desde que sirves el alimento hasta que termine de comer.\n\n' +
    '👀 Observa su comportamiento durante la alimentación y registra tus observaciones en la encuesta.\n\n' +
    '📝 Recuerda realizar el registro todos los días durante los 7 días del estudio.\n\n' +
    '🔢 Código de registro: {{censo}}\n\n' +
    '🔗 INGRESA AQUÍ A LA ENCUESTA:\nhttps://forms.gle/3qsgqgVaCEepHrA89\n\n' +
    '¡Muchas gracias por tu compromiso y participación!';

function extraerConst(nombre) {
    const inicio = src.indexOf('const ' + nombre + ' = ');
    if (inicio === -1) throw new Error('no encontre ' + nombre);
    const fin = src.indexOf('\n};', inicio);
    if (fin === -1) throw new Error('no pude cerrar ' + nombre);
    return src.slice(inicio, fin + 3);
}

const fns = [
    extraerConst('waEsc'),
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

const els = {};
['waTemplateCategoryGroup', 'waTemplateHoraGroup', 'waTemplateHora', 'waTemplateCategory',
 'waTemplateDayGroup', 'waTemplateDay', 'waTemplateInlinePreview', 'waTemplateError',
 'waPreviewTemplateName', 'waPreviewBody', 'waPreviewError', 'whatsappSendTemplateModal',
 'whatsappTemplatePreviewModal', 'waNewChatKind', 'waNewChatName', 'waNewChatSubject',
 'waNewChatDay', 'waNewChatDayLabel', 'waNewChatNameLabel', 'waNewChatSubjectLabel',
 'waNewChatLinkLabel', 'waNewChatPreview'].forEach(id => { els[id] = el(id); });

const catalogo = {
    [KEY]: { key: KEY, label: 'Sibate 90 + 15 días',
        params: ['dia', 'encuestado', 'perro', 'censo'], body: BODY },
    sibate_2: { key: 'sibate_2', label: 'Recordatorio diario',
        params: ['encuestado', 'nombre_mascota', 'censo', 'dia'], body: 'DÍA {{dia}} de {{encuestado}}' },
    r2_729: { key: 'r2_729', label: 'Shampoo 729 — segunda videollamada (R2)',
        params: ['nombre_entrevistada', 'encuestador', 'hora_agendada'],
        body: 'Hola {{nombre_entrevistada}}, le saluda {{encuestador}} a las {{hora_agendada}}.' },
};

let radioChecked = { value: KEY };

const ctx = {
    document: {
        getElementById: id => els[id] || el(id),
        querySelector: sel => (sel.includes('waTemplateKey') ? radioChecked : null),
    },
    waTemplateCatalogMap: catalogo,
    currentCallData: { person_name: 'Ana', dog_name: 'Luna', census: '8877', collection_time: '3:30 pm' },
    currentUserName: 'Luis',
    waTemplateSourceField: 'chat',
    waChatCallId: 42,
    waPendingTemplatePayload: null,
    console,
};
vm.createContext(ctx);
vm.runInContext(fns, ctx);

const fallas = [];
function check(cond, msg) {
    console.log((cond ? '  OK    ' : '  FALLA ') + msg);
    if (!cond) fallas.push(msg);
}

// 1. Modal 1x1: el dia se digita y se ve en la vista previa.
console.log('[1] Modal 1x1');
els['waTemplateCategory'].value = '';
els['waTemplateDay'].value = '';
ctx.waUpdateTemplateForm();
check(els['waTemplateDayGroup'].style.display === 'block', 'la plantilla muestra el campo Día');
check(els['waTemplateInlinePreview'].textContent.startsWith('REGISTRO DIARIO – DÍA [día]/7'),
    'sin dia digitado la vista previa muestra [día]');
els['waTemplateDay'].value = '3';
ctx.waUpdateTemplateForm();
const inline = els['waTemplateInlinePreview'].textContent;
check(inline.startsWith('REGISTRO DIARIO – DÍA 3/7'), 'la vista previa muestra el dia digitado (3)');
check(!inline.includes('{{dia}}'), 'la vista previa no deja el dia sin sustituir');
check(inline.includes('Ana') && inline.includes('8877'),
    'la vista previa mantiene encuestado / censo');

// 2. Sin dia no se puede pasar a la confirmacion.
console.log('[2] Validacion antes de enviar');
els['waTemplateDay'].value = '';
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'block', 'sin dia se muestra un error');
check(els['waTemplateError'].textContent === 'Indica el día del registro antes de enviar.',
    'el error pide el dia del registro');
check(ctx.waPendingTemplatePayload === null, 'sin dia no queda payload pendiente de envio');

// 3. Con dia el payload lo lleva en el parametro correcto.
console.log('[3] Payload del 1x1');
els['waTemplateDay'].value = '3';
els['waTemplateError'].style.display = 'none';
ctx.showWhatsAppTemplatePreview();
const payload = ctx.waPendingTemplatePayload || {};
check(payload.dia === '3', 'el payload 1x1 manda dia = 3');
check(payload.template_key === KEY, 'el payload 1x1 conserva la plantilla');
check(els['waPreviewBody'].textContent.startsWith('REGISTRO DIARIO – DÍA 3/7'),
    'la confirmacion muestra el dia digitado');

// 4. "Nuevo chat": pide y manda el dia.
console.log('[4] Modal "Nuevo chat"');
els['waNewChatKind'].value = KEY;
const params = ctx.waNewChatTemplateParams();
check(params.needsDia === true, 'la plantilla pide el dia en "Nuevo chat"');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'block', 'se muestra el campo Día');
els['waNewChatDay'].value = '5';
els['waNewChatName'].value = 'Ana';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
check(els['waNewChatPreview'].textContent.startsWith('REGISTRO DIARIO – DÍA 5/7'),
    'la vista previa de "Nuevo chat" muestra el dia digitado (5)');
check(!els['waNewChatPreview'].textContent.includes('{{dia}}'),
    'la vista previa de "Nuevo chat" no deja el dia sin sustituir');

// 5. Regresion: plantillas con y sin dia siguen igual.
console.log('[5] Regresion de otras plantillas');
els['waNewChatKind'].value = 'sibate_2';
check(ctx.waNewChatTemplateParams().needsDia === true, 'sibate_2 sigue pidiendo el dia');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'block', 'sibate_2 sigue mostrando el campo Día');

els['waNewChatKind'].value = 'r2_729';
check(ctx.waNewChatTemplateParams().needsDia === false, 'r2_729 no pide el dia');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'r2_729 no muestra el campo Día');

radioChecked = { value: 'r2_729' };
els['waTemplateDay'].value = '3';
ctx.waUpdateTemplateForm();
check(els['waTemplateDayGroup'].style.display === 'none', 'r2_729 no muestra el campo Día en el modal 1x1');
check(els['waTemplateInlinePreview'].textContent.includes('Ana') &&
      els['waTemplateInlinePreview'].textContent.includes('Luis'), 'r2_729 sigue previsualizando bien');

radioChecked = { value: 'sibate_2' };
els['waTemplateDay'].value = '6';
ctx.waUpdateTemplateForm();
check(els['waTemplateInlinePreview'].textContent === 'DÍA 6 de Ana',
    'sibate_2 sigue previsualizando igual con el dia digitado');

if (fallas.length) {
    console.log(`\n${fallas.length} fallas.`);
    process.exit(1);
}
console.log('\nTodo OK.');
