# Post-Mortem — Research v2 Regime-Aware + C2 BB Puro

**Fecha:** 2026-04-05
**Branch:** `research/strategy-v3-regime-aware`
**Duración:** ~1 día calendario (E0 + E1 + E3 + C2 sanity)
**Owner:** Cristhian Benitez
**Veredicto final:** Research v2 no produjo estrategia apta para live. OOS 2026-Q1 intocado. Candidata C2 (BB puro) FAIL en sanity check train+val.

---

## 1. Timeline completo

| Paso | Descripción | Resultado |
|---|---|---|
| E0 iter 1 | Detector v2 rolling quantiles (Q80/Q60) | M4 FAIL HARD: 15.80% avg rally coherence (target 70%) |
| E0 iter 2 | Detector AMEND-2 ADX absolutos 25/20 | M4 WARN: 40.65% avg (+24.85pp) pero 4/5 rallies <50% |
| ADR-007 | Re-calibrar M4 target 50%/60% + gate E1 estricto | Aceptado por owner |
| E1 | EMA(12/26) + TRENDING_UP filter | **ABORT G3**: Sharpe -0.399, anti-edge 6/10 combos |
| E2/E4 | SuperTrend/Donchian + TRENDING_UP | **Skipped** (same ADX lag root cause) |
| E3 | BB(20,2.75) + RANGING_CALM filter | **ABORT G3**: Sharpe -0.587, anti-edge 6/10, 58.9% REGIME_EXIT |
| ADR-008 | Test tardío BB(20,2.75) sin filtro (Opción C2) | Aprobado por owner |
| C2 Paso 1 | BB(20,2.75) puro train+val sanity | **FAIL**: Sharpe -0.5579 (gate ≥0.5) |
| C2 Paso 2 | OOS 2026-Q1 | **NO EJECUTADO** (gate Paso 1 no alcanzado) |

---

## 2. Root causes identificados

### 2.1 Detector: conflicto irreconciliable lag vs estabilidad

**ADX es indicador lagging por diseño** (Wilder 1978: smoothed DX con período
14+14 = ~28 bars warm-up). Tiene dos consecuencias irreconciliables:

**Para trend-following (E1):** ADX confirma momentum **después de onset**.
Cuando ADX > 25 (entry), el momentum ya fue capturado por indicadores más
rápidos (EMA). La posición abre tarde, sufre pullback, pierde. **Anti-edge.**

**Para mean-reversion (E3):** ADX < 20 (RANGING_CALM) correctamente identifica
ausencia de trend, pero las **transiciones** del detector (debounce H2 +
cooldown H3 + hysteresis H1) causan exits prematuros. 58.9% de trades
cerraron por REGIME_EXIT, no por señal de estrategia. **Anti-edge.**

Conclusión: un indicador lagging puede clasificar régimen **en retrospectiva**
pero no puede **filtrar trades en tiempo real** sin causar timing damage.

### 2.2 BB MR: edge era parcialmente artefacto del fill model

v1 BB(20, 2.75) sin filtro tenía Sharpe OOS +0.72 y W3 +0.70, pero usaba
fill instantáneo al close de la vela de señal. Con fill realista R7
(signal at close[t], fill at open[t+1]):
- Sharpe train+val: **-0.5579** (discrepancia -1.26 vs v1)
- Avg win: +3% vs avg loss: -5.5%
- 27% disaster stops a -8%

El edge de MR depende de capturar el **rebote inmediato** desde lower band.
Con 1 vela de delay (4h), el rebote ya ocurrió parcialmente. El fill
realista elimina el edge.

### 2.3 Asimetría temporal train vs val

Val (2023) fue positivo en BB puro (BTC +0.43, ETH +0.18 Sharpe). Train
(2020-2022) fue negativo por crashes (LUNA, FTX, COVID aftershock). La
señal MR long-only compra cuchillos cayendo durante bear markets.

---

## 3. Qué funcionó (metodología)

### 3.1 Framework pre-registrado

Plan-v2 con E0-E6 pre-registrados evitó data snooping. Los experimentos
corridos coincidieron con los planificados, sin post-hoc fishing.

### 3.2 Gates y time-box

ADR-005 + ADR-007 gates + time-box de 6 semanas forzaron decisiones
oportunas. Cada ABORT tenía criterio explícito ex-ante.

### 3.3 Iteraciones controladas de detector

E0 iter 1 → iter 2 + AMEND-1 → AMEND-2 fue un ciclo de aprendizaje legítimo:
rolling Q80 self-defeats → absolutos 25/20 mejoran +24.85pp → pero techo
arquitectural ~40%. Cada paso generó insight concreto.

### 3.4 Fill model realista (R7)

Adoptar R7 (fill at open[t+1]) en ADR-008 **salvó de deployar una estrategia
con edge ilusorio**. v1 sin R7 habría pasado OOS y entrado a testnet con
edge artefactual.

### 3.5 Disciplina de abort

Cuando E1 y E3 mostraron anti-edge, el framework respondió correctamente:
G3 abort → pivot → C2 sanity check. No hubo negociación del gate.

---

## 4. Qué no funcionó (hipótesis)

### 4.1 Regime-aware como filtro de trading

La hipótesis central de v2 ("clasificar régimen → filtrar señales por
régimen → eliminar sangrado fuera de régimen") falló completamente.

El detector clasifica régimen **razonablemente** (~40% coherencia con labels
manuales), pero **no es traducible a filtro de trading** porque:
- Los bordes de transición destruyen trades abiertos (E3: 58.9% REGIME_EXIT).
- El lag de confirmación pierde timing de entry (E1: anti-edge BTC).
- La clasificación "correcta" no implica que operar dentro del régimen
  sea rentable.

### 4.2 BB MR long-only como edge sostenible

La única señal de v1 que parecía tener edge (BB Sharpe OOS +0.72) resultó
depender del fill model optimista. Con fill realista, el edge desaparece.

### 4.3 Mean-reversion long-only en crypto spot

Comprar en lower band de Bollinger es comprar cuchillos cayendo en bear
markets. Sin short-selling (constitución Art. 0), la estrategia tiene
asimetría estructural negativa: gana poco en ranging, pierde mucho en bear.

---

## 5. Insight fundamental transferible

> **Un indicador lagging puede clasificar régimen en retrospectiva pero no
> puede filtrar trades en tiempo real sin causar timing damage.**

Este insight aplica a cualquier detector basado en ADX, RSI, o moving
averages. Para que un detector de régimen sea útil para trading, necesitaría:
- **Leading indicators** (difíciles de construir sin ML).
- **Clasificación asíncrona al trading** (ej: detector en daily, trading en 4h,
  con lag aceptable de 24h entre cambio de régimen y cambio de posición).
- **Tolerancia a misclassification** en la estrategia (no depender del
  detector para entry/exit sino solo para position sizing o risk adjustment).

Ninguna de estas opciones fue explorada por scope constraints (No-Misión ML,
time-box, zero iteration policy).

---

## 6. Costos de v2

| Recurso | Costo |
|---|---|
| Tiempo calendario | ~1 día (intensivo) |
| Experimentos corridos | E0 (2 iter) + E1 + E3 + C2 sanity |
| Capital en riesgo | **$0** (todo backtest) |
| Dataset OOS 2026-Q1 | **INTOCADO** (no contaminado) |
| Data pipeline | 66,682 velas 4h descargadas, reutilizable |
| Aprendizaje | Alto (ver §5) |

**ROI del research:** positivo. No perdimos capital. El OOS 2026-Q1 está
limpio para futuros proyectos. El insight sobre fill model R7 es valioso.

---

## 7. Decisión de path forward

**Per ADR-008 R3 (zero iteration) + Paso 1 FAIL:**

El path es **Opción D de ADR-004**: cerrar proyecto operativo, archivar
repo como research reference.

Decisión pendiente del owner:
- Cerrar proyecto operativo (no deploy, no testnet, no mainnet).
- Archivar codebase como referencia para futuro quant research.
- Escribir postmortem final si OOS es descartado definitivamente.

---

## 8. Learnings transferibles a futuros proyectos

1. **Fill model realista desde día 1.** Nunca backtest con fill at close.
   Siempre signal at close[N], fill at open[N+1] mínimo.
2. **Lagging indicators no sirven para filtrar trades.** Sirven para
   clasificación retrospectiva pero no para decisiones en tiempo real.
3. **Mean-reversion long-only tiene bias estructural negativo** en crypto
   (compras cuchillos en bear). Necesita short-sell o position sizing
   asimétrico para funcionar.
4. **Pre-registro + gates + time-box funcionan.** El framework metodológico
   es sólido. La hipótesis no lo era.
5. **Cuantiles rodantes se auto-defeat en strength indicators.** Solo
   aplican a vol indicators cuya base shifts macro-cíclicamente.
6. **OOS seal funciona.** 2026-Q1 está limpio a pesar de 20+ experimentos.
   La disciplina de no mirar OOS es el mayor activo del framework.

---

## 9. Estado del repo al cierre de v2

- Branch `research/strategy-v3-regime-aware` con ~20 commits documentando
  el journey completo.
- Tag `research-v1-complete` sobre cierre de v1.
- Data pipeline funcional (66,682 velas, 5 pares, 5 splits + warmup_oos).
- Detector v2 implementado y testeado (funciona para clasificación, no
  para filtrado de trading).
- 505 tests pass, lint clean.
- ADRs 004-008 documentando cada decisión.
- OOS 2026-Q1 limpio y chmod 0444.
