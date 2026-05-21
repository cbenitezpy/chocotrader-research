# ADR-024: Cierre formal de Research v6 — No edge accionable en alpha sources no-técnicas

**Fecha:** 2026-05-20
**Status:** Accepted
**Decisores:** Cristhian Benitez (owner)
**Relacionado con:** ADR-012 (cierre research v1-v5), ADR-023 (apertura research v6), `research/v6/reports/FINAL_RESULT.md`, `research/v6/pre_registration.md`

---

## 1. Contexto

ADR-023 abrió research v6 con scope acotado: 3 hipótesis basadas en señales exógenas (F&G index, funding rate, DXY overlay) × 2 modelados cada una (filter sobre SuperTrend + standalone). Time-box 45h, gates pre-registrados, OOS forward-only sellado.

El research se ejecutó respetando el pre-registro sin modificaciones:
- Fase 0: ADR-023 + pre-registro committeados (`a3a388f`).
- Fase 1: 3 fetchers + alignment spec (`c1557f8`).
- Fase 2: 6 signal generators + helpers + 19 tests verdes (`406739c`).
- Fase 3: backtest engine + métricas + runner + walk-forward (pendiente commit).
- Fase 4: **NO EJECUTADA** — sin acceso al OOS según trigger ADR-023 §2.5 #1.
- Fase 5: este ADR + `FINAL_RESULT.md`.

---

## 2. Hechos

Per `research/v6/reports/FINAL_RESULT.md` y `walkforward_BTC_USDT.md`:

### 2.1 Gate train+val (Δ Sharpe ≥ +0.20 vs B&H BTC)

Únicamente `supertrend_baseline` pasa (+0.282), pero NO es una hipótesis nueva del v6 — es la estrategia existente del bot vivo, incluida como referencia. Las 6 hipótesis externas máximo alcanzan +0.034 (h3_funding_filter).

### 2.2 Gate walk-forward W3 (Δ Sharpe ≥ +0.15 vs B&H BTC)

**Ninguna estrategia pasa.** Ranking de mejor a peor en W3:

| Estrategia | Δ Sharpe W3 |
|---|---:|
| supertrend_baseline | -0.457 |
| h3_funding_filter | -0.353 |
| h5_dxy_standalone | -0.720 |
| h1_fg_standalone | -0.742 |
| h3_funding_standalone | -0.877 (0 trades en W3) |
| h5_dxy_filter | -1.198 |
| h1_fg_filter | -1.625 |

### 2.3 Patrón regime-dependent confirmado

Estrategias con Δ positivo en W1/W2 (bull markets) colapsan en W3 (consolidación + bear suave 2023-2026). Esto matchea la firma de **edge ilusorio por overfit a régimen específico** documentada en `lessons-learned-final.md` §2.6-2.7.

### 2.4 OOS no quemado

Per ADR-023 §2.5 trigger #1 y pre_registration.md §7 paso 1, el OOS forward-only no se accedió. Queda intocado para futuros research que cumplan condiciones del ADR-012.

---

## 3. Decisión

**Cerrar research v6 sin promover ninguna estrategia a live.**

### 3.1 Lo que queda

- `research/v6/` queda congelado como referencia histórica (paralelo a `research/` v1-v5).
- Activos reutilizables siguen disponibles: fetchers, alignment helpers, backtest engine, walk-forward runner, métricas estandarizadas.
- Tests existentes (26 verdes en total) deben pasar en CI futura si se cambia el venv o las dependencias.
- ADR-023 + pre-registro v6 quedan como referencia procesal — replicables para futuros research.

### 3.2 Lo que NO se va a hacer (anti-patrones explícitos)

- **NO** ajustar thresholds para que alguna hipótesis "pase" post-resultado.
- **NO** probar ensembles ad-hoc combinando hipótesis (prohibido en pre_registration §3 regla 5).
- **NO** extender el research a otros pares con el mismo scope — si BTC no muestra edge, los pares menos líquidos amplifican ruido sin agregar señal.
- **NO** reabrir research v7 dentro del mismo scope (spot-only + indicadores técnicos / sentiment / macro). El espacio está agotado.

### 3.3 Condiciones para abrir research v7 (más estrictas que ADR-012)

Cualquier futuro research necesita:
1. Cambio constitucional explícito (Art. 0 de spot-only → futures u otro mercado).
2. Hipótesis con evidencia académica formal (paper revisado por pares, no blog post).
3. Pre-registro firmado ANTES de mirar datos.
4. Fill model realista desde día 1.
5. Walk-forward + OOS sellado.
6. Time-box duro.
7. Gates absolutos en plata final, no sólo Sharpe (lección de §2.4 de FINAL_RESULT — Sharpe positivo + plata negativa = ilusión de edge).

---

## 4. Consecuencias

### 4.1 Para el bot vivo en testnet

El bot está corriendo SuperTrend baseline, que en W3 tiene Δ Sharpe -0.457 vs B&H. **El bot está corriendo la estrategia que el research demostró que pierde plata vs comprar y dormir, en el régimen actual del mercado.**

Esto requiere decisión de producto separada (no incluida en este ADR):

| Opción | Implicancia |
|---|---|
| A — Hibernación | Stop bot en testnet, mover capital a B&H BTC + DCA. Infra queda viva como activo. |
| B — Pivot fundacional | Enmienda constitucional + nuevo MVP en futures u otro mercado. |
| C — Status quo | Bot sigue corriendo en testnet "para validar ejecución operativa". El gate ADR-022 sigue evaluando uptime+trades, NO rentabilidad. |

Recomendación del research: **A** o **B**. **C** es válida operativamente pero estratégicamente debe reconocerse como "ejercicio infraestructural", no "camino a generar retorno".

### 4.2 Para el framework

El framework de governance (constitution + ADRs + gates + pre-registro + OOS sealing + walk-forward) cumplió su rol perfectamente. **$0 de capital perdido durante todo el research v1-v6** (~50-80h totales de trabajo).

### 4.3 Para el aprendizaje técnico

Quedan documentadas conclusiones que valen para futuros proyectos quant:
1. Indicadores técnicos clásicos no tienen edge en crypto spot retail con costos realistas (ADR-012).
2. Sentiment retail (F&G) tampoco — "comprar miedo" pierde plata en horizonte 1-4 semanas (v6 H1).
3. Funding rate como proxy de sentiment perp → spot tiene edge marginal pero ya está arbitrado (v6 H3).
4. Filtros macro (DXY) son regime-dependent y fallan en out-of-regime (v6 H5).
5. **Spot-only sin apalancamiento + long-only + barra alta de B&H BTC = handicap estructural** para retail (lessons-learned §4.4, confirmado v6).

---

## 5. Referencias

- `docs/adr/ADR-023-reopen-research-v6-external-alpha.md`
- `research/v6/pre_registration.md` (hash sellado en commit a3a388f)
- `research/v6/reports/FINAL_RESULT.md`
- `research/v6/reports/walkforward_BTC_USDT.md`
- `research/v6/reports/BTC_USDT_train_val_summary.md`
- `research/lessons-learned-final.md`
- `constitution.md` §Art. 0, §Art. 4, §Art. 8.1

---

## 6. Próximo paso

Owner debe elegir entre opciones A / B / C de §4.1. Sin elección explícita, el sistema queda en C por inercia hasta nuevo aviso.
