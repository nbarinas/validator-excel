#!/usr/bin/env node
/**
 * Regresion (B2): el select `waNewChatKind` lo comparte el envio "una por una" y el
 * "Envio masivo" (pegado de lista). Cuando todavia no se eligio estudio, tiene que
 * quedar con una key valida del catalogo, no con 'filter'/'form'/vacio (que
 * /whatsapp/send-bulk rechaza con 400).
 *
 * Evalua el codigo real de frontend/call_center.js con un DOM minimo, sin dependencias.
 * Uso: node scripts/tests/check_new_chat_bulk_default.js [ruta/call_center.js]
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

const fns = ['waNewChatAllSingleKeys', 'waPopulateNewChatTemplates'].map(extraer).join('\n');

function el(id) {
    return {
        id,
        value: '',
        innerHTML: '',
        style: {},
        textContent: '',
        dataset: {},
        querySelector: () => null,
        addEventListener: () => {},
    };
}

const els = {};
['waNewChatKind', 'waNewChatSingleGroup', 'waNewChatName', 'waNewChatSubject',
 'waNewChatPreview', 'waNewChatLink', 'waNewChatLinkLabel', 'waNewChatNameLabel',
 'waNewChatSubjectLabel'].forEach(id => { els[id] = el(id); });

const catalogo = {
    manana_3: { key: 'manana_3', label: 'Buenas tardes (recordatorio)', params: ['nombre', 'encuestador', 'categoria'] },
    shampo_primer: { key: 'shampo_primer', label: 'Shampoo — primer contacto', params: ['encuestada', 'encuestador', 'hora'] },
    in_home_beta_385: { key: 'in_home_beta_385', label: 'In Home Beta 385', params: ['encuestada', 'encuestador', 'hora_asignada'] },
};

const ctx = {
    document: { getElementById: id => els[id] || el(id), querySelector: () => null },
    waTemplateCatalogMap: catalogo,
    waNewChatStudies: [
        { id: 1, single_template_keys: ['manana_3', 'shampo_primer'] },
        { id: 2, single_template_keys: ['in_home_beta_385', 'manana_3'] },
    ],
    waEsc: s => String(s),
    waToggleNewChatLink: () => {},
    console,
};
vm.createContext(ctx);
vm.runInContext(fns, ctx);

const fallas = [];
function check(cond, msg) {
    console.log((cond ? '  OK    ' : '  FALLA ') + msg);
    if (!cond) fallas.push(msg);
}

const union = ctx.waNewChatAllSingleKeys();
check(JSON.stringify(union) === JSON.stringify(['manana_3', 'shampo_primer', 'in_home_beta_385']),
    `union de estudios activos, sin duplicados -> ${JSON.stringify(union)}`);

ctx.waPopulateNewChatTemplates(union);
const valor = els['waNewChatKind'].value;
check(!['filter', 'form', ''].includes(valor),
    `sin estudio elegido, el select queda con una key valida -> ${JSON.stringify(valor)}`);
check(!!catalogo[valor], `la key ${JSON.stringify(valor)} existe en el catalogo`);

if (fallas.length) {
    console.error(`\n${fallas.length} falla(s).`);
    process.exit(1);
}
console.log('\nTodo OK.');
