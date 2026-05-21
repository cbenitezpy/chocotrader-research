# Research v6 — Pre-registro de hipótesis

**Fecha de pre-registro:** 2026-05-20
**Status:** SEALED — modificaciones requieren ADR enmienda a ADR-023
**Author:** Cristhian Benitez
**Hash de este documento al sellar:** (se calcula tras commit inicial)

---

## 1. Propósito

Este documento congela las hipótesis, gates, datasets y reglas de decisión **ANTES de mirar cualquier dato**. La disciplina de pre-registro evita el data snooping documentado en `lessons-learned-final.md` §3.1.

Toda modificación post-mirada-de-datos requiere ADR formal enmendando ADR-023. Las modificaciones en datasets sin ADR invalidan automáticamente los resultados.

---

## 2. Hipótesis y gates

### H1 — Fear & Greed extremos como señal contrarian

**Tesis falsable**: Cuando F&G ∈ [0, 25] (Extreme Fear), el retorno forward 7-30 días en BTC tiene esperanza positiva mayor que el promedio histórico.

**Fuente de datos**: alternative.me API (gratis, 3027 días desde 2018-02-01).

**Modelados**:
- **H1-filter**: SuperTrend BUY se ejecuta solo si F&G ≤ 25 en el día previo. SELL se mantiene igual que SuperTrend solo.
- **H1-standalone**: BUY cuando F&G cruza ≤ 25 (entry). SELL cuando F&G cruza ≥ 75 (exit) **o** stop loss -10% desde entry.

**Hipótesis nula (H0)**: F&G no aporta información direccional sobre BTC forward 7-30 días.

**Métricas pre-registradas**:
- Sharpe sobre B&H BTC (delta)
- MaxDD
- Profit factor
- Win rate
- Trades totales
- Promedio días en posición

**Gate de promoción**: ver §3.

---

### H3 — Funding rate de perpetuals como sentiment de spot

**Tesis falsable**: Funding rate sostenido > 0.05% (8h) en BTC perp anticipa retornos forward 1-7 días negativos en BTC spot. Funding < −0.02% anticipa positivos.

**Fuente de datos**: Binance fapi public (`/fapi/v1/fundingRate`). Histórico desde lanzamiento de cada perp (~2019-09 para BTC).

**Modelados**:
- **H3-filter**: SuperTrend BUY se ejecuta solo si funding rate promedio 24h < 0.03%. SELL se ejecuta si SuperTrend señala SELL **o** funding > 0.06% promedio 24h.
- **H3-standalone**: BUY spot cuando funding < −0.01% (8h, último). SELL cuando funding > 0.05%. Sin SuperTrend.

**H0**: Funding rate no contiene información direccional sobre spot forward.

**Literatura de referencia**: Soska et al. 2021, Alexander & Heck 2023. Edge documentado pero corto en horizonte y susceptible de erosión por crowding institucional.

**Riesgo metodológico identificado**: El usuario opera SPOT, no perpetuals. La señal viene de un mercado donde no se opera. Mitigación: validar que el lag entre signal y fill (spot next-open) no destruye el edge. Pre-test conceptual obligatorio en Fase 2.

---

### H5 — DXY como filtro macro

**Tesis falsable**: Cuando DXY está en uptrend 20d (close > MA20 y MA20 ascending), el retorno forward 7-14d en BTC tiene esperanza negativa o nula.

**Fuente de datos**: FRED `DTWEXBGS` (Broad Dollar Index) o `DTWEXAFEGS` (Advanced Foreign Economies). Histórico décadas. Backup: Yahoo `DX-Y.NYB`.

**Modelados**:
- **H5-filter**: SuperTrend BUY se ejecuta solo si DXY NO está en uptrend 20d.
- **H5-standalone**: BUY BTC cuando DXY cruza por debajo de MA20. SELL cuando cruza arriba.

**H0**: DXY no anticipa retornos en BTC en horizonte 7-14d.

**Riesgo metodológico identificado**: La relación BTC↔DXY es régime-dependent. Fuerte inversa 2022-2024, débil pre-2020 y post-2025. La hipótesis puede tener edge en un régime y anti-edge en otro. Walk-forward debe capturar esto.

---

## 3. Gates de promoción (pre-registrados)

Cada hipótesis y modelado se evalúa contra los **mismos gates**, sin ajuste post-hoc:

| Gate | Umbral | Aplicable en |
|---|---|---|
| Δ Sharpe vs B&H BTC | ≥ +0.20 | Train+val |
| Δ Sharpe vs B&H BTC | ≥ +0.15 | Walk-forward W3 |
| Δ Sharpe vs B&H BTC | ≥ +0.10 | OOS forward-test (mínimo 4 meses de datos) |
| MaxDD absoluto | ≤ 25% | Todas las ventanas |
| Profit Factor | ≥ 1.3 | Train+val |
| Trades totales | ≥ 50 | Train+val (sample size estadístico) |
| Sharpe absoluto train+val | ≥ 0.8 | (criterio secundario, no decide solo) |

**Nota sobre el umbral OOS bajado a +0.10**: el usuario lo acordó explícitamente conociendo el trade-off — un edge de +0.10 Sharpe sostenido vs B&H BTC es "mejora leve pero real". Subimos la probabilidad de pasar a costa de menor magnitud esperada en live. La progresión train(+0.20) → walk-forward(+0.15) → OOS(+0.10) refleja la degradación natural in-sample → out-of-sample.

**Reglas de tie-breaking y decisión**:

1. Una hipótesis pasa **solo si cumple TODOS los gates de su ventana** (todos los AND).
2. Si más de una pasa, se elige la de mayor Δ Sharpe en walk-forward W3.
3. "Casi pasa" (Δ Sharpe entre +0.05 y +0.10 en OOS) = **FAIL**. No se reabren gates.
4. "Promedio sobre los 2 modelados" no es válido — cada modelado se evalúa independiente.
5. Combinaciones de hipótesis (ensembles) NO están pre-registradas. Cualquier ensemble sería data snooping y queda explícitamente prohibido en v6.

---

## 4. Datasets y splits

### 4.1 OHLCV
- BTC/USDT, ETH/USDT 4h (primarios)
- SOL/USDT, BNB/USDT 4h (secundarios para H2)
- Source: `data/ohlcv/*_4h_*.parquet` existente
- Coverage: 2017-08 a 2026-05 (verificar al fetchear)

### 4.2 External inputs
- F&G daily: 2018-02-01 a "today" (research/v6/data/external/fng_daily.parquet)
- Funding rate 8h: 2019-09 a "today" (research/v6/data/external/funding_btc_8h.parquet, idem ETH si aplica)
- DXY daily: 2018-01 a "today" (research/v6/data/external/dxy_daily.parquet)

### 4.3 Splits temporales

| Split | Rango | Uso |
|---|---|---|
| Train | [2018-02-01, 2024-12-31] | Optimización + estimación de parámetros |
| Val | [2025-01-01, 2026-04-30] | Validación de overfitting (sin tuning sobre val) |
| Walk-forward W1/W2/W3 | Ventanas 2-año dentro de train+val | Estimación predictiva OOS |
| **OOS (forward-only)** | [2026-05-20, end-of-v6] | **Reservado físicamente** (chmod 0444). Una sola corrida al final. |

Alineación entre OHLCV (4h) y external (daily / 8h):
- Cada vela 4h hereda el último valor disponible de la fuente externa (forward-fill explícito, sin look-ahead).
- Funding rate (8h) se alinea con la vela 4h que cubre el timestamp de funding.
- Documentado en `research/v6/data/alignment_spec.md` (a crear en Fase 1).

---

## 5. Fill model

**Default obligatorio**: `fill_mode = next_open`. Signal emitida al cierre de vela N, fill al open de vela N+1.

Comisiones: 0.10% por lado (0.20% round-trip), sin BNB discount.
Slippage modelado: 0.05% por lado en BTC/ETH, 0.10% en alts.
Costo total round-trip mínimo: 0.30% BTC/ETH, 0.40% alts.

**Cualquier cambio al fill model requiere ADR enmienda a ADR-023.**

---

## 6. Procedimiento para cada experimento

1. Implementar la función de señal en `research/v6/signals/Hx_<variant>.py` como función pura `(ohlcv, external_inputs) -> Series[int]`.
2. Correr backtest sobre **train+val** con fill realista. Loguear en `research/v6/results/run_log.jsonl`.
3. Correr walk-forward W1/W2/W3 sobre train. Loguear deltas predichos.
4. Generar report en `research/v6/reports/Hx_<variant>.md` con tabla:
   - Fila 1 SIEMPRE: B&H BTC del período.
   - Filas siguientes: la estrategia evaluada con todas las métricas pre-registradas.
5. Si pasa gates de train+val + walk-forward → candidata a OOS.

---

## 7. Procedimiento OOS

1. Solo se accede al OOS si al menos una hipótesis pasó §6 paso 5.
2. **Una corrida por hipótesis candidata, sin reintento**.
3. Loguear en `research/v6/oos_access.json` con timestamp y razón.
4. Calcular métricas y compararlas contra gates §3.
5. Generar report final `research/v6/reports/OOS_FINAL.md`.

---

## 8. Anti-patrones explícitamente prohibidos

| Anti-patrón | Razón |
|---|---|
| Ajustar gates después de ver resultados | Data snooping del peor tipo |
| Probar "una variante más" porque la actual falló | Crowding del espacio de búsqueda |
| Ensembles ad-hoc combinando hipótesis que pasaron | No pre-registrado |
| Mirar OOS antes de pasar walk-forward | Quema el OOS |
| Cambiar parámetros internos (períodos, umbrales) post-hoc | Optimización implícita |
| Reusar el OOS quemado por v1-v5 (2024-2025) | Ya contaminado |
| "El gate está cerca, hagamos una excepción" | Es la frase que ADR-012 explícitamente vetó |
| Saltarse el commit del pre-registro inicial | El hash de este documento debe quedar fijo en historia |

---

## 9. Cronograma estimado

| Fase | Estimación | Status |
|---|---|---|
| Fase 0 — ADR + pre-registro | 3-4h | COMPLETADA |
| Fase 1 — data pipeline (3 fuentes) | 6-8h | EN CURSO |
| Fase 2 — 6 signal generators | 9-12h | Pendiente |
| Fase 3 — backtest train+val+walk-forward | 12-15h | Pendiente |
| Fase 4 — OOS (condicional) | 3-5h | Pendiente |
| Fase 5 — reporte + ADR cierre/promoción | 3-5h | Pendiente |
| **Total** | **36-49h** | |

Time-box duro: **45h o 2026-07-31**, lo que ocurra primero.

**Scope reducido vs versión inicial**: H2 (BTC dominance) dropeada por riesgo metodológico de look-ahead. Decisión documentada en ADR-023 §2.1.

---

## 10. Sello

Este documento queda congelado al primer commit. Cualquier modificación post-commit:
1. Debe estar acompañada de ADR formal enmendando ADR-023.
2. Invalida los resultados de cualquier experimento ya corrido si la modificación afecta los gates, splits, fuentes de datos o fill model.

**Commit inicial pendiente**: este pre-registro debe commitearse a `main` antes de iniciar Fase 1.
