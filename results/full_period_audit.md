# Auditoria Final — Periodo Completo 2017-2026

**Fecha:** 2026-04-06
**Branch:** `research/strategy-v3-regime-aware`
**Periodo evaluado:** 2017-01 a 2026-04 (~9.25 anos)
**Combinaciones ejecutadas:** 144 (8 estrategias x 2 pares activos x 4 escenarios de capital x 3 perfiles de riesgo)
**Fill model:** `next_open` (signal at close[N], fill at open[N+1]) -- el modelo realista validado en v2
**Owner:** Cristhian Benitez

---

## 1. Resumen ejecutivo

Ninguna estrategia activa supera a Buy & Hold BTC en retorno absoluto sobre el periodo completo 2017-2026. Las mejores estrategias activas (SuperTrend y EMA crossover en BTC) ofrecen Sharpe ratios entre 0.90 y 1.05 con drawdowns de 13-37%, significativamente mejores en riesgo que B&H BTC (MaxDD -83.9%), pero generan entre 7x y 14x menos retorno absoluto. La unica estrategia que roza el gate de Sharpe >= 1.2 es EMA BTC en perfil agresivo (1.045), pero requiere 40% de equity por posicion y 7.5bps de fees -- supuestos optimistas para $100 de capital real. Mean-reversion (Bollinger Bands) es negativa en todas las combinaciones, confirmando los hallazgos de v1 y v2. La conclusion es inequivoca: no existe edge activo explotable que justifique operar este bot con capital real.

---

## 2. Tabla de referencia: todas las estrategias, $1000 compound, conservador

Esta es la tabla canonica con el escenario mas representativo de operacion real.

| Estrategia | Equity Final | Retorno | Sharpe | Sortino* | MaxDD | Trades | WinRate | PF | Exposure |
|---|---|---|---|---|---|---|---|---|---|
| BB(20,2.75) BTC | $835.94 | -16.4% | -0.358 | -0.48 | -20.6% | 145 | 58.6% | 0.70 | 12.9% |
| BB(20,2.75) ETH | $796.28 | -20.4% | -0.529 | -0.71 | -24.0% | 20 | 35.0% | 0.20 | 2.3% |
| EMA(12/26) BTC | $2,203.14 | +120.3% | 0.903 | ~1.25 | -21.6% | 315 | 27.9% | 1.47 | 52.4% |
| EMA(12/26) ETH | $1,913.80 | +91.4% | 0.635 | ~0.88 | -18.4% | 336 | 26.2% | 1.29 | 51.7% |
| SuperTrend(10,3) BTC | $2,190.10 | +119.0% | 0.977 | ~1.38 | -13.7% | 225 | 37.8% | 1.59 | 52.0% |
| SuperTrend(10,3) ETH | $2,371.74 | +137.2% | 0.840 | ~1.16 | -17.6% | 222 | 37.4% | 1.51 | 50.5% |
| Donchian(20/10) BTC | $1,746.35 | +74.6% | 0.780 | ~1.05 | -19.0% | 249 | 38.6% | 1.44 | 41.4% |
| Donchian(20/10) ETH | $1,749.61 | +75.0% | 0.592 | ~0.80 | -20.2% | 265 | 31.7% | 1.30 | 41.1% |
| Buy & Hold BTC | $15,958.24 | +1495.8% | 0.809 | ~1.10 | -83.9% | 1 | 100% | inf | 100% |
| Buy & Hold ETH | $6,941.70 | +594.2% | 0.694 | ~0.93 | -94.1% | 1 | 100% | inf | 100% |
| DCA mensual BTC | $4,866.89 | +386.7% | 0.650 | ~0.88 | -69.5% | - | - | - | 100% |
| DCA mensual ETH | $4,148.11 | +314.8% | 0.575 | ~0.78 | -77.0% | - | - | - | 100% |

*Sortino estimado a partir de Sharpe y perfil de retornos tipico de cada estrategia.

**Observaciones clave:**
- B&H BTC genera 16x sobre $1,000. Ninguna estrategia activa supera 2.4x.
- SuperTrend BTC tiene el mejor Sharpe (0.977) entre las activas conservadoras.
- BB es la unica estrategia con Sharpe negativo -- pierde dinero sistematicamente.
- BB ETH tiene solo 20 trades y 2.3% de exposicion: estadisticamente irrelevante.

---

## 3. Top 5 por equity final (entre las 144 combinaciones)

| # | Estrategia | Escenario | Perfil | Equity Final | Sharpe |
|---|---|---|---|---|---|
| 1 | Buy & Hold BTC | $1000 compound | Agresivo | $15,972.61 | 0.810 |
| 2 | Buy & Hold BTC | $1000 compound | Conservador | $15,958.24 | 0.809 |
| 3 | Buy & Hold ETH | $1000 compound | Conservador | ~$6,941 | 0.694 |
| 4 | DCA mensual BTC | $1000 compound | Conservador | ~$4,867 | 0.650 |
| 5 | EMA(12/26) BTC | $1000 compound | Agresivo | $4,656.98 | 0.975 |

B&H BTC domina por margen aplastante. La mejor estrategia activa (EMA BTC agresivo compuesto) llega a un tercio.

---

## 4. Top 5 por Sharpe ratio (entre las 144 combinaciones)

| # | Estrategia | Escenario | Perfil | Sharpe | MaxDD | Equity Final |
|---|---|---|---|---|---|---|
| 1 | EMA(12/26) BTC | $1000 flat | Agresivo | 1.045 | -37.2% | ~$2,880 |
| 2 | SuperTrend(10,3) BTC | $1000 flat | Agresivo | 1.032 | -27.4% | ~$2,750 |
| 3 | SuperTrend(10,3) BTC | $1000 compound | Agresivo | 1.030 | -27.4% | ~$2,870 |
| 4 | SuperTrend(10,3) BTC | $1000 flat | Conservador | 0.999 | -13.7% | ~$2,190 |
| 5 | EMA(12/26) BTC | $1000 compound | Agresivo | 0.975 | -37.2% | $4,656.98 |

**Nota critica:** los unicos Sharpe >= 1.0 requieren perfil agresivo (40% equity por posicion, fees 7.5bps). Con perfil conservador (el realista para capital real), ningun Sharpe supera 1.0. El gate constitucional de Sharpe >= 1.2 no se alcanza en ningun caso.

---

## 5. Comparacion directa: mejor activa vs B&H vs DCA por escenario de capital

### $100 flat (stop en $80)

| Metrica | Mejor activa (EMA BTC agr.) | B&H BTC | DCA BTC |
|---|---|---|---|
| Equity final | ~$288 | ~$1,597 | ~$487 |
| Sharpe | 1.045 | 0.809 | 0.650 |
| MaxDD | -37.2% | -83.9% | -69.5% |
| Riesgo de stop | Bajo | Alto ($16 minimo) | Medio |

### $100 compound (stop en $80)

| Metrica | Mejor activa (EMA BTC agr.) | B&H BTC | DCA BTC |
|---|---|---|---|
| Equity final | ~$466 | ~$1,597 | ~$487 |
| Sharpe | 0.975 | 0.809 | 0.650 |
| MaxDD | -37.2% | -83.9% | -69.5% |

### $1000 flat (stop en $800)

| Metrica | Mejor activa (ST BTC cons.) | B&H BTC | DCA BTC |
|---|---|---|---|
| Equity final | ~$2,190 | ~$15,958 | ~$4,867 |
| Sharpe | 0.999 | 0.809 | 0.650 |
| MaxDD | -13.7% | -83.9% | -69.5% |

### $1000 compound (stop en $800)

| Metrica | Mejor activa (EMA BTC agr.) | B&H BTC | DCA BTC |
|---|---|---|---|
| Equity final | $4,656.98 | $15,958.24 | $4,866.89 |
| Sharpe | 0.975 | 0.809 | 0.650 |
| MaxDD | -37.2% | -83.9% | -69.5% |

**Patron consistente en todos los escenarios:**
- B&H BTC gana en retorno absoluto por amplio margen.
- Las estrategias activas ganan en Sharpe y MaxDD.
- DCA BTC ofrece un punto medio razonable.
- Con $100, las diferencias absolutas son irrelevantes (la mejor activa genera ~$188-$366 de ganancia en 9 anos).

---

## 6. Analisis por sub-periodos (retorno mensual promedio, $1000 compound conservador)

| Periodo | Mercado | EMA BTC | ST BTC | DON BTC | BB BTC | B&H BTC | DCA BTC |
|---|---|---|---|---|---|---|---|
| 2017-2019 | Mixed/Bull | +1.54% | +0.90% | n/a* | neg | +4.54% | +3.2%** |
| 2020-2021 | Bull fuerte | +1.65% | +1.98% | n/a* | neg | +10.45% | +7.8%** |
| 2022 | Bear (LUNA/FTX) | -1.27% | -0.86% | n/a* | neg | -6.99% | -4.1%** |
| 2023 | Recovery | +1.23% | +1.29% | n/a* | neg | +9.06% | +6.5%** |
| 2024-2025 | Bull maduro | +0.28% | +0.38% | n/a* | neg | +4.03% | +3.0%** |
| 2026 Q1 | Correccion | -1.28% | -1.02% | n/a* | neg | -5.41% | -3.8%** |

*Donchian no desagregado por sub-periodo en los resultados del audit.
**DCA estimado como fraccion del B&H proporcional al timing de compras.

### Acumulados por sub-periodo (mejores activas)

| Periodo | EMA BTC cumul | ST BTC cumul | B&H BTC cumul |
|---|---|---|---|
| 2017-2019 | +44.6% | +26.0% | +131.7% |
| 2020-2021 | +39.5% | +47.4% | +250.8% |
| 2022 | -15.3% | -10.3% | -83.8% |
| 2023 | +14.8% | +15.5% | +108.7% |
| 2024-2025 | +6.6% | +9.0% | +96.8% |
| 2026 Q1 | -5.1% | -4.1% | -21.6% |

**Hallazgos de regimen:**
1. **Ninguna estrategia activa fue positiva en todos los sub-periodos.** 2022 fue negativo para todas. 2026 Q1 tambien.
2. **B&H pierde mas en bears pero gana mucho mas en bulls.** La asimetria favorece al pasivo a largo plazo.
3. **Las activas capturan ~10-20% de los bulls pero evitan ~70-85% de los bears.** Esto mejora Sharpe pero destruye retorno absoluto.
4. **2024-2025 (bull maduro) fue pobre para activas.** EMA BTC solo +6.6% en 2 anos vs B&H +96.8%. El trend-following sufre en mercados que suben gradualmente sin pullbacks fuertes.

---

## 7. Sensibilidad al fill model

| Estrategia | Sharpe next_open | Sharpe close | Delta |
|---|---|---|---|
| BB(20,2.75) BTC | -0.358 | -0.362 | +0.004 |
| BB(20,2.75) ETH | -0.529 | -0.531 | +0.002 |
| EMA(12/26) BTC | 0.903 | 0.905 | -0.002 |
| EMA(12/26) ETH | 0.635 | 0.633 | +0.002 |
| SuperTrend(10,3) BTC | 0.977 | 0.978 | -0.001 |
| SuperTrend(10,3) ETH | 0.840 | 0.941 | **-0.101** |
| Donchian(20/10) BTC | 0.780 | 0.776 | +0.004 |
| Donchian(20/10) ETH | 0.592 | 0.693 | **-0.101** |

**Conclusion sobre fill model:**
- Para BTC, la diferencia entre fill models es despreciable (|delta| < 0.005).
- Para ETH SuperTrend y Donchian, `next_open` cuesta ~0.10 puntos de Sharpe. Esto sugiere que ETH tiene spreads/gaps mas amplios entre close y open, penalizando strategies que dependen de ejecucion rapida.
- **next_open es el modelo correcto.** Los resultados con fill at close serian levemente optimistas pero no cambian ninguna conclusion.

---

## 8. Estrategias detenidas por min equity

| Estrategia | Combinaciones detenidas | Equity al stop |
|---|---|---|
| BB(20,2.75) ETH | **12 de 12** (todas) | < $80 / $800 |
| BB(20,2.75) BTC agresivo | 4 de 4 | $741 - $764 |
| SuperTrend(10,3) ETH agresivo | 2+ | ~$773 |
| Donchian(20/10) ETH agresivo | 2+ | ~$781 |

BB ETH habria sido liquidada (por reglas internas) en el 100% de los escenarios. Esto confirma que BB mean-reversion long-only en crypto spot es estructuralmente no viable.

---

## 9. Conclusiones honestas

### Pregunta 1: Existe edge explotable en alguna estrategia activa?

**No.** Ningun escenario alcanza el gate constitucional de Sharpe >= 1.2 con perfil conservador. Los mejores Sharpe activos (0.97-1.05) requieren perfil agresivo con supuestos de costos optimistas (7.5bps fees) y posiciones del 40% del equity -- parametros que no son realistas para $100 de capital en Binance Spot.

Ademas, el Sharpe de las activas no es estable entre sub-periodos. En 2024-2025, EMA BTC genero solo +0.28%/mes -- un rendimiento que no compensa la complejidad operacional.

### Pregunta 2: Alguna estrategia activa supera a Buy & Hold?

**En retorno absoluto: no, ni remotamente.** B&H BTC genera $15,958 vs $4,657 de la mejor activa (EMA BTC agresivo compound). La diferencia es 3.4x.

**En metricas ajustadas por riesgo: marginalmente.** SuperTrend BTC tiene Sharpe 0.977 vs B&H 0.809, y MaxDD -13.7% vs -83.9%. Pero este "mejor riesgo" se paga con 7x menos retorno.

**La paradoja:** las estrategias activas son mejores gestoras de riesgo pero peores generadoras de retorno. Para alguien con $100 de capital, el riesgo de MaxDD -84% en B&H es irrelevante (perderia $84), mientras que la diferencia de retorno ($1,497 vs $366) es significativa.

### Pregunta 3: Cual es la mejor opcion para $100 de capital real?

**DCA mensual en BTC.** Razones:
- No requiere infraestructura (bot, servidor, monitoreo, alertas).
- Genera ~$387 en el periodo ($487 equity final) vs ~$188-$366 de las activas.
- MaxDD de -69.5% suena aterrador pero en $100 significa $69.50 de drawdown temporal -- tolerable psicologicamente.
- Cero costos operacionales (no hay fees de trading frecuente, no hay slippage por ordenes pequenas).
- No tiene riesgo de bugs, API failures, o desincronizacion de estado.

Para capital bajo ($100-$1,000), la complejidad de un bot de trading activo no se justifica economicamente. El retorno incremental (si lo hay) es inferior al costo de oportunidad del tiempo de desarrollo y mantenimiento.

### Pregunta 4: Se justifica continuar el desarrollo del bot?

**No.** Las razones son multiples y convergentes:

1. **Gate no alcanzado.** Ningun escenario conservador pasa Sharpe >= 1.2. La constitucion es clara.
2. **Retorno absoluto irrisorio con $100.** La mejor activa genera ~$25-40/ano en el mejor caso. El costo de un VPS para correr el bot supera ese retorno.
3. **Sin edge estable entre regimenes.** Todas las activas perdieron dinero en 2022 y 2026 Q1. No hay evidencia de que protejan capital mejor que simplemente no estar en el mercado.
4. **Mean-reversion descartada definitivamente.** BB pierde dinero en todas las combinaciones, con 12/12 escenarios ETH detenidos por min equity.
5. **El trend-following funciona pero no lo suficiente.** SuperTrend y EMA capturan tendencias reales, pero los costos de friccion, las senales falsas en rangos, y la incapacidad de capturar bull runs completos (50% exposure) destruyen la ventaja.
6. **Confirmacion de v1 y v2.** Este audit con periodo completo y 144 combinaciones confirma lo que v1 (Sharpe OOS 0.041) y v2 (BB con fill realista Sharpe -0.56) ya sugerian: no hay edge explotable.

**Recomendacion final:** archivar el repositorio como referencia de research. El framework metodologico (pre-registro, gates, OOS seal, fill model realista) es el activo mas valioso del proyecto y es transferible a futuros proyectos con hipotesis mas prometedoras.

---

## Apendice: detalle del mejor escenario activo

**EMA(12/26) BTC, $1000 compound, agresivo (40% posicion, 7.5bps fees, 3bps slippage)**

| Metrica | Valor |
|---|---|
| Equity final | $4,656.98 |
| Retorno total | +365.7% |
| Retorno anualizado | 19.52% |
| Sharpe | 0.975 |
| MaxDD | -37.21% |
| Duracion MaxDD | 865.8 dias (~2.4 anos) |
| Profit Factor | 1.379 |
| Trades | 315 |
| Win Rate | 28.6% |
| Avg Win / Avg Loss | 3.45 |
| Exposure | 52.4% |
| Peor mes | -9.34% |
| Mejor mes | +28.48% |
| Max meses negativos consecutivos | 8 |

Este es el techo de lo que las estrategias activas pueden ofrecer en el mejor de los casos. Un Sharpe de 0.975 con MaxDD de -37% y un drawdown que dura casi 2.5 anos no es operable con capital real bajo. Ocho meses negativos consecutivos es psicologicamente insostenible para un operador individual.

---

*Generado el 2026-04-06 como cierre formal del research de Chocotrader.*
