# Resultado final OOS — Ensemble 60/40

**Fecha:** 2026-04-05
**Decisión:** NO live deployment. Volver a research.
**Gate Phase 4:** OOS Sharpe ≥ 0.8 → **NO PASA (0.041)**

---

## Resumen ejecutivo

El candidato final (**Ensemble 60% E3b-5p + 40% BB(20, 2.75)**, 5 pares, 4h)
pasó todos los gates de train+val y auditoría formal, pero **falló en OOS**.

- **OOS Sharpe: +0.041** (gate ≥0.8)
- **$100 → $99.81** (breakeven, -0.2%)
- **MaxDD OOS: -9.17%**

## Por sub-componente (donde está la información)

| Componente | OOS Sharpe | $100 → | W3 walk-forward (predicción) |
|---|---|---|---|
| Trend solo (E3b-5p) | **-0.55** | $94.54 | -0.54 |
| MR solo (BB 20, 2.75) | **+0.72** | $107.73 | +0.70 |
| Ensemble 60/40 | +0.04 | $99.81 | -0.22 |
| Buy & Hold ref | +0.12 | $95.47 (MaxDD -40%) | — |

**El walk-forward fue casi perfectamente predictivo.** Trend fracasó, MR funcionó, ensemble
quedó en breakeven.

## Distribución de trades OOS

- Trend: 46 trades (9 BTC, 13 ETH, 9 SOL, 10 BNB, 5 XRP)
- MR: 54 trades (13 BTC, 11 ETH, 10 SOL, 9 BNB, 11 XRP)
- Total: **100 trades** en 7 meses

## Interpretación

**El régimen W3 (consolidación post-rally 2024) continuó en OOS.**

Como predijo el walk-forward, trend-following simple no tiene edge en este
régimen. MR tiene edge real (+0.72) pero no alcanza el gate estricto 0.8.
El ensemble al 60% trend "arrastró" a MR hasta breakeven.

**Si hubiéramos corrido MR solo**, habríamos obtenido $107.73 con Sharpe 0.72 —
pero elegir MR solo ahora **sería data snooping post-OOS y está prohibido
por el pre-registro**.

## Disciplina cumplida

✓ OOS corrido UNA SOLA VEZ
✓ Acceso logueado en splits.json con timestamp y razón
✓ No hubo "pico rápido" antes de la corrida formal
✓ Gate 0.8 respetado sin ajuste post-hoc
✓ No se eligió "la segunda mejor"
✓ Predicciones W3 validadas con precisión en OOS

## Aprendizajes

### 1. El framework walk-forward funcionó

Predecimos Trend=-0.54 (real -0.55), MR=+0.70 (real +0.72) dentro de ±0.02
Sharpe. **Invertir tiempo en walk-forward antes de OOS fue la mejor decisión
del research.** Nos permitió predecir el fracaso SIN quemar OOS, y cuando
quemamos OOS fue para confirmar, no para descubrir.

### 2. Trend-following simple NO tiene edge persistente en crypto spot retail

Como advertía el plan ("trend-following simple en spot crypto retail puede no
tener edge"). 2024 fue atípico, no repetible. Los rallies lineales que
alimentaban EMA cross no existen en régimen de consolidación.

### 3. Mean-reversion ES una hipótesis viable (pero falta evidencia)

BB(20, 2.75) MR obtuvo Sharpe 0.72 en OOS — **muy cerca** del gate 0.8. En
un dataset fresco con un nuevo OOS, MR podría pasar. Requiere:
- Nueva data (2026 cuando esté disponible)
- Nuevo split con OOS intocado
- Research específico para MR (optimization no data-snooped)

### 4. El ensemble "salvó el capital" pero no alcanza Phase 4

$99.81 (breakeven) vs $94.54 (trend solo). La diversificación protegió ~$5,
lo cual valida el concepto de ensemble. Pero no suficiente para live.

### 5. El dataset 2024-2025 quedó quemado

Cualquier strategy futura con el mismo dataset será data-snooping retroactivo
si usamos este OOS como referencia. La próxima iteración de research debe
traer su propio holdout independiente.

## Decisiones de producto pendientes (del usuario)

### Opción 1 — Pivot a MR-only con dataset fresco
- Descargar data 2026 cuando esté disponible.
- Research específico de MR con train/val/OOS nuevo.
- Hipótesis: si OOS Sharpe ≥ 0.8 en dataset independiente, promover MR.

### Opción 2 — ADR fundacional
- Aceptar que "trend-following en spot" no se sostuvo como thesis.
- Re-scopear MVP: ¿futures? ¿mean-reversion? ¿risk-parity? ¿DCA inteligente?
- Requiere enmienda constitutional.

### Opción 3 — Pausar con honor
- Research fue disciplinado y produjo aprendizaje técnico valioso.
- Infrastructure creada (data split, runner, metrics) es reusable.
- Aceptar que por ahora no hay strategy live-able.
- Retomar cuando haya data fresca 2026+.

## Artefactos

- Equity curves OOS: `research/results/OOS_ensemble_60_40.csv`
- Reports en: `research/reports/`
- Data split log: `data/splits.json` (OOS accessed 2026-04-05T16:49:04Z)
