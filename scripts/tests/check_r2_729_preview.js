#!/usr/bin/env node
/**
 * Verifica la plantilla r2_729 en el front: la vista previa del modal 1x1 y del
 * modal "Nuevo chat" sustituyen sus variables propias ({{nombre_entrevistada}},
 * {{encuestador}}, {{hora_agendada}}) y el formulario reconoce sus parametros.
 *
 * Regresion: in_home_beta_385 sigue previsualizando bien (codigo compartido).
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Uso: node scripts/tests/check_r2_729_preview.js [ruta/call_center.js]
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
 'waNewChatSubjectLabel'].forEach(id => { els[id] = el(id); });

const r2_729_BODY = '¡Muy buenos días, señora {{nombre_entrevistada}}! 😊\n\n' +
    'La saluda {{encuestador}}, de AZ Marketing Plus.\n\n' +
    'Le escribo porque hoy tiene programada la segunda videollamada del estudio de ' +
    'shampoo 729, a las {{hora_agendada}}.\n\n' +
    '¿Sería posible realizarla en este momento o prefiere que la contactemos más tarde?\n\n' +
    'Quedo atento a su respuesta. ¡Muchas gracias y feliz día! 🌷';

const catalogo = {
    r2_729: { key: 'r2_729', label: 'Shampoo 729 — segunda videollamada', params: ['nombre_entrevistada', 'encuestador', 'hora_agendada'], body: r2_729_BODY },
    in_home_beta_385: { key: 'in_home_beta_385', label: 'In Home Beta 385', params: ['encuestada', 'encuestador', 'hora_asignada'], body: 'Az-Marketing\nHola {{encuestada}}, le saluda {{encuestador}} a las {{hora_asignada}}.' },
};

let radioChecked = { value: 'r2_729' };

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

// 1. Modal 1x1: reconoce los parametros de r2_729 y previsualiza bien.
radioChecked = { value: 'r2_729' };
els['waTemplateCategory'].value = '';
ctx.waUpdateTemplateForm();
check(els['waTemplateHoraGroup'].style.display === 'block',
    'r2_729 reconocido como plantilla con hora (grupo de hora visible)');
const inline729 = els['waTemplateInlinePreview'].textContent;
check(inline729.includes('Ana') && inline729.includes('Luis') && inline729.includes('3:30 pm'),
    'r2_729 previsualiza nombre_entrevistada / encuestador / hora_agendada');
check(!inline729.includes('{{'), 'r2_729 no deja variables sin sustituir en la vista previa');

// 2. Modal "Nuevo chat": pide el nombre y previsualiza.
els['waNewChatKind'].value = 'r2_729';
els['waNewChatName'].value = 'Ana';
els['waNewChatSubject'].value = '';
const params729 = ctx.waNewChatTemplateParams();
check(params729.needsName === true, 'r2_729 pide el nombre en "Nuevo chat"');
ctx.waToggleNewChatLink();
check(els['waNewChatNameLabel'].style.display === 'block', 'r2_729 muestra el campo Nombre');
ctx.waRenderNewChatPreview();
const newChat729 = els['waNewChatPreview'].textContent;
check(newChat729.includes('Ana') && newChat729.includes('Luis') && newChat729.includes('[hora de recogida]'),
    'r2_729 previsualiza sus variables en "Nuevo chat"');
check(!newChat729.includes('{{'), 'r2_729 no deja variables sin sustituir en "Nuevo chat"');

// 3. Regresion: las plantillas existentes siguen previsualizando igual.
radioChecked = { value: 'in_home_beta_385' };
els['waTemplateCategory'].value = '';
ctx.waUpdateTemplateForm();
const inline385 = els['waTemplateInlinePreview'].textContent;
check(inline385.includes('Ana') && inline385.includes('Luis') && inline385.includes('3:30 pm'),
    'in_home_beta_385 sigue previsualizando sus variables');
check(!inline385.includes('{{'), 'in_home_beta_385 no deja variables sin sustituir');

if (fallas.length) {
    console.error(`\n${fallas.length} falla(s).`);
    process.exit(1);
}
console.log('\nTodo OK.');
