# Research v6 — Resultado Final

**Fecha:** 2026-05-20
**Status:** CERRADO — ninguna hipótesis pasa los gates pre-registrados.
**Capital arriesgado durante v6:** $0
**OOS quemado:** ninguno (no se accedió — pre-registro respetado).
**Decision:** Aceptar la conclusión expandida. No promover ninguna estrategia a live.

---

## 1. Resumen ejecutivo

De acuerdo con el ADR-023 y el pre-registro sellado el 2026-05-20, se evaluaron 6 experimentos (3 hipótesis × 2 modelados: filter sobre SuperTrend y standalone) sobre BTC/USDT 4h, usando 3 fuentes de datos externas no-técnicas (F&G index, funding rate de perpetuals BTC, DXY).

**Ningún experimento pasó el gate de walk-forward W3** (Δ Sharpe vs B&H BTC ≥ +0.15) — y la mayoría tampoco pasó el gate más laxo de train+val (Δ ≥ +0.20). El gate de OOS (Δ ≥ +0.10) ni siquiera se evaluó: el pre-registro lo prohíbe sin pasar walk-forward primero. El dataset OOS forward-only queda intocado para futuros research que cumplan condiciones del ADR-012.

El research previo (ADR-012, abril 2026) había cerrado las estrategias basadas en indicadores técnicos puros. **v6 expande esa conclusión**: agregar fuentes de información exógenas (sentiment retail F&G, derivatives funding rate, macro DXY) sobre la misma arquitectura long-only spot **tampoco produce edge consistente** sobre B&H BTC con costos realistas.

---

## 2. Gates pre-registrados y resultado

| Gate | Umbral | Aplicable | Resultado |
|---|---|---|---|
| Δ Sharpe train+val | ≥ +0.20 | Train+val | Solo SuperTrend baseline pasa (+0.282) — **no es nueva hipótesis del v6**. Las 6 hipótesis externas: máximo +0.034 (h3_funding_filter). |
| Δ Sharpe walk-forward W3 | ≥ +0.15 | W3 (2023-07 → 2026-04) | **NADIE pasa.** Mejor delta en W3: h3_funding_standalone con −0.877 (0 trades). |
| Δ Sharpe OOS forward | ≥ +0.10 | OOS | NO EVALUADO (pre-registro: requiere pasar W3 antes). |

Per ADR-023 §2.5 trigger #1: **"Ninguna hipótesis pasa walk-forward W3 → cierre con ADR-024."**

---

## 3. Resultados por experimento

### 3.1 Tabla principal — train+val 2018-02-01 → 2026-04-30

Ordenado por Δ Sharpe vs B&H BTC descendente:

| Experimento | Sharpe | Δ vs B&H | MaxDD | PF | Trades | Final $ | Veredicto |
|---|---:|---:|---:|---:|---:|---:|---|
| supertrend_baseline (referencia) | +0.972 | **+0.282** | -25.6% | 1.49 | 213 | $366 | Pasa gate train pero NO es hipótesis v6 |
| h3_funding_filter | +0.724 | +0.034 | -23.8% | 1.23 | 167 | $208 | NO pasa |
| h3_funding_standalone | +0.723 | +0.033 | -30.8% | 5.07 | 6 | $195 | NO pasa (sample chico) |
| h5_dxy_filter | +0.441 | -0.250 | -31.7% | 1.10 | 122 | $148 | NO pasa |
| h5_dxy_standalone | +0.207 | -0.483 | -41.4% | 1.04 | 144 | $118 | NO pasa |
| h1_fg_standalone | +0.048 | -0.642 | -37.7% | 1.02 | 8 | $94 | NO pasa |
| h1_fg_filter | -0.215 | -0.905 | -30.2% | 0.91 | 65 | $81 | NO pasa (peor que B&H) |
| **B&H BTC (baseline)** | **+0.690** | — | -77.0% | — | 1 | $673 | **Mejor en plata absoluta** |

### 3.2 Walk-forward W1 / W2 / W3

| Estrategia | Δ W1 | Δ W2 | Δ W3 | Pasa W3 |
|---|---:|---:|---:|:---:|
| h5_dxy_filter | +0.633 | +0.047 | -1.198 | ❌ |
| h3_funding_standalone | +0.572 | -0.476 | -0.877 | ❌ |
| supertrend_baseline | +0.500 | +0.555 | -0.457 | ❌ |
| h5_dxy_standalone | -0.305 | -0.706 | -0.720 | ❌ |
| h1_fg_standalone | -0.400 | -1.043 | -0.742 | ❌ |
| h3_funding_filter | -0.123 | +0.296 | -0.353 | ❌ |
| h1_fg_filter | -0.119 | -1.396 | -1.625 | ❌ |

Período W1: 2018-02 → 2020-09 (bull suave + crash COVID).
Período W2: 2020-10 → 2023-06 (mega bull + bear 2022).
Período W3: 2023-07 → 2026-04 (consolidación + bear suave 2025-2026).

**Patrón crítico**: estrategias que parecen tener edge en W1/W2 (bull markets) fallan en W3 (consolidación). **Edge regime-dependent ≠ edge persistente.** Esto matchea exactamente la firma de overfit a régimen documentada en `lessons-learned-final.md` §2.6-2.7.

---

## 4. Hallazgos honestos

### 4.1 H1 (Fear & Greed) es el peor performer del experimento

**Tesis original**: F&G ≤ 25 anticipa rebote en BTC.

**Realidad**: las dos variantes terminan PEOR que B&H en train+val.
- h1_fg_filter: Sharpe -0.215 (NEGATIVO), Δ = -0.905, $81 final.
- h1_fg_standalone: Sharpe +0.048, Δ = -0.642, $94 final.

**Razón inferida**: "comprar miedo" en cripto retail spot frecuentemente significa entrar en bear markets que tienen otros 30-60 días de caída por delante. La intuición popular "F&G bajo = oportunidad" es **estadísticamente falsa** en este universo con horizonte 1-4 semanas y posición spot long-only.

### 4.2 H3 (funding rate) es la única que se acerca al ruido

Sharpe absoluto cercano a B&H (+0.72 vs +0.69), pero **NO supera el umbral del gate** (+0.034 vs +0.20). En W3 cae a -0.353.

**Razón inferida**: el funding rate sí contiene información direccional pero el lag entre la señal (settled cada 8h) y la ejecución spot (next-open 4h candle) ya está parcialmente arbitrado por traders con mejor latencia. El edge residual es marginal.

**Observación tangencial relevante**: el funding rate medio anualizado de BTC perp es +11.86% — los longs perpetuamente subsidian a los shorts. Si el edge de H3 fuera real, **ya estaría completamente arbitrado por desk de carry trade**.

### 4.3 H5 (DXY) muestra el caso clásico de regime overfit

- En W1 (post-2018 mini-bull + COVID crash): Δ Sharpe = +0.633 ✓
- En W2 (mega bull 2020-2022 + bear 2022): Δ = +0.047 (apenas)
- En W3 (2023-2026): Δ = -1.198 ❌

**Razón inferida**: la correlación inversa BTC/DXY fue fuerte durante 2022 (cuando institutional money trataba BTC como activo de riesgo). Antes y después, el accoplamiento es débil. Filtrar BUYs por DXY simplemente quita trades buenos en períodos donde la macro no manda.

### 4.4 SuperTrend baseline sigue siendo lo mejor pero NO supera B&H en plata

`supertrend_baseline` tiene Sharpe +0.972 vs B&H +0.690 (Δ +0.282). PERO:
- Final equity: $366 (SuperTrend) vs $673 (B&H).
- En W3: Sharpe +0.421 vs B&H +0.877 (Δ -0.457).

Esto es **idéntico al hallazgo de lessons-learned-final.md §2.2**: "estrategias activas ganan en riesgo ajustado pero pierden en retorno absoluto vs B&H". Ocho años después, $100 en B&H quedan en $673, $100 en SuperTrend quedan en $366. **El bot vivo está corriendo una estrategia que pierde plata vs comprar y dormir.**

### 4.5 Sample size de H3-standalone fue insuficiente

El flag amarillo documentado en `alignment_spec.md` §7 se confirmó:
- h3_funding_standalone disparó solo 6 trades en train+val (8+ años).
- En W3 (2023-07 → 2026-04): **0 trades** porque funding nunca alcanzó el umbral -0.02%.

Cuando una estrategia "no falla" porque no opera, no aporta evidencia.

---

## 5. Decisión y caminos hacia adelante

### 5.1 Aplicación del pre-registro

Per ADR-023 §2.5 trigger #1 y pre_registration.md §3 regla 1:

> "Ninguna hipótesis pasa walk-forward W3 → cierre con ADR-024."

**Cierre formal con ADR-024**. OOS forward-only queda intocado, sellado para futuros research que cumplan condiciones de ADR-012.

### 5.2 Lo que NO se va a hacer

- **NO** se va a "ajustar thresholds" para que alguna hipótesis pase. Eso es data snooping post-OOS prohibido en pre_registration §8.
- **NO** se van a probar ensembles (combinaciones de H1+H3+H5). Prohibido en pre_registration §3 regla 5.
- **NO** se van a probar otros pares (ETH, SOL, BNB) bajo el scope actual. Si el edge no aparece en BTC con la mejor liquidez, agregar pares más volátiles solo amplifica el ruido.

### 5.3 Caminos disponibles tras el cierre

(Comprometidos en ADR-023 §4)

1. **Aceptar la conclusión expandida**. El bot framework existe, funciona, está validado en testnet operacionalmente. La conclusión técnica final ahora cubre: indicadores técnicos puros (ADR-012) + alpha sources no-técnicas spot-only (v6). En el scope auto-impuesto de la constitución, **no hay edge accionable retail**.

2. **Cambiar el scope (ADR fundacional)**. Pivotar a futures/options/carry trade requiere enmendar `constitution.md` Art. 0 y construir un nuevo MVP. Es otro proyecto, comparte sólo infraestructura.

3. **Hibernación**. Detener el bot vivo en testnet (ya no valida nada nuevo) y mover capital a B&H BTC + DCA. La infraestructura (bot, framework de research, tests, ADRs, data pipeline) queda viva como activo reutilizable.

### 5.4 Recomendación dura

El research previo en abril 2026 (ADR-012, OOS_FINAL) ya decía: "no se encontró estrategia activa que justifique deployment a live". v6 era el último intento honesto dentro del scope constitucional original.

**Hicimos el experimento. La respuesta sigue siendo no.**

La pregunta ahora **no es de research, es de producto**: ¿el objetivo del proyecto sigue siendo "encontrar edge automático en spot crypto"? Si sí → cambio de scope obligatorio (camino 2). Si no → hibernación con honor (camino 3). En cualquier caso, **mantener el bot vivo en testnet ejecutando una estrategia documentadamente sin edge no aporta información nueva** — ni siquiera para el gate ADR-022, porque ese gate mide ejecución operativa, no rentabilidad.

---

## 6. Activos producidos por v6 (reutilizables)

| Activo | Valor reusable |
|---|---|
| `research/v6/data/fetchers/` | Fetchers de F&G, DXY, funding (gratis, mantienen API en JSON + parquet) |
| `research/v6/signals/_alignment.py` | Helpers de merge daily/8h con OHLCV 4h sin look-ahead. 10 tests verdes. |
| `research/v6/backtest/engine.py` | Engine long-only spot con fill next_open. 7 tests verdes. |
| `research/v6/backtest/metrics.py` | Métricas estandarizadas (Sharpe, MaxDD, PF, Calmar, etc.). |
| `research/v6/backtest/runner.py` | Orquestador train/val/train+val multi-experimento. |
| `research/v6/backtest/walkforward.py` | Walk-forward W1/W2/W3 automatizado con gate enforcement. |
| `research/v6/data/loaders.py` | Loaders canónicos para OHLCV + externals. |
| ADR-023 + pre_registration.md | Framework de governance pre-registrado, replicable para future research. |

Cualquier futuro research v7 (si se justifica por ADR) puede arrancar de esta infraestructura.

---

## 7. Decisión pendiente del owner

Cristhian: te queda elegir el camino (5.3 opciones 1/2/3). El research v6 ya entregó su veredicto. Cuando decidas, abrimos el ADR de cierre formal (ADR-024) con el camino seleccionado.

Sin decisión, el default per ADR-023 §2.5 es el camino 1 (aceptar la conclusión expandida) + bot vivo sigue funcionando hasta que se decida otra cosa.
