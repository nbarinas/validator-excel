#!/usr/bin/env node
/**
 * Verifica que waLoadTemplateCatalog() refresque el catalogo en cada llamada.
 *
 * Por que: GET /whatsapp/templates ya no es global, depende de las conexiones por
 * estudio que cambia el superusuario (S10 del doc `odd/tasks/plantillas-una-por-una.md`).
 * Con el short-circuit `if (waTemplateCatalog) return waTemplateCatalog;` el catalogo
 * quedaba cacheado para toda la vida de la pagina: si el superusuario conectaba una
 * plantilla mientras el agente tenia la pagina abierta, al reabrir el modal 1x1 los
 * selectores buscaban la key nueva en `waTemplateCatalogMap` (ausente), la tiraban y
 * la plantilla no aparecia hasta un F5.
 *
 * Ojo: este test tambien falla contra HEAD, porque el cache es previo. El filtro por
 * estudio es lo que convierte ese cache inocuo en un bug real.
 *
 * Extrae waLoadTemplateCatalog del codigo real y lo ejecuta con un `fetch` falso que
 * primero devuelve ['manana_3'] y despues ['manana_3', 'fatiga_729_r3'] (simula que, con la
 * pagina abierta, el superusuario conecto fatiga_729_r3 al estudio del agente).
 *
 * Uso:    node scripts/tests/check_template_catalog_refresh.js [ruta/call_center.js]
 * Salida: 0 = todo OK; 1 = hay diferencias.
 */
const fs = require('fs');
const vm = require('vm');

const ruta = process.argv[2] || 'frontend/call_center.js';
const src = fs.readFileSync(ruta, 'utf8');

// waLoadTemplateCatalog es `async`, asi que el recorte tiene que arrancar en `async function`.
function extraer(nombre) {
    const inicio = src.indexOf('async function ' + nombre + '(');
    if (inicio === -1) throw new Error('no encontre async function ' + nombre);
    let depth = 0;
    for (let j = src.indexOf('{', inicio); j < src.length; j++) {
        if (src[j] === '{') depth++;
        else if (src[j] === '}' && --depth === 0) return src.slice(inicio, j + 1);
    }
    throw new Error('no pude cerrar ' + nombre);
}

const fn = extraer('waLoadTemplateCatalog');

// Respuestas del servidor, en orden: la segunda incluye la plantilla recien conectada.
const respuestas = [['manana_3'], ['manana_3', 'fatiga_729_r3']];
let fetchLlamadas = 0;

const ctx = {
    // Los dos globales que declara call_center.js antes de la funcion (null / {} iniciales).
    waTemplateCatalog: null,
    waTemplateCatalogMap: {},
    // El filtro de keys ocultas no es el tema de este test; se deja vacio.
    HIDDEN_TEMPLATE_KEYS: [],
    headers: {},
    fetch: async function () {
        const keys = respuestas[Math.min(fetchLlamadas, respuestas.length - 1)];
        fetchLlamadas++;
        return {
            ok: true,
            json: async function () {
                return keys.map(function (key) {
                    return { key: key, label: key, body: 'cuerpo ' + key };
                });
            },
        };
    },
    console: console,
};
vm.createContext(ctx);
vm.runInContext(fn, ctx);

const fallas = [];
function check(cond, msg) {
    console.log((cond ? '  OK    ' : '  FALLA ') + msg);
    if (!cond) fallas.push(msg);
}

function claves(lista) {
    return (lista || []).map(function (t) { return t.key; });
}

(async function () {
    console.log('[1] Primera apertura de modal: pide el catalogo y devuelve lo conectado');
    const primero = await ctx.waLoadTemplateCatalog();
    check(fetchLlamadas === 1, 'hizo 1 fetch en la primera llamada');
    check(JSON.stringify(claves(primero)) === '["manana_3"]',
        'el primer fetch da ["manana_3"] -> ' + JSON.stringify(claves(primero)));

    console.log('[2] Segunda apertura: el superusuario conecto fatiga_729_r3 con la pagina abierta');
    const segundo = await ctx.waLoadTemplateCatalog();
    check(fetchLlamadas === 2,
        'volvio a pedir /whatsapp/templates (fetches totales: ' + fetchLlamadas + ')');
    check(claves(segundo).indexOf('fatiga_729_r3') !== -1,
        'el segundo fetch incluye fatiga_729_r3 -> ' + JSON.stringify(claves(segundo)));
    check(JSON.stringify(claves(segundo)) === '["manana_3","fatiga_729_r3"]',
        'el catalogo vigente es ["manana_3","fatiga_729_r3"]');
    check(JSON.stringify(claves(ctx.waTemplateCatalog)) === '["manana_3","fatiga_729_r3"]',
        'waTemplateCatalog se refresco con el resultado nuevo');

    console.log('[3] Los selectores leen waTemplateCatalogMap: la key nueva tiene que estar');
    check(ctx.waTemplateCatalogMap && ctx.waTemplateCatalogMap['fatiga_729_r3'] !== undefined,
        "waTemplateCatalogMap['fatiga_729_r3'] esta seteado (si falta, el selector tira la key)");
    check(ctx.waTemplateCatalogMap['fatiga_729_r3'] &&
        ctx.waTemplateCatalogMap['fatiga_729_r3'].key === 'fatiga_729_r3',
        "waTemplateCatalogMap['fatiga_729_r3'] es el item del catalogo");
    check(ctx.waTemplateCatalogMap['manana_3'] !== undefined,
        "waTemplateCatalogMap['manana_3'] sigue estando");

    console.log('[4] Regresion: si /whatsapp/templates falla, el catalogo queda vacio y no rompe');
    // El catch real hace console.error; se silencia aca para no ensuciar la salida del test.
    ctx.console = { error: function () {}, log: console.log };
    ctx.fetch = async function () {
        return { ok: false, json: async function () { return []; } };
    };
    const roto = await ctx.waLoadTemplateCatalog();
    check(JSON.stringify(claves(roto)) === '[]',
        'el try/catch sigue dejando el catalogo vacio cuando el fetch falla');
    check(Object.keys(ctx.waTemplateCatalogMap).length === 0,
        'y el mapa queda vacio (no se conservan keys viejas)');

    if (fallas.length) {
        console.log('\n' + fallas.length + ' fallas.');
        process.exitCode = 1;
    } else {
        console.log('\nTodo OK.');
    }
})().catch(function (e) {
    console.error(e);
    process.exitCode = 1;
});
