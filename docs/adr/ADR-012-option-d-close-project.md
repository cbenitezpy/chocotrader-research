# ADR-012: Cierre de Research — Archivar hallazgos, continuar desarrollo del bot

**Fecha:** 2026-04-07
**Status:** Accepted
**Decisores:** Cristhian Benitez (owner)
**Relacionado con:** ADR-004, ADR-008 R3, ADR-011,
`research/lessons-learned-final.md`, `research/full-period-audit.md`

---

## Contexto

Chocotrader investigó durante ~16 días calendario (~40h) si alguna estrategia
trend-following o mean-reversion sobre Binance Spot con costos realistas
(0.30% round-trip) tiene edge explotable. El research abarcó 4 fases:

| Fase | Enfoque | Resultado |
|---|---|---|
| v1 | Trend-following + ensemble naive | Sharpe OOS +0.04 (gate 0.8). FAIL |
| v2 | Regime-aware (detector ADX/ATR/BB) | Anti-edge en todos los experimentos. ABORT |
| v3 | BB(20,2.75) MR puro (ADR-008) | Paso 1 FAIL: Sharpe -0.56 (gate 0.5) |
| v4 | Auditoría 144 combinaciones, 9 años | Ninguna estrategia supera gates con margen |

### Findings clave

1. **Fill model R7:** BB MR con fill optimista Sharpe +0.72, con fill realista -0.56. Delta -1.28.
2. **B&H BTC Sharpe 0.81 en 9 años** es barrera extremadamente alta para retail spot.
3. **Walk-forward predijo correctamente** todos los fallos OOS.
4. **$0 de capital perdido.** Gates cumplieron su propósito.

## Decisión

**Cerrar la fase de research de estrategias. El proyecto continúa como bot framework.**

La investigación de señales de trading queda cerrada. El bot, su infraestructura,
risk management, test suites y backtest engine siguen en desarrollo activo.

## Qué cambia

- La carpeta `research/` queda congelada como referencia histórica.
- No se ejecutan más experimentos de estrategia sin un nuevo ADR que lo justifique.
- El desarrollo continúa en: execution engine, risk module, adapters, monitoring, tests.

## Qué NO cambia

- Constitution sigue vigente.
- Test suites siguen activas y deben pasar en CI.
- El framework acepta estrategias futuras que cumplan los gates.

## Condiciones para reabrir research

1. Nueva hipótesis con evidencia externa (no reciclada)
2. Fill model realista desde día 1
3. Walk-forward validation obligatorio
4. Nuevo ADR aprobando scope de investigación

## Referencias

- `research/lessons-learned-final.md`
- `research/full-period-audit.md`
- ADR-004 §Opción D, ADR-008 R3
