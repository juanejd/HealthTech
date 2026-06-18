# Plan de Verificación — HealthTech (dispensador de medicamentos)

> Estado base: rama `main`, commit `a20e01e`. Suite de tests: **69 passed** (modo mock).
> Hardware as-built: FS90R (GPIO18) + HX711 DT=GPIO17 / SCK=GPIO23. Sin pulsador.

## 0. Qué verifican (y qué NO) los tests actuales

| Capa | Herramienta | Qué prueba | Qué NO prueba |
|------|-------------|-----------|---------------|
| Lógica / contrato | `pytest` (69 tests, mock) | Cálculo de compartimento, flujo `/dispense`, scheduler, fault-tolerance, manejo de estados | Que el servo gire 45° reales; que el HX711 mida gramos reales |
| Smoke de hardware | `hw_selftest.py` | Que el servo gire y el sensor responda, de forma secuencial y manual | Precisión angular, calibración en gramos, latencia, deriva acumulada |

**Conclusión:** los tests verdes prueban el software, no el sistema físico. Para que los **requerimientos** se cumplan hay que cubrir la brecha de hardware con pruebas medibles y dos scripts nuevos.

---

## 1. Pruebas de regresión (sin hardware — corren en cualquier PC)

```bash
cd backend
python -m pytest -q          # esperado: 69 passed
```

Correr esto **antes y después** de cualquier cambio. Es la red de seguridad de la lógica.

---

## 2. Pruebas de hardware en la Raspberry Pi (manual)

```bash
cd backend
python3 scripts/hw_selftest.py
```

Cubre el smoke test: giro del servo, lectura continua del HX711, un paso + confirmación.
**Limitación:** no mide nada — solo te deja ver a ojo. No alcanza para validar requerimientos.

---

## 3. Brechas de requerimientos y scripts faltantes

### 3.1 RF-3 — Detección de extracción (BLOQUEANTE) → falta `hx711_calibrate.py`

**Problema:** `CALIBRATION_FACTOR = 1.0` y `DROP_THRESHOLD_G = 5.0` (gramos).
Con factor 1.0, `read_weight()` devuelve **cuentas crudas del ADC, no gramos**, así que un
umbral de "5 gramos" no significa nada. **RF-3 no puede funcionar sin calibrar primero.**

**Script a crear:** `backend/scripts/hx711_calibrate.py`
1. `tare()` con la bandeja vacía.
2. Pedir al operador que coloque un peso conocido (ej. 50 g).
3. Leer crudo, calcular `CALIBRATION_FACTOR = peso_conocido / (raw - tara)`.
4. Persistir el factor (a `config/` o `logs/`) para que `sensor_manager` lo cargue al arrancar.
5. Repetir la lectura 20–30 veces e imprimir media y desvío.

**Doble función — diagnóstico:** si en el paso 5 las lecturas **saltan erráticamente**, eso
confirma el problema conocido del bit-bang de gpiozero (los `.on()/.off()/.value` tardan
~100 µs, el SCK queda HIGH >60 µs y el HX711 entra en power-down a mitad de lectura). Si el
desvío es enorme, hay que reescribir `_read_hx711_raw()` con lgpio directo antes de seguir.

> ⚠️ Riesgo abierto: `_read_hx711_raw()` devuelve `_MOCK_RAW_VALUE` en timeout DRDY
> (`sensor_manager.py:102`) y en excepción (`:130`). En hardware real eso **enmascara fallos**:
> el sensor parece andar devolviendo un valor fijo. La calibración lo expone enseguida.

### 3.2 RF-2 — Posicionamiento del carrusel → falta calibración de paso

**Problema:** `STEP_DURATION_S = 0.25` es un valor tentativo. No hay garantía de que un paso
sean 45° reales, ni de que 8 pasos vuelvan exactamente a home (deriva acumulada).

**Prueba a realizar (con el script de calibración de servo, ver 3.4):**
- Ejecutar 8 `step_one_compartment()` seguidos y verificar que el carrusel da **una vuelta
  completa y vuelve a home** (marca física de referencia).
- Si se pasa o no llega: ajustar `STEP_DURATION_S` y repetir.

### 3.3 RNF-2 — Latencia activación→movimiento ≤ 200 ms → prueba de tiempo

**Problema:** hoy `step_one_compartment()` construye un `Servo()` nuevo en cada llamada y el
paso dura 250 ms. Hay que medir el tiempo entre **invocación → inicio de movimiento** (no la
duración del giro) y confirmar que entra en 200 ms.

**Prueba:** instrumentar con `time.monotonic()` alrededor de la creación del servo + primer
comando de velocidad. Si la construcción del `Servo()` se come el presupuesto, cachear la
instancia en vez de recrearla por paso.

### 3.4 Script de calibración de servo (recomendado) → `servo_calibrate.py`

Pequeño asistente para encontrar `STEP_DURATION_S` y `DIRECTION`:
1. Gira un paso, pregunta "¿giró 45°? ¿en qué dirección?".
2. Permite ajustar duración en caliente y reintentar.
3. Imprime el valor final a fijar en `servo_controller.py`.

---

## 4. Pruebas de flujo end-to-end (integración)

Con servo y sensor ya calibrados, levantar el backend en la Pi y disparar el ciclo real:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000   # ajustar al entrypoint real
curl -X POST http://localhost:8000/dispense
```

Verificar la respuesta `{"status": "OK", "extraction_detected": true, ...}` **con un pill real
cayendo**, y que el evento quede registrado (RF-6, log UTC) y encolado (RF-7).

---

## 5. Resumen — orden de ejecución

1. `pytest` verde (regresión lógica). ✅ ya pasa
2. `hx711_calibrate.py` (NUEVO) → calibrar gramos + diagnosticar estabilidad del sensor. **BLOQUEANTE para RF-3.**
3. `servo_calibrate.py` (NUEVO) → fijar `STEP_DURATION_S` real para 45°. **RF-2.**
4. Prueba de latencia ≤200 ms. **RNF-2.**
5. `hw_selftest.py` → smoke integrado.
6. `POST /dispense` end-to-end con pill real. **RF-3 + RF-6 + RF-7.**

> Nota: `docs/fases/fase-02-hardware.md` está desactualizado (describe SG90 + sensor IR +
> pulsador GPIO27). El as-built es FS90R + HX711 sin pulsador. Actualizar para que la doc
> refleje el hardware real.
