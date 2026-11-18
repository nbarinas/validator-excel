# Plantillas SunTea durazno R1 + Sibate 250 (4 keys)

Se suman cuatro plantillas de WhatsApp al catálogo, al envío 1x1 y al envío masivo, con vista
previa byte-idéntica en el front, siguiendo el camino de `shampo_729` y `853_sin_bono`.

## Specs

- **S1** `suntea_durazno_r1` (es). Parámetros `encuestada`, `encuestador`, `hora`. Cuerpo verbatim:

```
Hola, señora {{encuestada}}, ¿cómo está? 😊

Le saluda {{encuestador}}, del equipo de AZ Marketing Plus.

El motivo de mi mensaje es recordarle que hace aproximadamente una semana le dejamos una muestra de SunTea sabor a durazno para que pudiera prepararla y probarla en casa.

El día de hoy tenemos programada nuestra videollamada a las {{hora}}.

¿En este momento tendría unos minutos disponibles para realizarla?

Muchas gracias por su tiempo y colaboración. ¡Que tenga un feliz día! 🌷
```

- **S2** `entrega_sibate_250` (es). Parámetro `encuestada`. Cuerpo verbatim (conserva el doble
  espacio de "partir  de hoy" y las comillas rectas de "RECIBIDO"):

```
Hola, {{encuestada}} 😊

Te saluda el equipo de AZ Marketing Plus.

Te escribimos para confirmar que el transportador ya te hizo entrega del producto, que comenzarás a utilizar a partir  de hoy

Por favor, respóndenos "RECIBIDO" para confirmar que ya lo tienes.

¡Muchas gracias! 🙌
```

- **S3** `concentrado__producto_semana_16_de_noviembre_250` (es). Parámetros `encuestada`,
  `mascota`, `censo`. Cuerpo verbatim (arranca con "AZ Marketing Plus" y cierra cortado en
  "...y explicar"):

```
AZ Marketing Plus
Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.

¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas gracias por seguir participando y por tu compromiso.

📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer su concentrado habitual, mezclado con el suplemento que te enviamos.

🍽️ ¿Qué debes hacer cada día?

1. Sirve el alimento mezclado con el suplemento.
2. Mide el tiempo desde que le sirves hasta que termine de comer.
3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.
4. Al finalizar, diligencia la encuesta del día.

⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o cena, procurando mantener el mismo horario durante los 7 días.

codigo {{censo}}

🔗 Enlace para registrar tu actividad diaria:
https://forms.gle/FQpVjm9oxPRACPUt8

Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp para realizar la última encuesta y explicar
```

- **S4** `recordatorio_sibate_semana_16_de_noviembre_250` (es). Parámetros `dia`, `encuestada`,
  `mascota`, `censo`; requiere el día en el masivo. Cuerpo verbatim (arranca con "Saludos" y
  cierra cortado en "...del estudi"):

```
Saludos
🐶 REGISTRO DIARIO – DÍA {{dia}}/7

¡Hola, {{encuestada}}! 👋 Te saluda el equipo de AZ Marketing Plus.

🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 204).

🍽️ Registra una sola comida al día, manteniendo el mismo horario.

⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.

🔢 Código de registro: {{censo}}

🔗 Diligencia aquí la encuesta:
https://forms.gle/FQpVjm9oxPRACPUt8

¡Gracias por tu compromiso! 💚
Recuerda completar el registro durante los 7 días del estudi
```

- **S5** Las cuatro keys quedan disponibles en el envío 1x1 (`WHATSAPP_SINGLE_TEMPLATE_KEYS`), en
  el envío masivo (`WHATSAPP_TEMPLATE_MAP` + `BULK_TEMPLATE_VARS`) y en la vista previa
  (`WHATSAPP_TEMPLATE_BODIES` del backend y `WA_TEMPLATE_BODIES` del front, byte-idénticos).

## Tasks

- T1 · S1-S5 · inline · commit 1 — Catálogo y cuerpos en backend + front, checks y runner.

## Log

- L1 (pedido del usuario, verbatim):

```
cree 4 plantillas que quiero que las agregues al 1x1, masivo y vista, primera suntea_durazno_r1 · Spanish dice Hola, señora {{encuestada}}, ¿cómo está? 😊

Le saluda {{encuestador}}, del equipo de AZ Marketing Plus.

El motivo de mi mensaje es recordarle que hace aproximadamente una semana le dejamos una muestra de SunTea sabor a durazno para que pudiera prepararla y probarla en casa.

El día de hoy tenemos programada nuestra videollamada a las {{hora}}.

¿En este momento tendría unos minutos disponibles para realizarla?

Muchas gracias por su tiempo y colaboración. ¡Que tenga un feliz día! 🌷
12:07 pm
De una vez
Mas tarde , segunda entrega_sibate_250 · Spanish y dice Hola, {{encuestada}} 😊

Te saluda el equipo de AZ Marketing Plus.

Te escribimos para confirmar que el transportador ya te hizo entrega del producto, que comenzarás a utilizar a partir  de hoy

Por favor, respóndenos "RECIBIDO" para confirmar que ya lo tienes.

¡Muchas gracias! 🙌
12:07 pm
Recibido
No estoy segura , tercera concentrado__producto_semana_16_de_noviembre_250 · Spanish que dice AZ Marketing Plus
Hola, {{encuestada}}. ¡Buenos días! Te saluda el equipo de AZ Marketing Plus.

¡Hoy comenzamos la segunda fase del estudio con tu mascota {{mascota}}! 🐾 Muchas gracias por seguir participando y por tu compromiso.

📅 Durante los próximos 7 días, deberás medir el tiempo que tu perrito tarda en comer su concentrado habitual, mezclado con el suplemento que te enviamos.

🍽️ ¿Qué debes hacer cada día?

1. Sirve el alimento mezclado con el suplemento.
2. Mide el tiempo desde que le sirves hasta que termine de comer.
3. Observa si empieza a comer de inmediato o si primero olfatea el alimento.
4. Al finalizar, diligencia la encuesta del día.

⏰ La actividad se realiza una sola vez al día. Puedes elegir el desayuno, almuerzo o cena, procurando mantener el mismo horario durante los 7 días.

codigo {{censo}}

🔗 Enlace para registrar tu actividad diaria:
https://forms.gle/FQpVjm9oxPRACPUt8

Bono de $30.000: Al completar los 7 días, nos comunicaremos contigo por WhatsApp para realizar la última encuesta y explicar
12:07 pm
De una vez, porfa
Mas tarde y la cuarta recordatorio_sibate_semana_16_de_noviembre_250 · Spanish que dice Saludos
🐶 REGISTRO DIARIO – DÍA {{dia}}/7

¡Hola, {{encuestada}}! 👋 Te saluda el equipo de AZ Marketing Plus.

🐾 Hoy debes registrar el consumo de tu mascota, {{mascota}}, del concentrado mas  el producto entregado (código 204).

🍽️ Registra una sola comida al día, manteniendo el mismo horario.

⏱️ Mide el tiempo que tarda en comer y registra su comportamiento en la encuesta.

🔢 Código de registro: {{censo}}

🔗 Diligencia aquí la encuesta:
https://forms.gle/FQpVjm9oxPRACPUt8

¡Gracias por tu compromiso! 💚
Recuerda completar el registro durante los 7 días del estudi
12:08 pm
De una Vez
Mas tarde , al terminas haz commit en la rama main y me avisas
```

- L2 — Decisiones: la hora del chat ("12:07 pm"), los botones de respuesta rápida ("De una vez",
  "Mas tarde") y los rótulos "· Spanish"/"que dice" quedan afuera, igual que en las entregas
  anteriores. El nombre con doble guion bajo (`concentrado__producto_...`) se conserva verbatim
  tal como vino en el pedido, porque es el identificador de Meta. Los cortes del pedido
  ("...y explicar", "...del estudi") se conservan verbatim. No se toca el mapeo de variables:
  `encuestada`, `encuestador`, `hora`, `mascota`, `censo` y `dia` ya se resuelven en
  `whatsapp_send_template` y `whatsapp_send_bulk`.
