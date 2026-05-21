# Post-Mortem — Research v1 (Trend-Following Simple)

**Fecha:** 2026-04-05
**Branch:** `research/strategy-v2`
**Duración:** 14 días
**Experimentos ejecutados:** 20+ (E1 a E11c)
**Owner:** Cristhian Benitez
**Veredicto final:** Research v1 no produjo estrategia apta para live. OOS quemado. Pivot a v2 requerido.

---

## 1. Hipótesis original

Una de las siguientes estrategias trend-following, aplicada a Binance Spot en
timeframe 4h, tendría edge persistente suficiente para pasar Gate 1
(Sharpe ≥1.2 train+val, ≥0.8 OOS, MaxDD ≤30%):

- EMA crossover (con variantes de periodos y filtros)
- Donchian breakout
- SuperTrend
- Combinaciones con filtros de tendencia (SMA200)

---

## 2. Resultado ejecutivo

| Dimensión | Resultado |
|---|---|
| Estrategias que pasaron Gate 1 train+val | 1 (Ensemble 60/40 trend+MR) |
| Estrategias que pasaron Gate 1 OOS | **0** |
| OOS Sharpe del ensemble ganador | **+0.041** (gate ≥0.8) |
| OOS equity ensemble | $100 → $99.81 (breakeven) |
| Dataset OOS | **QUEMADO** (2024-2025 no reutilizable) |

---

## 3. Qué funcionó (metodología)

### 3.1 OOS seal respetado
No se miró OOS durante research. Esto no es trivial — la tentación existe.
Resultado: OOS válido como evaluación limpia.

### 3.2 Walk-forward como predictor
La tabla W3 walk-forward vs OOS real:

| Componente | W3 predicho | OOS real | Delta |
|---|---|---|---|
| Trend solo | -0.54 | -0.55 | 0.01 |
| MR solo | +0.70 | +0.72 | 0.02 |
| Ensemble | -0.22 | +0.04 | 0.26 |

**Conclusión:** el framework walk-forward **sí captura régimen real**. La
predicción de W3 coincidió con OOS dentro de ±0.03 Sharpe en los componentes
individuales. El framework funciona como señal de alerta.

### 3.3 Disciplina de sample size
Todas las variantes con <100 trades fueron marcadas "NEEDS-WORK" o
"muestra insuficiente" en vez de celebrarse. E2b (Sharpe 1.00, solo 21 trades)
NO fue promovida pese a métricas atractivas.

### 3.4 Sensibilidad a parámetros reportada
Cada experimento incluyó sweep ±20%. Esto detectó a tiempo fragilidades
(E3b-5p con sma_period 140-280: 37% drop en Sharpe).

### 3.5 Audit formal antes de OOS
El ensemble ganador (E11c) pasó auditoría de `backtest-validator` antes de
tocar OOS. No se saltó el gate.

### 3.6 Decisión honesta post-OOS
Cuando OOS falló, se escribió "NO live deployment" sin negociar el gate.
Este comportamiento es **la razón por la que la constitución existe**.

---

## 4. Qué no funcionó (estrategia)

### 4.1 Trend-following simple en spot crypto retail NO tiene edge persistente
Evidencia consolidada:
- EMA cross 12/26 y 50/200: Sharpe 0.58-1.00 train+val, principalmente por BTC,
  ETH drenaba pérdidas.
- SuperTrend: Sharpe 0.98, robusto pero no llega al gate.
- Donchian breakout: Sharpe 0.85.
- Ninguna variante pura de trend-following pasó Gate 1 train+val sola.

### 4.2 El edge está concentrado en régimen de rally
Walk-forward E3b-5p: W1+1.62 / W2+3.72 / **W3-0.52**.

El Sharpe agregado train+val (1.05) **oculta** que el edge existió solo en
régimen W2 (bull run 2024). En consolidación post-rally (W3), el edge desaparece
o se invierte.

### 4.3 Filtros de tendencia son frágiles
- SMA200 daily filter destruyó el edge (E3: Sharpe -0.71).
- SMA200 4h filter mejoró pero redujo trades a muestra insuficiente (E3b).
- ADX filter fue demasiado restrictivo (E8: exposure 1.7%, E8a: W3 sigue negativo).

**Conclusión:** filtros reducen exposición pero no resuelven el problema de
régimen. Siguen concentrando PnL en ventanas específicas.

### 4.4 Mean-reversion en bandas es la única señal que sobrevivió W3
- E10b BB(20, 2.75): W1+0.85 / W2+0.60 / **W3+0.70** (única estrategia con
  W3 positivo).
- Pero Sharpe agregado 0.69 no alcanzaba Gate 1 sola.
- Componente MR solo en OOS: Sharpe +0.72 (ligeramente bajo gate 0.8).

### 4.5 Naive ensemble NO compensó componente trend negativo
Hipótesis implícita: combinar trend (W2-strong) + MR (W3-strong) daría edge
todo-régimen. Realidad: la negatividad del componente trend en W3 y OOS
arrastró al ensemble a breakeven.

**Lección:** combinar estrategias no es garantía de diversificación real si
una de ellas tiene edge negativo en el régimen de evaluación.

---

## 5. Errores / gaps metodológicos

### 5.1 Demasiados experimentos sobre el mismo dataset (multiple testing)
20+ experimentos en train+val aumenta la probabilidad de encontrar un false
positive por azar. El ensemble ganador puede ser producto de data snooping
implícito aún respetando el OOS seal.

**Mitigación v2:** pre-registrar hipótesis antes de empezar. Reducir número
total de experimentos (≤6-8).

### 5.2 Falta de análisis de régimen explícito
Se iteró sobre señales asumiendo que "4h + filtro" resolvía régimen. En
realidad no se midió régimen explícitamente hasta E9 (walk-forward).

**Mitigación v2:** construir detector de régimen ANTES de elegir estrategia.
Mapear el histórico en regímenes y entender su distribución.

### 5.3 No se consideró ausencia de edge como hipótesis válida
El research asumió implícitamente que **alguna** estrategia trend-following
tendría edge. No se planificó una rama "qué hacer si ninguna funciona".

**Mitigación v2:** criterios de corte explícitos. Si en día X ninguna estrategia
regime-aware tiene Sharpe train+val ≥1.0, pivotar sin seguir intentando.

### 5.4 Gate Sharpe ≥1.2 puede ser poco realista para retail spot crypto
Literatura sugiere Sharpe 0.5-0.8 OOS es realista para retail trend-following
honesto. El gate 1.2 puede haber forzado ensembling forzado (E11c) en vez de
aceptar estrategias simples con Sharpe más modesto pero persistente.

**Mitigación v2:** ADR formal evaluando gate realista para retail spot crypto
antes de empezar.

---

## 6. Datos que aprendimos

### 6.1 Concentración de edge temporal
El edge de trend-following en 2024-2025 estuvo concentrado en ~25-33% del
período (ventana W2). Fuera de esa ventana, la estrategia sangra.

### 6.2 Asimetría BTC vs altcoins
BTC tiene mejor comportamiento trend (Sharpe 1.28-1.70 individual) que ETH
(Sharpe -0.12 a 0.63). Generalizar a 5 pares diluye edge.

### 6.3 Fees no son el problema
Total fees 4-10% del gross PnL. En estrategias con Sharpe malo, la causa es
señal ruidosa, no costos.

### 6.4 Mean-reversion tiene perfil defensivo
BB(20, 2.75) fue la única estrategia con 3 de 3 ventanas walk-forward positivas.
Es el candidato más robusto para "no perder plata" pero con retornos modestos.

### 6.5 Walk-forward predice OOS con alta fidelidad
Delta entre W3 predicho y OOS real fue ±0.03 Sharpe en componentes individuales.
Es evidencia de que el framework captura régimen real, no ruido.

---

## 7. Costos de v1

| Recurso | Costo |
|---|---|
| Tiempo calendario | 14 días (target cumplido) |
| Horas de trabajo | ~25-35h (estimado) |
| Capital en riesgo | **$0** (todo backtest) |
| Dataset OOS 2024-2025 | **QUEMADO** (costo de oportunidad alto) |
| Aprendizaje | Alto (ver sección 6) |

**ROI del research:** positivo. No perdimos capital y ganamos comprensión
fundamental del problema.

---

## 8. Decisión de path forward

**Opción elegida: A — Research v2 regime-aware**

Justificación:
1. Aprendizajes de v1 identifican el problema específico (régimen)
2. MR componente solo (Sharpe OOS +0.72) está a una distancia razonable del gate
3. Metodología funciona (walk-forward predice OOS)
4. Nueva data disponible para OOS fresco (pre-2024 + 2026+)

---

## 9. Principios derivados para v2 (candidatos a ADR)

### P1 — Detector de régimen antes que estrategia
No implementar señales sin un clasificador de régimen funcionando primero.

### P2 — Gate realista con justificación literaria
Evaluar bajar gate train+val a ≥1.0 y OOS a ≥0.5 con ADR formal que cite
benchmarks retail documentados.

### P3 — Pre-registro de hipótesis
Antes de empezar v2, escribir lista exhaustiva de variantes a probar (≤8).
No agregar experimentos post-hoc salvo con justificación explícita.

### P4 — Criterio de corte ex-ante
Definir día máximo de v2 y condiciones de "abandonar trend-following" antes
de empezar.

### P5 — Separar data estrictamente
Train/val: 2020-2023. OOS nuevo: 2024-2026. No mezclar.

### P6 — Aceptar "no hay edge" como outcome válido
Si v2 falla OOS, considerar Opción C (futures / pair trading) o D (cerrar).
No ensuciar OOS fresco iterando hasta que pase.

---

## 10. Action items inmediatos

- [ ] Tag commit actual como `research-v1-complete`
- [ ] Mergear branch `research/strategy-v2` (research actual) a main **sin
      modificar v2 plan** (el branch queda como archivo histórico)
- [ ] Crear branch nuevo `research/strategy-v3-regime-aware`
- [ ] Descargar histórico extendido BTC/ETH 2020-2023 (Binance klines)
- [ ] Escribir ADR-002: "Research v1 completed, pivot to regime-aware"
- [ ] Escribir ADR-003: "Gate adjusted with literature benchmarks"
- [ ] Escribir `research/plan-v2.md` con experimentos regime-aware pre-registrados

---

## 11. Reflexión honesta

Este research **no falló** — produjo el resultado más valioso que puede
producir un research honesto: **evidencia de que la hipótesis original era
incompleta**.

Un research "exitoso" que hubiera pasado OOS sin entender el mecanismo habría
sido peligroso para live. Uno que falla OOS con comprensión del por qué es
un triunfo metodológico.

**Costo real:** 14 días y un dataset OOS. **Valor obtenido:** saber que
trend-following simple no funciona en spot crypto retail sin regime-awareness.

Esta lección se paga o con backtest honesto o con capital real. Pagarla en
backtest es lo que hace que el próximo intento valga la pena.
