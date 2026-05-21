# ADR-023: Reapertura de Research v6 — Alpha sources no-técnicas

**Fecha:** 2026-05-20
**Status:** Proposed
**Decisores:** Cristhian Benitez (owner)
**Relacionado con:** ADR-012 (Cierre de research v1-v5), `constitution.md` Art. 0 (spot-only), Art. 8.1 (cambios en risk/strategy requieren ADR), `research/lessons-learned-final.md`

---

## 1. Contexto

ADR-012 cerró el research de estrategias de trading sobre indicadores técnicos clásicos (EMA, Donchian, SuperTrend, Bollinger MR) tras ~40h, 144 combinaciones y 9 años de datos. La conclusión técnica de `lessons-learned-final.md` §4.3 fue:

> "Los indicadores técnicos clásicos fueron diseñados para mercados con microestructura diferente (equities, commodities). Crypto spot tiene volatilidad extrema, bear markets de -80%, ausencia de mean-reversion confiable, y barra alta de B&H por apreciación secular de BTC."

ADR-012 §"Condiciones para reabrir research" definió 4 requisitos: hipótesis con evidencia externa no reciclada, fill model realista desde día 1, walk-forward validation obligatorio, nuevo ADR aprobando scope.

Este ADR cumple esos 4 requisitos para reabrir bajo un scope **explícitamente distinto**: fuentes de alpha **no derivadas de OHLCV** del propio activo.

### Por qué este scope es distinto del research previo

- v1-v5 trabajaron sobre indicadores técnicos calculados a partir de OHLCV del par operado.
- v6 introduce inputs exógenos: sentiment retail (F&G), dominance cross-asset, derivatives sentiment (funding rate), macro overlays (DXY).
- Estos inputs **no estaban en el espacio de búsqueda** de v1-v5. El dataset OHLCV está quemado para indicadores técnicos pero **no para señales exógenas** que nunca lo tocaron.

### Por qué ahora

1. El bot en testnet lleva 11 días con 1 trade cerrado, sin perspectiva de pasar el gate ADR-022 en horizonte razonable. Operacionalmente sano pero estratégicamente está corriendo una estrategia que `OOS_FINAL_RESULT.md` mostró sin edge (SuperTrend trend-following, OOS Sharpe -0.55).
2. Existe literatura cuantitativa pública para al menos una de las hipótesis propuestas (funding rate como sentiment proxy, papers Soska 2021 / Alexander 2023).
3. Las 4 fuentes propuestas son **gratuitas y de cobertura histórica suficiente** (verificado 2026-05-20):
   - F&G alternative.me: 3,027 días desde 2018-02-01
   - Binance funding rate: desde 2019-09 (lanzamiento del perp BTCUSDT)
   - FRED DXY: décadas
   - CoinGecko BTC.D: API gratuita con rate limit (current); histórico vía scrape de tradingview o CoinMetrics free tier
4. El usuario decidió explícitamente este camino tras revisar la conclusión del research previo.

---

## 2. Decisión

Reabrir research bajo el nombre **v6**, scope acotado a las hipótesis pre-registradas en `research/v6/pre_registration.md`. El scope es:

- **6 experimentos**: 3 hipótesis (H1, H3, H5) × 2 modelados (filter sobre SuperTrend + standalone).
- **Time-box**: 45h de trabajo o `2026-07-31`, lo que ocurra primero.
- **Capital arriesgado durante v6**: $0. Cero modificación del bot vivo.

### 2.1 Hipótesis pre-registradas

| # | Nombre | Fuente | Tesis |
|---|---|---|---|
| H1 | Fear & Greed extremos | alternative.me | F&G ∈ [0,25] anticipa rebote 1-4 semanas en BTC/ETH |
| H3 | Funding rate sentiment | Binance perp API | Funding extremo (>0.05% u <−0.02% 8h) marca exceso/capitulación en spot |
| H5 | DXY overlay | FRED + Yahoo | Uptrend DXY 20d reduce probabilidad de upside en BTC |

H2 (BTC dominance) y H4 (exchange netflows) quedan fuera del scope de v6:
- H2: riesgo metodológico de look-ahead — BTC.D es función lineal de market caps que ya incluyen el precio. Edge probable en backtest, frágil en forward-test. Reabrir bajo otro ADR si fuera necesario.
- H4: requiere data premium (Glassnode / CryptoQuant).

### 2.2 Cómo cumple las 4 condiciones del ADR-012

| Condición | Cumplimiento |
|---|---|
| Hipótesis con evidencia externa no reciclada | Las 3 hipótesis usan fuentes que v1-v5 no tocaron. H3 tiene literatura cuantitativa formal. |
| Fill model realista desde día 1 | Reutilización del backtest engine existente con `fill_mode=next_open` por default. No discutible. |
| Walk-forward validation obligatorio | Train (2018-2024) + val (2025) + walk-forward W1/W2/W3. OOS reservado forward-only. |
| Nuevo ADR aprobando scope | Este documento. |

### 2.3 Datasets

- **OHLCV**: reuso de `data/ohlcv/*_4h_*.parquet` existente (BTC/ETH/SOL/BNB/XRP).
- **External inputs**: nuevos en `research/v6/data/external/`:
  - `fng_daily.parquet` (alternative.me)
  - `funding_rate_8h.parquet` (Binance fapi)
  - `dxy_daily.parquet` (FRED)
- Splits temporales:
  - Train: `[2018-02-01, 2024-12-31]` (alineado a coverage F&G)
  - Validation: `[2025-01-01, 2026-04-30]`
  - **OOS forward-only**: `[2026-05-20, end-of-v6]`. Reservado físicamente con `chmod 0444` al inicio de Fase 4. No tocado durante train+val.

### 2.4 Gates de éxito (pre-registrados, no negociables)

Para que una hipótesis sea promovida a candidata de live:

| Gate | Umbral | Justificación |
|---|---|---|
| Train+val Sharpe vs B&H BTC | Δ ≥ +0.20 | In-sample, naturalmente optimista; exige más que el OOS |
| Walk-forward W3 Sharpe vs B&H BTC | Δ ≥ +0.15 | Predictivo de OOS según `lessons-learned-final.md` §3.2 (precisión ±0.02). Intermedio entre train y OOS. |
| OOS forward-test Sharpe vs B&H BTC | Δ ≥ +0.10 sostenido (≥4 meses) | El test real. Una sola corrida prerregistrada. Umbral acordado tras debate explícito sobre base rate. |
| MaxDD | ≤ 25% absoluto | Más estricto que el -30% de la constitución, alineado con tolerancia operativa |
| Profit Factor | ≥ 1.3 | Margen real sobre fees + slippage. Coherente con el umbral OOS bajado a +0.10. |
| Trades totales (train+val) | ≥ 50 | Sample size mínimo para inferencia estadística |

**Decisión de bajar el listón a +0.10 (vs +0.20 original)**: el usuario aceptó explícitamente este umbral conociendo el trade-off — un edge de +0.10 Sharpe sostenido vs B&H BTC es "mejora leve pero real", no "vencer claramente". La base rate de éxito sube de ~10% a ~20-25% pero la magnitud de retorno esperado en live es menor.

**"Casi pasa" = FAIL.** No se promueve nada con delta < +0.10 vs B&H. El research previo desperdició tiempo en "edge marginal" que no resistió OOS.

### 2.5 Triggers de cierre formal

v6 se cierra (sin promover nada) si:

1. Ninguna hipótesis pasa walk-forward W3 → cierre con ADR-024.
2. Una hipótesis pasa walk-forward pero falla OOS → cierre, single-shot OOS no se reusa.
3. Se cumple el time-box (60h o 2026-07-31).
4. Aparece un fallo metodológico (data leak, look-ahead, etc.) que invalida resultados previos.

---

## 3. Consecuencias

### Positivas

- Permite explorar el espacio que ADR-012 dejó explícitamente abierto.
- El framework de research (backtest engine, walk-forward, metrics, OOS sealing) es 100% reutilizable.
- Costo financiero: $0 (todas las fuentes son gratis).
- El bot vivo no se toca; cualquier riesgo del research está contenido.

### Negativas

- Costo de oportunidad: 45-60h de trabajo con base rate de éxito ≤10% (estimado conservadoramente).
- Si v6 falla, refuerza la conclusión de ADR-012 pero no agrega información accionable.
- Si v6 promueve algo, su integración al bot vivo (camino B) o nuevo bot (camino C) es trabajo adicional con sus propios riesgos.

### Neutras

- El bot vivo seguirá corriendo SuperTrend en testnet durante v6.
- ADR-022 (gate testnet) sigue vigente independientemente del research.
- Los resultados de v6 son input para una decisión de producto posterior (qué hacer con el bot), no son la decisión en sí.

---

## 4. Caminos posibles tras v6 (pre-comprometidos)

Para evitar data snooping post-OOS, los caminos se comprometen ahora:

| Resultado v6 | Camino |
|---|---|
| Ninguna hipótesis pasa walk-forward | ADR-024: cierre formal v6. Aceptar conclusión expandida del research. |
| 1+ pasa walk-forward + OOS, scope compatible con constitución actual | ADR de integración al bot actual. Risk-guardian review obligatorio. PR atómico con gates de CI. |
| 1+ pasa walk-forward + OOS, scope requiere cambios constitucionales | ADR de enmienda constitucional + nuevo proyecto (bot v2) con su propia governance. El bot actual queda en hibernación o B&H. |
| 1+ pasa walk-forward pero falla OOS | Cierre. OOS quemado, no se reusa. |

---

## 5. Implementación

### Fases

1. **Fase 0** (este ADR + pre-registro): 3-4h
2. **Fase 1** — data pipeline 3 fuentes (F&G, funding, DXY): 6-8h
3. **Fase 2** — 6 signal generators: 9-12h
4. **Fase 3** — backtest train+val+walk-forward: 12-15h
5. **Fase 4** — OOS forward-test (solo si pasa Fase 3): 3-5h
6. **Fase 5** — report + ADR de cierre/promoción: 3-5h

Total: 36-49h (rangos estimados). Time-box duro 45h o 2026-07-31.

### Reglas de ejecución

- Todo código vive en `research/v6/`. Cero modificación de `chocotrader/` (paquete del bot).
- Cada hipótesis tiene su report en `research/v6/reports/Hx_*.md` con tabla de métricas y plot de equity.
- Cada corrida de backtest loguea en `research/v6/results/run_log.jsonl` con timestamp, hash de datos, parámetros.
- OOS access se loguea en `research/v6/oos_access.json` con timestamp, razón, hash del estado del código.
- Todos los reportes incluyen B&H BTC como primera fila (regla §4.2 de `lessons-learned-final.md`).

---

## 6. Referencias

- `docs/adr/ADR-012-option-d-close-project.md`
- `research/lessons-learned-final.md`
- `research/reports/OOS_FINAL_RESULT.md`
- `constitution.md` §Art. 0, §Art. 8.1
- `research/v6/pre_registration.md`
- Literatura: Soska et al. 2021 ("Funding rate as sentiment indicator"), Alexander & Heck 2023 ("Crypto derivatives microstructure")
