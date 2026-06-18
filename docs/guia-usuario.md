# Guía de usuario — HealthTech

Esta guía está dirigida al **cuidador o administrador** que configura y supervisa el
dispensador de medicamentos desde la interfaz web. No requiere conocimientos técnicos.

---

## ¿Qué hace el dispensador?

HealthTech es un dispensador semanal de medicamentos. Tiene un carrusel con un
compartimento para cada día de la semana. A la hora indicada, el carrusel coloca el
compartimento del día frente al punto de retiro y, mediante una balanza interna, **verifica
que el medicamento haya sido efectivamente retirado** detectando la caída de peso.

Cada evento queda registrado con su fecha y hora, indicando si el medicamento se retiró
correctamente o no.

---

## Cómo acceder a la interfaz

1. Asegurate de que el dispensador (Raspberry Pi) y tu dispositivo estén en la **misma red
   Wi-Fi**.
2. Abrí el navegador y entrá a la dirección de la interfaz (por defecto, en desarrollo:
   `http://localhost:5173`).
3. Vas a ver el panel principal con cinco pestañas: **Estado**, **Horarios**, **Registros**,
   **Dispensar** y **Diagnóstico**.

En la esquina superior derecha, un indicador muestra si la interfaz está **conectada en
tiempo real** con el dispositivo (WebSocket: ● Conectado / ○ Desconectado).

---

## Pestaña «Estado»

Muestra de un vistazo la situación actual del dispensador:

- **Día actual** y compartimento correspondiente.
- **Próximo evento** programado.
- **Último evento** registrado (si el medicamento se retiró o no).
- Estado de la **conexión Wi-Fi**.
- Si el sistema está **ocupado** (dispensando en este momento).

Esta pantalla se actualiza sola cada vez que ocurre una dispensación.

---

## Pestaña «Horarios»

Acá configurás **cuándo y qué días** debe recordarse la toma del medicamento.

Cada horario tiene:

- **Hora** en formato 24 h (por ejemplo, `08:00` o `20:00`).
- **Días** de la semana en que aplica (lunes a domingo).
- **Mensaje** de recordatorio (por ejemplo, *"Es hora de tomar su medicamento de la
  mañana"*).
- Un interruptor para **activarlo o desactivarlo** sin borrarlo.

### Para crear o editar un horario

1. Agregá un horario nuevo o editá uno existente.
2. Ingresá la hora en formato `HH:MM`. Si el formato es inválido, el sistema lo rechaza y te
   avisa.
3. Seleccioná los días que correspondan.
4. Escribí el mensaje del recordatorio.
5. Guardá. Los cambios se aplican **al instante**, sin necesidad de reiniciar nada.

> **Importante.** Al llegar la hora de un horario habilitado, el dispensador **acciona el
> carrusel automáticamente** y queda esperando a que retires el medicamento (lo verifica por
> la caída de peso). Los cambios en los horarios se aplican al instante, sin reiniciar.
> También podés iniciar una dispensación en cualquier momento desde la pestaña «Dispensar».
> Los horarios se interpretan en hora UTC.

---

## Pestaña «Registros»

Lista el **historial de eventos**, del más reciente al más antiguo. Para cada evento vas a
ver:

- Fecha y hora (en UTC).
- Día y compartimento.
- Resultado: **OK** (medicamento retirado) o **FAIL** (no se detectó el retiro).

Esto te permite, como cuidador, confirmar la adherencia al tratamiento: si aparece un
**FAIL**, significa que el medicamento no fue retirado en la ventana esperada.

---

## Pestaña «Dispensar»

Permite **iniciar una dispensación manual**. Al accionarla, el dispensador:

1. Gira el carrusel hasta el compartimento del día actual.
2. Pone la balanza a cero (tara).
3. Espera a que retires el medicamento (detecta la caída de peso).
4. Registra el resultado (OK / FAIL) y lo muestra.

Mientras dura el proceso, el sistema queda **ocupado** y las acciones de diagnóstico se
bloquean para no interferir.

---

## Pestaña «Diagnóstico»

Pensada para **pruebas y mantenimiento** del hardware. Permite operar manualmente el motor
y la balanza:

- **Paso del servo**: avanza el carrusel un compartimento.
- **Home**: lleva el carrusel a la posición inicial (punto de recarga).
- **Peso**: muestra la lectura actual de la balanza. Podés activar la lectura **en vivo**
  para ver cómo cambia en tiempo real.
- **Poner a cero (tara)**: fija el cero de la balanza.

> Si la balanza aún **no está calibrada**, las lecturas se muestran en cuentas crudas del
> sensor, no en gramos. La calibración se hace una sola vez sobre el hardware real (ver el
> README, sección de calibración).

---

## Tareas habituales del cuidador

### Recargar los compartimentos (semanal)

1. Llevá el carrusel a **Home** desde la pestaña Diagnóstico.
2. Cargá cada compartimento con la dosis del día correspondiente (lunes a domingo).
3. Verificá en la pestaña Estado que el día y compartimento sean los correctos.

### Verificar que el paciente tomó su medicación

1. Entrá a la pestaña **Registros**.
2. Revisá los eventos del día: un **OK** confirma el retiro; un **FAIL** indica que no se
   detectó.

---

## Solución de problemas

| Síntoma | Posible causa | Qué hacer |
|---|---|---|
| La interfaz muestra «○ Desconectado» | La Pi no responde o cambió de red. | Verificá que el dispositivo esté encendido y en la misma red Wi-Fi. La interfaz reintenta sola cada pocos segundos. |
| La lectura de peso aparece en valores raros (no gramos) | La balanza no está calibrada. | Ejecutá la calibración (ver README). Hasta entonces, los valores son cuentas crudas del sensor. |
| Toda dispensación da **FAIL** | El medicamento no se retira en la ventana, o la balanza falla. | Probá leer el peso en Diagnóstico; si da error de sensor, revisá el cableado del HX711. |
| El diagnóstico responde «ocupado» (error 409) | Hay una dispensación en curso. | Esperá a que termine y reintentá. |
| Un horario no se guarda | El formato de hora es inválido. | Usá el formato `HH:MM` de 24 h (por ejemplo `09:30`). |

---

## Documentos relacionados

- [README](../README.md) — instalación y puesta en marcha.
- [Arquitectura](./arquitectura.md) — cómo funciona por dentro.
- [Referencia de API](./referencia-api.md) — para integraciones técnicas.
