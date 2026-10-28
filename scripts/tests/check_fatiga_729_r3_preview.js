#!/usr/bin/env node
/**
 * Verifica la plantilla fatiga_729_r3 en el front: la vista previa del modal 1x1 y
 * del modal "Nuevo chat" sustituyen sus variables propias
 * ({{nombre_entrevistada}}, {{encuestador}}, {{hora_agendada}}) y el formulario
 * reconoce sus parametros.
 *
 * Regresion: in_home_beta_385 sigue previsualizando bien (codigo compartido).
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Uso: node scripts/tests/check_fatiga_729_r3_preview.js [ruta/call_center.js]
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

const fatiga_BODY = `¡Muy buenos días, señora {{nombre_entrevistada}}! 😊

La saluda {{encuestador}}, de AZ Marketing Plus.

Le escribo para recordarle que hoy tiene programada la tercera videollamada del estudio de shampoo 729, a las {{hora_agendada}}.

Al finalizar la videollamada, le explicaremos cómo recibirá su primer bono de $20.000 por su participación en el estudio.

¿Podemos realizar la videollamada en este momento o prefiere que la contactemos más tarde?

¡Muchas gracias por su compromiso! Le deseo un feliz día. 🌷`;

const catalogo = {
    fatiga_729_r3: { key: 'fatiga_729_r3', label: 'Shampoo 729 — tercera videollamada (R3)', params: ['nombre_entrevistada', 'encuestador', 'hora_agendada'], body: fatiga_BODY },
    in_home_beta_385: { key: 'in_home_beta_385', label: 'In Home Beta 385', params: ['encuestada', 'encuestador', 'hora_asignada'], body: 'Az-Marketing\nHola {{encuestada}}, le saluda {{encuestador}} a las {{hora_asignada}}.' },
};

let radioChecked = { value: 'fatiga_729_r3' };

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

// 1. Modal 1x1: reconoce los parametros de fatiga_729_r3 y previsualiza bien.
radioChecked = { value: 'fatiga_729_r3' };
els['waTemplateCategory'].value = '';
ctx.waUpdateTemplateForm();
check(els['waTemplateHoraGroup'].style.display === 'block',
    'fatiga_729_r3 reconocido como plantilla con hora (grupo de hora visible)');
const inline = els['waTemplateInlinePreview'].textContent;
check(inline.includes('Ana') && inline.includes('Luis') && inline.includes('3:30 pm'),
    'fatiga_729_r3 previsualiza nombre_entrevistada / encuestador / hora_agendada');
check(inline.includes('tercera videollamada') && inline.includes('$20.000'),
    'fatiga_729_r3 muestra la tercera videollamada y el bono');
check(!inline.includes('{{'), 'fatiga_729_r3 no deja variables sin sustituir en la vista previa');

// 2. Modal "Nuevo chat": pide el nombre y previsualiza.
els['waNewChatKind'].value = 'fatiga_729_r3';
els['waNewChatName'].value = 'Ana';
els['waNewChatSubject'].value = '';
const params = ctx.waNewChatTemplateParams();
check(params.needsName === true, 'fatiga_729_r3 pide el nombre en "Nuevo chat"');
ctx.waToggleNewChatLink();
check(els['waNewChatNameLabel'].style.display === 'block', 'fatiga_729_r3 muestra el campo Nombre');
ctx.waRenderNewChatPreview();
const nuevo = els['waNewChatPreview'].textContent;
check(nuevo.includes('Ana') && nuevo.includes('Luis') && nuevo.includes('[hora de recogida]'),
    'fatiga_729_r3 previsualiza sus variables en "Nuevo chat"');
check(!nuevo.includes('{{'), 'fatiga_729_r3 no deja variables sin sustituir en "Nuevo chat"');

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
