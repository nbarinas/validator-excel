#!/usr/bin/env node
/**
 * Verifica las vistas previas y el dia digitado de las plantillas
 * `recordatorio_sibate_1_204` y `recordatorio_sibate_2_302`.
 *
 * Reglas del pedido:
 *  - El encabezado "DÍA {{dia}}/7" usa el numero que la persona digita antes de enviar.
 *  - La 204 saluda con {{entrevistada}}; la 302 con {{encuestada}}.
 *  - Ambas muestran mascota y censo, y no dejan variables sin sustituir.
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Regresion: una plantilla sin dia (r2_729) sigue ocultando el campo.
 *
 * Uso: node scripts/tests/check_recordatorio_sibate_preview.js [ruta/call_center.js]
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

function extraerConst(nombre) {
    const inicio = src.indexOf('const ' + nombre + ' = ');
    if (inicio === -1) throw new Error('no encontre ' + nombre);
    const fin = src.indexOf('\n};', inicio);
    if (fin === -1) throw new Error('no pude cerrar ' + nombre);
    return src.slice(inicio, fin + 3);
}

const KEY_204 = 'recordatorio_sibate_1_204';
const KEY_302 = 'recordatorio_sibate_2_302';

const CABECERA = '🐶 REGISTRO DIARIO – DÍA {{dia}}/7';
const BODY_204 = CABECERA + '\n\n¡Hola, {{entrevistada}}! 👋 Te saluda el equipo de AZ Marketing Plus.\n\n' +
    '🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  ' +
    'el producto entregado (código 204).\n\n' +
    '🍽️ Registra una sola comida al día, manteniendo el mismo horario.\n\n' +
    '⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.\n\n' +
    '🔢 Código de registro: {{censo}}\n\n' +
    '🔗 Diligencia aquí la encuesta:\nhttps://forms.gle/pP9Fd9v5ZSTGjemX8\n\n' +
    '¡Gracias por tu compromiso! 💚 Recuerda completar el registro durante los 7 días del estudio.';
const BODY_302 = BODY_204.replace('{{entrevistada}}', '{{encuestada}}').replace('código 204', 'código 302');

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
    [KEY_204]: { key: KEY_204, label: 'Recordatorio Sibate 1 — producto 204',
        params: ['dia', 'entrevistada', 'mascota', 'censo'], body: BODY_204 },
    [KEY_302]: { key: KEY_302, label: 'Recordatorio Sibate 2 — producto 302',
        params: ['dia', 'encuestada', 'mascota', 'censo'], body: BODY_302 },
    r2_729: { key: 'r2_729', label: 'Shampoo 729 — segunda videollamada (R2)',
        params: ['nombre_entrevistada', 'encuestador', 'hora_agendada'],
        body: 'Hola {{nombre_entrevistada}}, le saluda {{encuestador}} a las {{hora_agendada}}.' },
};

let radioChecked = { value: KEY_204 };

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

function preview204(dia) {
    radioChecked = { value: KEY_204 };
    els['waTemplateDay'].value = dia;
    ctx.waUpdateTemplateForm();
    return els['waTemplateInlinePreview'].textContent;
}

// 1. Modal 1x1: dia digitado, entrevistada y datos de la mascota.
console.log('[1] Modal 1x1 de la 204');
check((() => { preview204(''); return els['waTemplateDayGroup'].style.display === 'block'; })(),
    'la 204 muestra el campo Dia');
check(preview204('').startsWith('🐶 REGISTRO DIARIO – DÍA [día]/7'),
    'sin dia digitado la vista previa muestra [día]');
const inline204 = preview204('3');
check(inline204.startsWith('🐶 REGISTRO DIARIO – DÍA 3/7'),
    'la vista previa muestra el dia digitado (3)');
check(inline204.includes('¡Hola, Ana!'), 'la 204 sustituye {{entrevistada}} por el nombre');
check(inline204.includes('Luna') && inline204.includes('8877'),
    'la 204 sustituye mascota y censo');
check(!inline204.includes('{{'), 'la 204 no deja variables sin sustituir');

// 2. Modal 1x1 de la 302.
console.log('[2] Modal 1x1 de la 302');
radioChecked = { value: KEY_302 };
els['waTemplateDay'].value = '4';
ctx.waUpdateTemplateForm();
const inline302 = els['waTemplateInlinePreview'].textContent;
check(els['waTemplateDayGroup'].style.display === 'block', 'la 302 muestra el campo Dia');
check(inline302.startsWith('🐶 REGISTRO DIARIO – DÍA 4/7'),
    'la 302 muestra el dia digitado (4)');
check(inline302.includes('¡Hola, Ana!'), 'la 302 sustituye {{encuestada}} por el nombre');
check(inline302.includes('(código 302)'), 'la 302 conserva su codigo de producto');
check(!inline302.includes('{{'), 'la 302 no deja variables sin sustituir');

// 3. Sin dia no se pasa a la confirmacion; con dia el payload lo lleva.
console.log('[3] Validacion y payload del 1x1');
radioChecked = { value: KEY_204 };
els['waTemplateDay'].value = '';
els['waTemplateError'].style.display = 'none';
ctx.waPendingTemplatePayload = null;
ctx.showWhatsAppTemplatePreview();
check(els['waTemplateError'].style.display === 'block', 'sin dia se muestra un error');
check(els['waTemplateError'].textContent === 'Indica el día del registro antes de enviar.',
    'el error pide el dia del registro');
check(ctx.waPendingTemplatePayload === null, 'sin dia no queda payload pendiente de envio');

els['waTemplateDay'].value = '5';
els['waTemplateError'].style.display = 'none';
ctx.showWhatsAppTemplatePreview();
const payload = ctx.waPendingTemplatePayload || {};
check(payload.dia === '5', 'el payload 1x1 manda dia = 5');
check(payload.template_key === KEY_204, 'el payload 1x1 conserva la plantilla');
check(els['waPreviewBody'].textContent.startsWith('🐶 REGISTRO DIARIO – DÍA 5/7'),
    'la confirmacion muestra el dia digitado');

// 4. "Nuevo chat": pide nombre y dia, y sustituye entrevistada.
console.log('[4] Modal "Nuevo chat"');
els['waNewChatKind'].value = KEY_204;
const params = ctx.waNewChatTemplateParams();
check(params.needsDia === true, 'la 204 pide el dia en "Nuevo chat"');
check(params.needsName === true, 'la 204 pide el nombre (parametro entrevistada)');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'block', 'se muestra el campo Dia');
check(els['waNewChatNameLabel'].style.display === 'block', 'se muestra el campo Nombre');
els['waNewChatDay'].value = '6';
els['waNewChatName'].value = 'Ana';
els['waNewChatSubject'].value = '';
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.startsWith('🐶 REGISTRO DIARIO – DÍA 6/7'),
    'la vista previa de "Nuevo chat" muestra el dia digitado (6)');
check(nuevo.includes('¡Hola, Ana!'), 'la vista previa de "Nuevo chat" sustituye entrevistada');
check(!nuevo.includes('{{'), 'la vista previa de "Nuevo chat" no deja variables');

// 5. Regresion: una plantilla sin dia sigue ocultando el campo.
console.log('[5] Regresion de una plantilla sin dia');
els['waNewChatKind'].value = 'r2_729';
check(ctx.waNewChatTemplateParams().needsDia === false, 'r2_729 no pide el dia');
ctx.waToggleNewChatLink();
check(els['waNewChatDayLabel'].style.display === 'none', 'r2_729 no muestra el campo Dia');
radioChecked = { value: 'r2_729' };
els['waTemplateDay'].value = '3';
ctx.waUpdateTemplateForm();
check(els['waTemplateDayGroup'].style.display === 'none', 'r2_729 no muestra el campo Dia en 1x1');
check(els['waTemplateInlinePreview'].textContent.includes('Ana') &&
      els['waTemplateInlinePreview'].textContent.includes('Luis'), 'r2_729 sigue previsualizando bien');

if (fallas.length) {
    console.log(`\n${fallas.length} fallas.`);
    process.exit(1);
}
console.log('\nTodo OK.');
