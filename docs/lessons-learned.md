# Lessons Learned Final -- Chocotrader

**Fecha:** 2026-04-06
**Proyecto:** Chocotrader -- Bot trend-following automatizado, Binance Spot
**Alcance:** Research v1 + v2 + Auditoria final periodo completo 2017-2026
**Veredicto:** NO se encontro estrategia activa que justifique deployment a live
**Capital en riesgo durante todo el proyecto:** $0

---

## 1. Resumen ejecutivo

Chocotrader investigo durante ~16 dias calendario (~30-40h de trabajo) si
alguna estrategia trend-following o mean-reversion, aplicada a Binance Spot
con costos realistas (0.30% round-trip), podia superar a buy & hold BTC como
para justificar un bot automatizado con $100 de capital inicial. Tras 20+
experimentos en v1, un pivot a deteccion de regimen en v2, y una auditoria
final de 144 combinaciones sobre 9 anos de datos (2017-2026), la conclusion
es definitiva: las estrategias activas probadas logran mejor riesgo ajustado
(SuperTrend BTC: Sharpe 0.98, MaxDD -14% vs B&H MaxDD -84%) pero capturan
solo el 15% del retorno absoluto ($219 vs $1,596). Ningun edge activo fue
consistente en todos los sub-periodos, y la unica senal que parecia tener
edge independiente (BB mean-reversion, Sharpe OOS +0.72 en v1) resulto ser
un artefacto del modelo de fill optimista -- con fill realista colapso a
Sharpe -0.56. El proyecto no perdio capital, produjo un framework de
investigacion reutilizable validado, y la decision honesta de no deployar
es el outcome correcto.

---

## 2. Hallazgos tecnicos (ordenados por importancia)

### 2.1 El modelo de fill es critico para mean-reversion, irrelevante para trend-following

**Impacto: ALTO -- habria evitado semanas de trabajo si se validaba primero.**

La senal BB(20, 2.75) mostro Sharpe OOS +0.72 en v1 con fill instantaneo al
cierre de la vela de senal. Con fill realista R7 (signal at close[N], fill at
open[N+1]), el Sharpe colapso a -0.56. La discrepancia es de -1.26 Sharpe.

Para trend-following (EMA, SuperTrend, Donchian), la sensibilidad al fill
model fue casi nula: |delta| < 0.01 Sharpe. Esto se explica por la naturaleza
de cada estrategia:

- **Mean-reversion** depende de capturar el rebote inmediato desde un extremo.
  Con 4h de delay, el rebote ya ocurrio parcialmente. El timing es el edge.
- **Trend-following** depende de capturar movimientos multi-vela. Una vela de
  delay es ruido frente a un trend de semanas.

**Leccion:** antes de invertir tiempo en optimizacion de senales, validar que
el modelo de fill no invalida la premisa de la estrategia.

### 2.2 BTC buy & hold tiene Sharpe ~0.81 en 9 anos -- una barrera muy alta

**Impacto: ALTO -- debia ser el benchmark desde el dia 1.**

BTC B&H entre 2017-2026: $100 a $1,596, Sharpe 0.81, MaxDD -84%. Cualquier
estrategia activa que aspire a "superar al mercado" en retorno absoluto
necesita Sharpe > 0.81 sostenido, lo cual es extremadamente dificil para
retail spot sin apalancamiento, sin short-selling, y con costos de 0.30%
por trade.

Las mejores estrategias activas alcanzaron:

| Estrategia | Equity final | Sharpe | MaxDD |
|---|---|---|---|
| B&H BTC | $1,596 | 0.81 | -84% |
| SuperTrend BTC conservative | $219 | 0.98 | -14% |
| EMA BTC aggressive compound | $466 | 0.98 | -37% |
| SuperTrend BTC aggressive compound | $463 | 1.03 | -25% |

Las estrategias activas ganan en riesgo ajustado pero pierden
contundentemente en retorno absoluto. Un inversor con horizonte largo y
tolerancia a drawdowns de -84% esta mejor con B&H.

### 2.3 ADX como detector de regimen: clasifica pero no filtra

**Impacto: MEDIO -- consumio el nucleo de v2.**

ADX (Wilder 1978) con umbrales absolutos 25/20 alcanzo ~40% de coherencia
con labels manuales de regimen. Esto es util para analisis retrospectivo
pero inutilizable como filtro de trading por dos razones estructurales:

1. **Lag de confirmacion:** ADX confirma tendencia ~28 bars despues del onset.
   Cuando ADX > 25, el movimiento ya fue capturado por indicadores mas rapidos.
   Resultado en E1: anti-edge (Sharpe -0.40).

2. **Damage de transicion:** Los cambios de regimen del detector causan exits
   prematuros. En E3, 58.9% de los trades cerraron por REGIME_EXIT, no por
   senal de la estrategia. La clasificacion "correcta" destruye trades abiertos.

**Leccion:** un indicador lagging puede clasificar regimen en retrospectiva
pero no puede filtrar trades en tiempo real sin causar timing damage.

### 2.4 Rolling quantiles se auto-derrotan en indicadores de fuerza

**Impacto: MEDIO -- invalido detector v1 de E0.**

La primera iteracion del detector uso percentiles rodantes (Q80/Q60) sobre
ADX y BBW. Resultado: 15.80% de coherencia con rallies (target era 70%).
La razon es que la propia persistencia del indicador durante trends eleva
el umbral del quantil. Cuando ADX esta alto sostenidamente, Q80 sube,
haciendo que el threshold se mueva en contra de la deteccion.

Solo aplican a indicadores cuya base cambia macro-ciclicamente (como
volatilidad), no a indicadores de fuerza directional.

### 2.5 Compounding amplifica tanto edge como anti-edge

**Impacto: MEDIO -- explica divergencias entre escenarios.**

Con position sizing compuesto:
- EMA BTC aggressive: $100 a $466 (vs $288 flat) -- amplifica edge positivo.
- BB ETH: stopped en todos los escenarios -- amplifica anti-edge hasta
  triggear min equity stop.

No es un hallazgo sorprendente, pero importa operativamente: una estrategia
marginalmente negativa se convierte en desastrosa con compounding.

### 2.6 ETH es sistematicamente peor que BTC para trend-following

**Impacto: BAJO-MEDIO -- confirma hallazgo de v1.**

En la auditoria final, cada estrategia activa tuvo peor Sharpe en ETH que
en BTC. Multiples combinaciones ETH aggressive activaron el min equity stop
($80). ETH tiene mas ruido, mas drawdowns abruptos, y menor tendencia
sostenida que BTC.

### 2.7 Capital de $100 es demasiado pequeno para position sizing significativo

**Impacto: BAJO -- constrains operativos, no invalida conclusiones.**

Con $100 y posicion maxima de 20% equity ($20), fees de 0.30% round-trip
representan $0.06 por trade. En estrategias con 200-300 trades en 9 anos,
los fees acumulados son significativos (~$12-18, o 12-18% del capital).
Con $1,000 los porcentajes son identicos pero el capital residual permite
mas granularidad en sizing.

La auditoria confirmo que escalar de $100 a $1,000 no cambia Sharpe ni
ratios -- solo escala linealmente los valores absolutos.

---

## 3. Hallazgos metodologicos

### 3.1 Pre-registro previene p-hacking

v1 ejecuto 20+ experimentos sin pre-registro, lo que introduce riesgo de
data snooping implicito. v2 pre-registro E0-E6 antes de empezar y ejecuto
exactamente los planificados. No se agregaron experimentos post-hoc.

El contraste es claro: v2 fue mas eficiente (1 dia vs 14 dias), mas
disciplinado, y la conclusion fue igual de valida.

### 3.2 Walk-forward predice OOS con alta fidelidad

La ventana W3 del walk-forward predijo el Sharpe OOS real dentro de +/-0.03:

| Componente | W3 predicho | OOS real | Delta |
|---|---|---|---|
| Trend solo | -0.54 | -0.55 | 0.01 |
| MR solo | +0.70 | +0.72 | 0.02 |

Esto valida el framework walk-forward como herramienta de prediccion. No
como garantia, pero si como senal de alerta confiable.

### 3.3 Gates + time-box fuerzan decisiones honestas

La constitucion definio gates estrictos (Sharpe >= 1.2 train+val, >= 0.8 OOS,
MaxDD <= 30%) y time-box (14 dias v1, 6 semanas v2). Cuando ninguna
estrategia paso, el framework forzo la decision correcta: no deployar.

Sin gates, la tentacion de "bajar un poco el criterio" o "probar una variante
mas" habria extendido el research indefinidamente.

### 3.4 OOS seal funciono

El dataset OOS 2026-Q1 se mantuvo intocado a traves de 20+ experimentos en
v1 y 5+ en v2. Se uso chmod 0444 como proteccion fisica. Cuando se uso OOS
en v1, fue una sola vez, y el resultado (Sharpe 0.04) confirmo que no habia
edge.

### 3.5 Min equity stop identifica estrategias perdedoras temprano

La constitucion define min equity $80 USD. En la auditoria final, todas las
combinaciones BB ETH y varias ETH aggressive triggearon este stop. Funciona
como kill-switch: no permite que una estrategia mala destruya todo el capital.

### 3.6 ADRs documentan el trail de decisiones

Se produjeron ADRs 001-008 cubriendo: spot-only, research v1 pivot, gate
adjustment, regime-aware plan, detector metrics, abort decisions, y test
tardio BB. Cada decision tiene contexto, alternativas consideradas, y
justificacion.

Para futuro research, el trail de ADRs es mas valioso que los resultados
numericos porque explica el *por que* de cada pivot.

---

## 4. Que hariamos diferente empezando de cero

### 4.1 Validar el modelo de fill ANTES de cualquier otra cosa

El hallazgo mas impactante del proyecto (BB edge era artefacto del fill
model) se descubrio en v2, despues de 14 dias de v1 iterando sobre senales
con fill optimista. Si se hubiera implementado fill_mode=next_open desde el
dia 1, BB habria sido descartada inmediatamente y v1 habria terminado con
la misma conclusion en menos tiempo.

**Regla propuesta:** todo backtest engine debe tener fill_mode=next_open como
default, y fill_mode=same_close como opcion que requiere justificacion
explicita.

### 4.2 Benchmark contra B&H desde el dia 1

v1 no comparo sistematicamente contra B&H hasta tarde en el proceso. Si la
primera tabla de resultados hubiera incluido B&H BTC como fila de referencia,
las expectativas habrian sido mas realistas desde el inicio.

**Regla propuesta:** todo reporte de backtest debe incluir B&H del activo
principal como primera fila de la tabla de metricas.

### 4.3 No asumir que indicadores tecnicos tienen edge en crypto spot

La hipotesis implicita de v1 era "alguna combinacion de EMA/SuperTrend/
Donchian/BB tendra edge en crypto spot". Despues de 144 combinaciones en
9 anos de datos, la evidencia dice que no. Los indicadores tecnicos clasicos
fueron disenados para mercados con microestructura diferente (equities,
commodities). Crypto spot tiene:

- Volatilidad extrema que destruye trailing stops.
- Bear markets de -80% que destruyen long-only.
- Ausencia de mean-reversion confiable (no hay "valor fundamental" como ancla).
- Barra alta de B&H por apreciacion secular de BTC.

### 4.4 Considerar alternativas de mercado mas temprano

El proyecto se auto-limito a spot-only por la constitucion (Art. 0). Esto
es prudente para capital preservation pero elimina herramientas fundamentales:

- **Futures:** permiten short-selling, eliminando la asimetria long-only.
- **Options:** permiten estrategias de volatilidad sin direccionalidad.
- **Cross-exchange arb:** edge mas robusto que prediccion direccional.

Si el objetivo es "generar retorno activo", spot-only es un handicap
estructural. Si el objetivo es "proteger capital", B&H + DCA es mas simple
y mas efectivo que un bot.

### 4.5 Menos tiempo en deteccion de regimen, mas en identificacion de alpha

v2 invirtio esfuerzo significativo en construir un detector de regimen
(ADX + BBW + ATR) que resulto inutilizable para trading. El problema no era
"operar en el regimen equivocado" sino "no tener alpha source".

Un detector de regimen es util para position sizing o risk management, no
como filtro binario de entry/exit.

### 4.6 $100 de capital inicial es insuficiente para un bot con fees

Con 0.30% round-trip y posiciones de $20, se necesitan movimientos de >0.30%
solo para cubrir costos. Esto es viable en crypto (alta volatilidad), pero el
capital es tan chico que no permite diversificacion real ni absorcion de
drawdowns sin triggear min equity stops.

Un capital minimo mas realista para operar con fees seria $500-$1,000.

---

## 5. Activos reutilizables

### 5.1 Data pipeline

- 66,000+ velas de 4h, 5 pares (BTC, ETH, SOL, BNB, XRP contra USDT).
- Cobertura continua 2017-01 a 2026-04 sin gaps.
- Script de descarga incremental funcional (gap_2024_2025 + recent).
- Formato parquet, listo para pandas/vectorbt.
- Tambien disponible en 1d para analisis de mas largo plazo.

### 5.2 Backtest engine

- Fill model configurable (same_close, next_open).
- Position sizing flat y compuesto.
- Perfiles de riesgo (conservative, aggressive, ultra_conservative).
- Min equity stop configurable.
- Output estandarizado en CSV con todas las metricas.

### 5.3 Generadores de senales

Funciones puras en `core/strategy/` y `research/signals.py`:
- EMA crossover (configurable fast/slow).
- SuperTrend (ATR-based, configurable period/multiplier).
- Donchian breakout (configurable entry/exit periods).
- Bollinger Bands mean-reversion (configurable period/std).

### 5.4 Framework de metricas

Calculo estandarizado de:
- Sharpe ratio (annualized, rf=0).
- Sortino ratio.
- Calmar ratio.
- MaxDD (absoluto y duracion en dias).
- Win rate, Profit factor.
- Avg Win / Avg Loss.
- Max consecutive losses / negative months.
- Exposure time.
- Total fees.

### 5.5 Framework walk-forward

- Train/validation/OOS split configurable.
- Ventanas rodantes (W1, W2, W3).
- Prediccion validada: delta OOS < +/-0.03 Sharpe.

### 5.6 Detector de regimen

- ADX + BBW + ATR con umbrales configurables.
- Debounce, cooldown, hysteresis para estabilidad.
- Util para clasificacion retrospectiva y analisis.
- **NO util para filtrado de trades en tiempo real.**

### 5.7 Framework de gobernanza

- `constitution.md` con principios no-negociables.
- Template de ADR con secciones estandarizadas.
- Template de pre-registro de experimentos.
- Gates secuenciales (backtest -> testnet -> mainnet).
- Kill-switches y min equity stops.
- OOS seal con chmod 0444.

---

## 6. Tabla de costos

### 6.1 Inversion total

| Concepto | v1 | v2 | Auditoria final | Total |
|---|---|---|---|---|
| Dias calendario | 14 | ~1 | ~1 | ~16 |
| Horas trabajo (est.) | 25-35h | ~4-6h | ~4-6h | ~30-40h |
| Experimentos | 20+ | 5 (E0x2, E1, E3, C2) | 144 combinaciones | ~170 |
| Capital en riesgo | $0 | $0 | $0 | **$0** |
| Dataset OOS quemado | 2024-2025 | Ninguno (2026-Q1 intocado) | N/A | 1 periodo |

### 6.2 Que valio la pena

| Actividad | Costo | Valor producido |
|---|---|---|
| Fill model R7 (v2) | ~2h | Evito deployar estrategia con edge ilusorio. Habria perdido capital real. |
| Walk-forward framework (v1) | ~6h | Validado como predictor (+/-0.03 Sharpe). Reutilizable en cualquier proyecto. |
| B&H benchmark (auditoria) | ~2h | Establecio la barrera real. Cambio la interpretacion de todos los resultados anteriores. |
| Data pipeline | ~8h | 66k+ velas limpias, continuas, 9 anos. Reutilizable indefinidamente. |
| Constitution + ADRs | ~4h | Framework de gobernanza transferible a cualquier proyecto quant. |
| Pre-registro v2 | ~1h | Previno data snooping. v2 fue 10x mas eficiente que v1 en tiempo. |

### 6.3 Que NO valio la pena

| Actividad | Costo | Por que no valio |
|---|---|---|
| Iteracion extensiva de regimen (E0 iter1 -> iter2 -> AMEND) | ~4h | El resultado era previsible: ADX es lagging por construccion. Bastaba con leer Wilder 1978. |
| 20+ experimentos v1 sin pre-registro | ~15h | Data snooping implicito. Con pre-registro + B&H benchmark, habrian bastado 5-6 experimentos. |
| Optimizacion de BB sin validar fill model | ~4h | Todo el trabajo sobre BB en v1 fue invalidado por fill model. Esfuerzo desperdiciado. |
| Ensemble trend+MR (E11c) | ~3h | Combinar una estrategia con anti-edge no produce edge. Previsible en retrospectiva. |

### 6.4 ROI del proyecto

El proyecto no genero retorno financiero, pero evito perdida de capital real.
Si se hubiera deployado la estrategia BB con fill optimista (la "ganadora" de
v1), habria perdido ~$17-26 de $100 en el primer ano basado en la auditoria
final (BB BTC conservative: -17%, BB ETH: stopped at -20%).

**Costo de oportunidad:** $100 en B&H BTC desde enero 2026 habria generado
retorno de mercado. Pero el proyecto nunca arriesgo capital, asi que el costo
de oportunidad real es solo el tiempo invertido.

**Valor intangible:** framework de investigacion validado, data pipeline
reutilizable, comprension profunda de por que retail trend-following en
crypto spot no funciona, y la disciplina de aceptar "no hay edge" como
resultado valido.

---

## Nota final

Este documento cierra la fase de research activo de Chocotrader. El
repositorio queda archivado como referencia. Los activos reutilizables
(seccion 5) estan disponibles para futuros proyectos quant que exploren
mercados con mejor estructura para alpha activo (futures, options,
cross-exchange).

La leccion mas importante no es tecnica: es que un proceso de investigacion
honesto que concluye "no hay edge" vale mas que un backtest overfitted que
dice "Sharpe 2.0" y pierde dinero en live. Pagar esa leccion con tiempo de
backtest en vez de capital real es exactamente para lo que existe un framework
de research riguroso.
