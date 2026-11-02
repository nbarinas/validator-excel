#!/usr/bin/env node
/**
 * Verifica la plantilla primera_recogida_853_ en el front: la vista previa del
 * modal 1x1 y del modal "Nuevo chat" sustituyen sus variables propias
 * ({{nombre_entrevistada}}, {{nombre_encuestador}}, {{hora_agendada}}) y el
 * formulario reconoce sus parametros.
 *
 * Regresion: final_beta y fatiga_729_r3 siguen previsualizando bien (codigo compartido).
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Uso: node scripts/tests/check_primera_recogida_853_preview.js [ruta/call_center.js]
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

const fns = [
    extraerConst('waEsc'),
    [
        'waFormatPreviewHtml',
        'getWhatsAppTemplateHora',
        'waTemplateBody',
        'waRenderInlineTemplatePreview',
        'waUpdateTemplateForm',
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
 'waTemplateInlinePreview', 'waNewChatKind', 'waNewChatName', 'waNewChatSubject',
 'waNewChatPreview', 'waNewChatLink', 'waNewChatLinkLabel', 'waNewChatNameLabel',
 'waNewChatSubjectLabel', 'waNewChatDayLabel'].forEach(id => { els[id] = el(id); });

const KEY = 'primera_recogida_853_';
const BODY_853 = `¡Hola, señora {{nombre_entrevistada}}! ¿Cómo está? 😊

Mucho gusto, mi nombre es {{nombre_encuestador}}, del equipo de AZ Marketing Plus.

Le escribo porque hace 10 días le dejamos el shampoo 853 y para el día de hoy tiene programada una videollamada.

El objetivo es realizar un seguimiento al uso del shampoo, conocer cómo le ha ido con el producto y registrar su experiencia durante estos días.

¿Me confirma si todavía tiene disponibilidad para realizarla a las {{hora_agendada}} o si prefiere que la hagamos en este momento?

Quedo atento a su respuesta. ¡Muchas gracias y feliz día!`;

const FINAL_BETA_BODY = `¡Hola, {{nombre_entrevistada}}! 😊

Te saluda {{nombre_encuestador}}, del equipo de AZ Marketing Plus.

Te escribimos porque tienes programada la última videollamada del estudio de tratamiento capilar para hoy a las {{hora_agendada}}.

¿Continúas disponible para realizarla a esa hora o prefieres que la hagamos en este momento?

Al finalizar la videollamada, te brindaremos las indicaciones para recibir tu bono de participación.

Quedamos atentos a tu respuesta.

¡Feliz día! 🌷`;

const catalogo = {
    [KEY]: { key: KEY, label: 'Shampoo 853 — primera recogida', params: ['nombre_entrevistada', 'nombre_encuestador', 'hora_agendada'], body: BODY_853 },
    final_beta: { key: 'final_beta', label: 'final_beta', params: ['nombre_entrevistada', 'nombre_encuestador', 'hora_agendada'], body: FINAL_BETA_BODY },
    fatiga_729_r3: { key: 'fatiga_729_r3', label: 'Shampoo 729 — tercera videollamada (R3)', params: ['nombre_entrevistada', 'encuestador', 'hora_agendada'], body: '¡Muy buenos días, señora {{nombre_entrevistada}}! Le saluda {{encuestador}} a las {{hora_agendada}}.' },
};

let radioChecked = { value: KEY };

const ctx = {
    document: {
        getElementById: id => els[id] || el(id),
        querySelector: sel => (sel.includes('waTemplateKey') ? radioChecked : null),
    },
    waTemplateCatalogMap: catalogo,
    currentCallData: { person_name: 'Ana', collection_time: '3:30 pm' },
    currentUserName: 'Luis',
    console,
};
vm.createContext(ctx);
vm.runInContext(fns, ctx);

const fallas = [];
function check(cond, msg) {
    console.log((cond ? '  OK    ' : '  FALLA ') + msg);
    if (!cond) fallas.push(msg);
}

// 0. El respaldo local del front incluye la plantilla byte-exacta (si falla el
// catalogo del servidor, la vista previa no se queda sin texto).
const bodiesCtx = vm.createContext({});
const frontBodies = vm.runInContext(
    extraerConst('WA_TEMPLATE_BODIES') + '\nWA_TEMPLATE_BODIES;', bodiesCtx);
check(frontBodies[KEY] === BODY_853,
    `WA_TEMPLATE_BODIES del front tiene ${KEY} byte-exacto`);

// 1. Modal 1x1: reconoce los parametros y previsualiza bien.
radioChecked = { value: KEY };
els['waTemplateCategory'].value = '';
ctx.waUpdateTemplateForm();
check(els['waTemplateHoraGroup'].style.display === 'block',
    `${KEY} reconocido como plantilla con hora (grupo de hora visible)`);
const inline = els['waTemplateInlinePreview'].textContent;
check(inline.includes('Ana') && inline.includes('Luis') && inline.includes('3:30 pm'),
    `${KEY} previsualiza nombre_entrevistada / nombre_encuestador / hora_agendada`);
check(inline.includes('shampoo 853') && inline.includes('durante estos días'),
    `${KEY} muestra el shampoo 853 y el seguimiento durante estos días`);
check(!inline.includes('{{'), `${KEY} no deja variables sin sustituir en la vista previa`);

// 2. Modal "Nuevo chat": pide el nombre y previsualiza.
els['waNewChatKind'].value = KEY;
els['waNewChatName'].value = 'Ana';
els['waNewChatSubject'].value = '';
const params = ctx.waNewChatTemplateParams();
check(params.needsName === true, `${KEY} pide el nombre en "Nuevo chat"`);
ctx.waToggleNewChatLink();
check(els['waNewChatNameLabel'].style.display === 'block', `${KEY} muestra el campo Nombre`);
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.includes('Ana') && nuevo.includes('Luis') && nuevo.includes('[hora de recogida]'),
    `${KEY} previsualiza sus variables en "Nuevo chat"`);
check(!nuevo.includes('{{'), `${KEY} no deja variables sin sustituir en "Nuevo chat"`);

// 3. Regresion: final_beta y fatiga_729_r3 siguen previsualizando igual.
for (const vecina of ['final_beta', 'fatiga_729_r3']) {
    radioChecked = { value: vecina };
    els['waTemplateCategory'].value = '';
    ctx.waUpdateTemplateForm();
    const inlineVecina = els['waTemplateInlinePreview'].textContent;
    check(inlineVecina.includes('Ana') && inlineVecina.includes('Luis') && inlineVecina.includes('3:30 pm'),
        `${vecina} sigue previsualizando sus variables`);
    check(!inlineVecina.includes('{{'), `${vecina} no deja variables sin sustituir`);
}

if (fallas.length) {
    console.error(`\n${fallas.length} falla(s).`);
    process.exit(1);
}
console.log('\nTodo OK.');
