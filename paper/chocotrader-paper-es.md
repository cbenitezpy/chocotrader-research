# Sin edge persistente: un estudio pre-registrado y multi-fase de trading algorítmico retail long-only en Binance Spot (2017–2026)

**Autor:** Cristhian Benitez
**Fecha:** Mayo 2026 (rev. con chequeos de robustez)
**Estado:** Preprint / working paper
**Repositorio complementario:** https://github.com/cbenitezpy/chocotrader-research — simuladores, fetchers de datos y logs completos de resultados.

> Traducción al español del paper original en inglés (`chocotrader-paper-en.md`). En caso de discrepancia, la versión en inglés es la de referencia.

---

## Resumen

Reportamos los resultados completos de *Chocotrader*, un programa de investigación autofinanciado y pre-registrado que hizo una sola pregunta: **¿tiene alguna estrategia algorítmica simple y accesible para retail un edge persistente y explotable en Binance Spot, neto de costos realistas, que justifique comprometer capital real?** A lo largo de seis fases de research que abarcaron ~50–80 horas de trabajo y 9.25 años de datos históricos (2017–2026, 66.682 velas de 4 horas en cinco pares), evaluamos trend-following (cruce de EMA, breakout Donchian, SuperTrend), mean-reversion (Bandas de Bollinger), filtrado regime-aware (detectores ADX/ATR), ensembles naive, portfolios multi-par y — en la fase final — fuentes de alpha no-técnicas (el índice Fear & Greed, el funding rate de futuros perpetuos, y el Índice del Dólar como overlay macro).

**La respuesta fue no.** Ninguna estrategia pasó nuestro gate out-of-sample (OOS) pre-registrado. El único ensemble naive que pasó los gates in-sample colapsó a un Sharpe OOS de **+0,041** contra un requerido ≥0,8. La estrategia activa más fuerte de la auditoría de período completo (SuperTrend en BTC) logró un Sharpe ajustado por riesgo de 0,977 — mejor que el 0,809 de Buy-and-Hold (B&H) BTC — pero retornó **7× menos capital absoluto** ($2.190 vs $15.958 sobre una base de $1.000). En el régimen de mercado más reciente y más relevante (2023–2026), **todas** las estrategias que probamos, incluyendo las seis variantes de señales externas, rindieron por debajo de B&H BTC.

La contribución de este paper es doble. Primero, es un **resultado negativo** honesto en un dominio dominado por el sesgo de supervivencia y los fracasos no publicados. Segundo, es una **metodología reproducible** — pre-registro, sellado físico del OOS, validación walk-forward, un modelo de fill realista next-open, y gates constitucionales — que nos impidió desplegar un edge ilusorio. Documentamos un caso donde una señal de mean-reversion aparentemente rentable (Sharpe +0,72 bajo un modelo de fill optimista) **desapareció por completo** (Sharpe −0,56) una vez aplicado un modelo de fill realista. Capital total perdido en todo el programa: **$0**.

Luego sometimos la conclusión a una batería de chequeos de robustez adversariales (Sección 6), probando si el resultado es un artefacto de nuestro modelo de costos, nuestro timeframe de 4h, nuestra fecha de inicio, nuestro universo de large-caps, o nuestra restricción long-only. La conclusión sobrevive a los cinco: costos menores (incluso cero) no rescatan ninguna estrategia con Sharpe negativo; el timeframe diario no le gana al de 4h; el edge activo sobre B&H depende de la fecha de inicio y nunca alcanza el gate; el gate de Sharpe no se cumple en ninguna de las siete altcoins mid-cap sobrevivientes (una cota superior, ya que los pares deslistados están ausentes); y agregar venta en corto vía perpetuos 1x con costo de funding real *empeora* el Sharpe del trend-following en lugar de mejorarlo. Notablemente, el test long/short produjo primero un Sharpe demasiado bueno de 2,7 que rastreamos a un bug de contabilidad — una demostración en vivo de la misma disciplina que el paper defiende.

**Nota de alcance (importante).** Nuestra afirmación es deliberadamente estrecha: *dentro del envelope long-only, spot-only, de costos retail*, ninguna estrategia simple técnica o de sentiment le ganó a Buy-and-Hold BTC out-of-sample. **No** afirmamos que no exista edge en cripto en general; el carry apalancado de perpetuos, el arbitraje cross-exchange, las opciones y los enfoques de ML quedan fuera de este envelope y explícitamente fuera de scope.

**Palabras clave:** trading algorítmico, criptomonedas, backtesting, pre-registro, validación out-of-sample, resultados negativos, reproducibilidad, eficiencia de mercado.

---

## 1. Introducción

### 1.1 Motivación

El interés retail por el trading algorítmico de criptomonedas es enorme, y la narrativa pública es abrumadoramente positiva: las redes sociales están saturadas de capturas de bots rentables y "estrategias que imprimen dinero". Casi nada de esto viene acompañado de metodología pre-registrada, modelado de costos realista, o validación out-of-sample. La tasa base de *fracasos publicados* es cercana a cero, lo cual es en sí mismo evidencia fuerte de un severo sesgo de supervivencia y publicación.

Chocotrader empezó como un intento de construir tal bot para uso personal, con un objetivo deliberadamente modesto: encontrar cualquier estrategia lo suficientemente buena como para justificar arriesgar $100–$500 de capital real en Binance Spot. El proyecto se impuso autogobierno estricto desde el día uno — una "constitución" escrita de principios no negociables, gates de validación secuenciales, y una regla de que *"sin edge"* era un resultado aceptable y respetable. Este paper reporta qué pasó.

### 1.2 Alcance y restricciones

La investigación operó bajo restricciones deliberadas y autoimpuestas que reflejan la situación de un trader retail disciplinado:

- **Solo spot.** Sin futuros, sin margen, sin apalancamiento, sin venta en corto.
- **Solo long.** Consecuencia directa de spot-only.
- **Costos realistas.** 0,10% de fee por lado (0,20% round-trip, sin descuento por token de exchange) más 0,05% de slippage por lado en BTC/ETH — un piso de 0,30% round-trip.
- **Capital bajo.** $100–$1.000, donde el notional mínimo y el arrastre de fees son materiales.
- **Sin machine learning.** Por regla constitucional, para mantener todo resultado interpretable y evitar la superficie de overfitting que el ML introduce.

Estas restricciones importan: son precisamente las condiciones bajo las que opera un participante retail típico, y varias de nuestras conclusiones son *consecuencias* de estas restricciones más que afirmaciones universales.

### 1.3 Contribuciones

1. Un **estudio empírico pre-registrado de seis fases** completo sobre estrategias accesibles para retail, en 9.25 años de datos, con todos los resultados in-sample y out-of-sample reportados — incluyendo los fracasos.
2. Un **framework metodológico** documentado y reutilizable (constitución → pre-registro → sellado OOS → walk-forward → modelo de fill realista → gates) que demostrablemente impidió el despliegue de un edge ilusorio.
3. Una demostración empírica clara de tres trampas recurrentes en el backtesting retail: el **artefacto del modelo de fill**, la **ilusión de overfit de régimen**, y la **paradoja retorno-ajustado-por-riesgo-vs-absoluto** relativa a Buy-and-Hold.
4. Un resultado negativo honesto: bajo las restricciones declaradas, **no encontramos edge persistente y explotable** — y argumentamos que para capital bajo, el dollar-cost averaging (DCA) en BTC domina a un bot activo en toda dimensión que importa.

### 1.4 Lo que este paper no es

No es una afirmación de que *no* existe edge algorítmico en mercados cripto. Plausiblemente existen edges en regímenes que excluimos deliberadamente — carry/basis trading de futuros perpetuos, arbitraje cross-exchange, market making, y enfoques de machine learning con datos y latencia fuera del alcance de un participante retail. Nuestra afirmación es más estrecha y, creemos, más útil: **dentro del envelope de spot-only, long-only y costos retail, las estrategias simples técnicas y basadas en sentiment no le ganan a Buy-and-Hold BTC out-of-sample.**

---

## 2. Metodología y Framework

El framework metodológico es, a nuestro juicio, la contribución más transferible de este trabajo. Cada componente existe para defenderse de un modo de fallo específico y bien documentado del backtesting.

### 2.1 Constitución y gates secuenciales

Antes de escribir código, redactamos un `constitution.md` de principios no negociables, siendo los más importantes *preservación de capital sobre retorno* y *"ningún trade es mejor que un mal trade"*. Definió tres **gates secuenciales**, cada uno de los cuales debía pasarse antes del siguiente:

1. **Gate de backtest:** Sharpe ≥ 1,2 (train+validation), Sharpe ≥ 0,8 (out-of-sample), MaxDD ≤ 30%.
2. **Gate de testnet:** validación operativa solamente (uptime, reconciliación, idempotencia) — explícitamente *no* una prueba de rentabilidad.
3. **Gate de mainnet:** capital real pequeño, escalado solo tras desempeño sostenido.

Crucialmente, los gates se escribieron *antes* de que existieran resultados, así que no podían relajarse silenciosamente cuando una estrategia "casi" pasaba.

### 2.2 Pre-registro

Tras la Fase 1 (v1), adoptamos el **pre-registro**: cada hipótesis, parámetro, split de datos y umbral de aceptación se committeaba al control de versiones *antes* de mirar los datos. Esto ataca directamente el problema de multiple-testing / data-snooping. El contraste fue marcado: v1 corrió 20+ experimentos sin pre-registro en 14 días; v2 corrió un conjunto pre-registrado de ~6 experimentos en aproximadamente un día y llegó a una conclusión igualmente válida con mucho menos riesgo de data-snooping.

### 2.3 Sellado out-of-sample

Un dataset OOS dedicado fue reservado y **sellado físicamente** (`chmod 0444`, acceso logueado con timestamp y razón). Se accedió exactamente una vez, al final de una fase, para confirmar o refutar el hallazgo in-sample — nunca para iterar. Cuando el dataset OOS de v1 (2024–2025) se consumió, se trató como *quemado* y nunca se reutilizó, precisamente porque reutilizarlo constituiría data-snooping retroactivo. En la fase final (v6), el gate nunca se pasó, así que el dataset OOS **nunca se accedió** y permanece limpio.

### 2.4 Validación walk-forward

Dividimos el registro histórico en ventanas secuenciales (W1, W2, W3) y medimos el comportamiento de cada estrategia a lo largo de ellas. La ventana más reciente (W3) sirvió como *predictor* del desempeño out-of-sample. Esto resultó notablemente preciso: en v1, la predicción walk-forward de W3 coincidió con el Sharpe OOS realizado dentro de ±0,03 para los componentes individuales (Tabla 3). El walk-forward funcionó así como un sistema de alerta temprana — pudimos anticipar el fracaso OOS *sin quemar el set OOS*.

### 2.5 El modelo de fill

La elección metodológica más consecuente fue el **modelo de fill**. Usamos `next_open`: una señal calculada al cierre de la vela *t* se ejecuta en la apertura de la vela *t+1*. La alternativa naive — ejecutar al cierre de la vela de señal (`same_close`) — le otorga silenciosamente al backtest información que no podría haber tenido en tiempo real.

Para trend-following esta distinción es despreciable (|ΔSharpe| < 0,01, porque un retraso de una vela es ruido frente a una tendencia de varias semanas). Para mean-reversion es **catastrófica**, porque todo el edge depende de capturar un rebote inmediato desde un extremo. Lo documentamos en detalle en la Sección 4.2.

### 2.6 Modelo de costos

Todos los backtests aplican 0,10% de fee por lado (0,20% round-trip, sin descuento BNB) y 0,05% de slippage por lado en BTC/ETH (0,10% en alts menos líquidas), para un piso de 0,30% round-trip. Verificamos que los fees *no* son la restricción vinculante: a lo largo de las estrategias, los fees totales representaron solo 4–10% del PnL bruto. Cuando el Sharpe de una estrategia era pobre, la causa era ruido de señal, no costo.

### 2.7 El benchmark: Buy-and-Hold BTC

Cada resultado se reporta contra **Buy-and-Hold BTC** como primera fila de cada tabla. Esta fue una lección aprendida a la fuerza — v1 no comparó sistemáticamente contra B&H hasta tarde, lo que infló las expectativas tempranas. En 2017–2026, B&H BTC entregó un Sharpe de 0,809 con un retorno de +1.495,8% (y un brutal max drawdown de −83,9%). Esta es una barra extraordinariamente alta: cualquier estrategia activa que afirme "ganarle al mercado" debe superar un Sharpe sostenido por encima de 0,81 — muy difícil para spot retail long-only con costos de 0,30% round-trip.

### 2.8 Datos

Ensamblamos 66.682 velas de 4 horas cubriendo 2017-08 a 2026-05, continuas y sin gaps, para cinco pares USDT (BTC, ETH, SOL, BNB, XRP), almacenadas como Parquet. También se retuvo resolución diaria para análisis de horizonte más largo. Para la fase final agregamos tres series externas: el índice Fear & Greed (3.027 observaciones diarias desde 2018-02 vía alternative.me), el funding rate de futuros perpetuos (7.333 observaciones de 8 horas para BTC desde 2019-09 vía Binance), y el Índice del Dólar (DTWEXBGS, 5.107 observaciones diarias vía FRED).

---

## 3. Diseño Experimental

El programa corrió en seis fases. Cada fase fue un intento autocontenido de encontrar edge, informado por los fracasos de la anterior.

| Fase | Foco | Resultado principal |
|---|---|---|
| **v1** | Trend-following + ensemble naive (20+ experimentos, 14 días) | Mejor ensemble: Sharpe OOS **+0,041** (gate ≥0,8). FAIL. |
| **v2** | Filtrado regime-aware (detector ADX/ATR) | Anti-edge en cada variante. ABORT. |
| **v3** | Mean-reversion Bollinger, puro (fill realista) | Sharpe train+val **−0,56** (gate ≥0,5). FAIL. |
| **Auditoría** | Barrido período completo: 144 combinaciones, 9.25 años | Ningún escenario conservador alcanza Sharpe ≥ 1,2. |
| **v5** | Portfolio SuperTrend multi-par | Sharpe in-sample mejora; OOS regime-dependent. |
| **v6** | Alpha externa (F&G, funding, DXY), pre-registrado | Ninguna estrategia pasa walk-forward W3. CIERRE. |

### 3.1 Fase v1 — Trend-following y ensembles naive

Probamos cruce de EMA (múltiples períodos), breakout Donchian, SuperTrend, y variantes con filtro SMA, en BTC y ETH a 4h. Las mejores estrategias individuales superaron un Sharpe cercano a 1,0 in-sample pero estaban cargadas casi enteramente por BTC; ETH sangraba consistentemente. Ninguna variante pura de trend-following pasó el gate in-sample sola. Un ensemble naive 60/40 de un componente trend y un componente Bollinger mean-reversion *sí* pasó el gate in-sample (Sharpe 1,48) y pasó una auditoría formal pre-OOS — y luego falló OOS.

### 3.2 Fase v2 — Filtrado regime-aware

La hipótesis: clasificar el mercado en regímenes (trending / ranging) usando un detector ADX/ATR/ancho-de-Bollinger, y luego operar cada estrategia solo en su régimen favorable. El detector clasificó regímenes razonablemente en retrospectiva (~40% de coherencia con etiquetas manuales) pero fue **inútil como filtro de trades en tiempo real**, por una razón estructural elaborada en la Sección 5.3. Tanto la variante trend (E1) como la de mean-reversion (E3) mostraron anti-edge y fueron abortadas.

### 3.3 Fase v3 — Mean-reversion Bollinger bajo fill realista

El componente de mean-reversion que sobrevivió el walk-forward de v1 fue re-testeado en aislamiento bajo el modelo de fill `next_open`. Falló catastróficamente (Sección 4.2). Este fue el resultado individual más importante de todo el programa.

### 3.4 Auditoría de período completo — 144 combinaciones

Para eliminar cualquier duda de que se estuviera perdiendo una elección de parámetros afortunada, corrimos un barrido exhaustivo: 8 configuraciones de estrategia × 2 pares activos × 4 escenarios de capital × 3 perfiles de riesgo sobre el registro completo de 9.25 años, todo bajo `next_open`. Esta es la referencia canónica (Sección 4.1).

### 3.5 Fase v5 — Portfolios multi-par

SuperTrend fue evaluado en cinco pares y como portfolios de 2 a 5 pares. El Sharpe del portfolio mejoró con la diversificación *in-sample* (el portfolio de 5 alcanzó Sharpe 2,10 con baja correlación cross-par), pero el walk-forward y el veredicto OOS previo sobre el componente trend (−0,55) mostraron que esta mejora in-sample no se trasladó hacia adelante.

### 3.6 Fase v6 — Fuentes de alpha externas (no-técnicas)

La fase final preguntó si información *exógena* al propio precio del par operado podía agregar edge. Tres hipótesis, cada una en dos formas (un **filtro** sobre SuperTrend y una señal **standalone**), pre-registradas antes de examinar dato alguno:

- **H1 — Fear & Greed:** miedo extremo (índice ≤ 25) como señal de compra contrarian.
- **H3 — Funding rate:** funding perpetuo extremo como proxy de sentiment para spot.
- **H5 — Overlay DXY:** suprimir entradas long mientras el dólar está en uptrend.

(Una cuarta hipótesis, dominancia de BTC, fue descartada en pre-registro por riesgo de look-ahead; una quinta, net-flows de exchanges, fue excluida por requerir datos premium.)

---

## 4. Resultados

### 4.1 La tabla canónica: auditoría de período completo (2017–2026, $1.000 compuesto, perfil conservador)

| Estrategia | Equity final | Retorno | Sharpe | MaxDD | Trades | Win rate | PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Buy & Hold BTC** | **$15.958** | **+1.495,8%** | **0,809** | −83,9% | 1 | 100% | ∞ |
| Buy & Hold ETH | $6.942 | +594,2% | 0,694 | −94,1% | 1 | 100% | ∞ |
| DCA mensual BTC | $4.867 | +386,7% | 0,650 | −69,5% | — | — | — |
| SuperTrend(10,3) BTC | $2.190 | +119,0% | 0,977 | −13,7% | 225 | 37,8% | 1,59 |
| SuperTrend(10,3) ETH | $2.372 | +137,2% | 0,840 | −17,6% | 222 | 37,4% | 1,51 |
| EMA(12/26) BTC | $2.203 | +120,3% | 0,903 | −21,6% | 315 | 27,9% | 1,47 |
| EMA(12/26) ETH | $1.914 | +91,4% | 0,635 | −18,4% | 336 | 26,2% | 1,29 |
| Donchian(20/10) BTC | $1.746 | +74,6% | 0,780 | −19,0% | 249 | 38,6% | 1,44 |
| Donchian(20/10) ETH | $1.750 | +75,0% | 0,592 | −20,2% | 265 | 31,7% | 1,30 |
| BB(20,2.75) BTC | $836 | −16,4% | −0,358 | −20,6% | 145 | 58,6% | 0,70 |
| BB(20,2.75) ETH | $796 | −20,4% | −0,529 | −24,0% | 20 | 35,0% | 0,20 |

**Hallazgos.** B&H BTC retorna 16× sobre $1.000; ninguna estrategia activa supera ~2,4×. El mejor *Sharpe* activo en cualquier escenario fue EMA BTC en perfil agresivo (1,045), pero eso requería 40% de equity por posición y fees optimistas de 7,5 bps; **ninguna estrategia de perfil conservador alcanzó Sharpe 1,0, y ninguna alcanzó el gate constitucional de 1,2.** El mean-reversion Bollinger perdió dinero sistemáticamente; su variante ETH habría sido liquidada por la regla de equity mínimo en 12 de 12 escenarios.

### 4.2 El artefacto del modelo de fill (el resultado individual más importante)

La señal de mean-reversion de Bandas de Bollinger, BB(20, 2.75), parecía ser la única idea genuinamente rentable surgida de v1:

| Modelo de fill | Sharpe OOS | Interpretación |
|---|---:|---|
| `same_close` (optimista) | **+0,72** | Parece un edge desplegable |
| `next_open` (realista) | **−0,56** | Sin edge; pierde dinero |
| **Delta** | **−1,28** | El "edge" era un artefacto |

Todo el edge aparente del mean-reversion dependía de ejecutar al cierre de la *misma* vela que generó la señal — capturando un rebote que, con un retraso realista de una vela (4h), ya ocurrió parcialmente. **Si hubiéramos desplegado sobre el backtest optimista, habríamos comprometido capital real en una estrategia sin edge.** Esta única verificación es la justificación más clara de todo el aparato metodológico.

### 4.3 El walk-forward predijo el out-of-sample con alta fidelidad

| Componente | W3 walk-forward (predicho) | OOS (realizado) | Error |
|---|---:|---:|---:|
| Solo trend | −0,54 | −0,55 | 0,01 |
| Solo mean-reversion | +0,70 | +0,72 | 0,02 |
| Ensemble 60/40 | −0,22 | +0,04 | 0,26 |

Para los componentes individuales, el walk-forward predijo el Sharpe OOS realizado dentro de ±0,03. Esto valida al walk-forward como un instrumento genuino de captura de régimen, no ruido — y nos permitió anticipar el fracaso sin consumir el set OOS.

### 4.4 El ensemble de v1: lo más cerca que llegamos, y por qué falló

El ensemble 60/40 pasó cada gate in-sample (Sharpe 1,48 train+val, MaxDD −14,1%, 223 trades, auditoría formal aprobada). Su Sharpe OOS fue **+0,041** ($100 → $99,81, breakeven). Descompuesto: el componente trend retornó −0,55 (perdió dinero en el régimen de consolidación post-rally), el componente mean-reversion retornó +0,72 (real pero por debajo del gate de 0,8), y el peso del 60% sobre el componente trend fallido arrastró al ensemble al breakeven. **Combinar una estrategia que tiene edge negativo en el régimen de evaluación no produce diversificación — produce dilución.**

### 4.5 Fase v6: las señales externas no agregan nada out-of-sample

In-sample (train+val 2018–2026), medido como Sharpe delta versus B&H BTC:

| Experimento | Sharpe | Δ vs B&H | MaxDD | Trades | Veredicto |
|---|---:|---:|---:|---:|---|
| SuperTrend baseline (referencia) | +0,972 | +0,282 | −25,6% | 213 | Pasa gate train, *no es hipótesis de v6* |
| H3 funding (filtro) | +0,724 | +0,034 | −23,8% | 167 | FAIL |
| H3 funding (standalone) | +0,723 | +0,033 | −30,8% | 6 | FAIL (muestra ínfima) |
| H5 DXY (filtro) | +0,441 | −0,250 | −31,7% | 122 | FAIL |
| H5 DXY (standalone) | +0,207 | −0,483 | −41,4% | 144 | FAIL |
| H1 Fear&Greed (standalone) | +0,048 | −0,642 | −37,7% | 8 | FAIL |
| H1 Fear&Greed (filtro) | −0,215 | −0,905 | −30,2% | 65 | FAIL (peor que B&H) |

Walk-forward (Sharpe delta vs B&H BTC por ventana):

| Estrategia | Δ W1 (2018–20) | Δ W2 (2020–23) | Δ W3 (2023–26) | ¿Pasa W3 (≥+0,15)? |
|---|---:|---:|---:|:---:|
| H5 DXY (filtro) | +0,633 | +0,047 | −1,198 | No |
| H3 funding (standalone) | +0,572 | −0,476 | −0,877 | No |
| SuperTrend baseline | +0,500 | +0,555 | −0,457 | No |
| H3 funding (filtro) | −0,123 | +0,296 | −0,353 | No |
| H1 F&G (standalone) | −0,400 | −1,043 | −0,742 | No |
| H5 DXY (standalone) | −0,305 | −0,706 | −0,720 | No |
| H1 F&G (filtro) | −0,119 | −1,396 | −1,625 | No |

**Ninguna estrategia pasó el gate W3.** Según el pre-registro, el set OOS por lo tanto nunca se accedió. El patrón es diagnóstico: varias estrategias muestran delta positivo en W1/W2 (regímenes alcistas) y colapsan en W3 (la consolidación 2023–2026) — la firma de manual del overfit de régimen en lugar de edge persistente.

Notablemente, la hipótesis de "comprar miedo" (H1) fue la **peor** de todas: comprar con Fear & Greed ≤ 25 en un horizonte de 1–4 semanas repetidamente significaba comprar en bear markets con más caída por delante. La intuición retail popular no es meramente débil aquí — es *anti-predictiva*.

---

## 5. Discusión: Qué Aprendimos

### 5.1 Validar el modelo de fill antes que cualquier otra cosa

La lección más cara, aprendida a mitad del programa, fue que un edge aparente puede ser enteramente un artefacto de un supuesto de ejecución optimista. El Sharpe del mean-reversion cayó 1,28 (de +0,72 a −0,56) al pasar de `same_close` a `next_open`. El corolario es una regla que ahora aplicamos universalmente: **un motor de backtest debe usar `next_open` por defecto; `same_close` debe requerir justificación explícita.** Validar el modelo de fill primero habría ahorrado aproximadamente dos semanas de trabajo gastadas optimizando una señal que el modelo de fill realista invalidó inmediatamente.

### 5.2 Buy-and-Hold BTC es una barra extraordinariamente alta

La apreciación secular de BTC (Sharpe 0,81 en nueve años) fija un benchmark que las estrategias retail long-only luchan por superar. Las estrategias activas que probamos eran *mejores gestoras de riesgo* (SuperTrend BTC: MaxDD −13,7% vs −83,9% de B&H) pero *muy peores generadoras de retorno* (7× menos retorno absoluto). Esta es la **paradoja ajustado-por-riesgo-vs-absoluto**: para un participante con $100, un drawdown de −84% es psicológicamente aterrador pero financieramente trivial ($84), mientras que la diferencia de retorno ($1.497 vs $366) es lo que realmente importa. Para capital bajo, el bot activo pierde en la dimensión que cuenta.

### 5.3 Los indicadores lagging clasifican régimen pero no pueden filtrar trades

ADX es, por construcción de Wilder, un indicador lagging (~28 velas de warm-up). Puede etiquetar un régimen en retrospectiva pero no puede filtrar trades en tiempo real sin daño de timing: para trend-following, cuando ADX confirma una tendencia el movimiento ya fue capturado por indicadores más rápidos (la entrada es tardía y devuelve ganancias); para mean-reversion, los bordes de transición de régimen forzaron salidas prematuras (58,9% de los trades cerraron por un flag de régimen y no por señal de estrategia). **La clasificación correcta no implica filtrado rentable.**

### 5.4 El mean-reversion long-only tiene un sesgo negativo estructural en cripto

Comprar la banda inferior de Bollinger en una cuenta spot long-only es "atrapar un cuchillo que cae" durante bear markets. Sin venta en corto (una exclusión constitucional), el mean-reversion es estructuralmente asimétrico: gana poco en mercados laterales y pierde mucho en downtrends. BB-ETH habría sido liquidada en 12 de 12 escenarios de auditoría.

### 5.5 Edge concentrado en un solo régimen no es edge

Repetidamente, estrategias con Sharpe agregado atractivo debían ese desempeño a una sola ventana alcista. La insignia E3b-5p de v1 mostró W1 +1,62 / W2 +3,72 / **W3 −0,52**; el filtro DXY de v6 mostró W1 +0,633 / W2 +0,047 / **W3 −1,198**. Las métricas agregadas *ocultan* la concentración de régimen. El walk-forward la expone. Una estrategia que solo funciona en bull markets es una apuesta apalancada al régimen, no un edge.

### 5.6 La disciplina de tamaño de muestra importa

Varias variantes de aspecto atractivo descansaban en muy pocos trades (p.ej., una variante EMA 50/200 4h con Sharpe 1,00 sobre solo 21 trades; el funding-standalone de v6 con 6 trades en ocho años, y **cero** trades en la ventana W3). Una estrategia que "no falla" porque rara vez opera no provee evidencia. Mantuvimos un piso de ≥50 trades para relevancia estadística y rehusamos promover cualquier cosa por debajo.

### 5.7 Spot-only, long-only es un handicap estructural para el retorno activo

La meta-lección más clara: si el objetivo es *retorno activo*, la restricción spot-only long-only es un handicap estructural, porque elimina las herramientas (shorting, apalancamiento, carry de derivados) que hacen funcionar muchos edges documentados de cripto. Si el objetivo es *preservación de capital*, entonces B&H más DCA es más simple y más efectivo que cualquier bot que construimos. Para nuestro objetivo real — retorno modesto sobre capital bajo — el DCA en BTC dominó toda estrategia activa en costo, simplicidad, riesgo operacional, y (para $100) retorno efectivo.

### 5.8 La metodología se pagó sola

A lo largo de seis fases perdimos **$0** de capital. El valor del framework se concentra en momentos de rechazo: rehusar desplegar el artefacto del modelo de fill, rehusar relajar un gate cuando una estrategia "casi" pasaba, rehusar reutilizar un OOS quemado, rehusar acceder al set OOS de v6 tras fallar el gate walk-forward. Un proceso de research honesto que concluye "sin edge" vale más que un backtest sobreajustado que afirma "Sharpe 2,0" y pierde dinero en vivo. Pagar esa lección en tiempo de backtest en lugar de capital real es el punto entero.

---

## 6. Chequeos de Robustez (Respuesta a Críticas de Red-Team)

Un reviewer escéptico puede argumentar que el resultado negativo es un artefacto de nuestras elecciones de diseño y no una propiedad del mercado. Tomamos cinco de esas críticas en serio y probamos cada una directamente. Todos los experimentos usan base $1.000 y el modelo de fill realista `next_open`; el código está en `src/robustness/`.

### 6.1 ¿Es el modelo de costos? (No.)

Crítica: 0,30% round-trip es pesimista; los descuentos BNB y fills maker-only rescatarían estrategias marginales. Re-corrimos las estrategias clave bajo tres regímenes de costo — baseline (0,30%), BNB-reducido (0,25%), y una cota superior irreal de costo cero.

| Estrategia | Δ Sharpe vs B&H @ 0,30% | @ 0,25% | @ 0% (cota superior) |
|---|---:|---:|---:|
| SuperTrend baseline | +0,282 | +0,311 | +0,457 |
| h3 funding (filtro) | +0,034 | +0,064 | +0,213 |
| h3 funding (standalone) | +0,033 | +0,034 | +0,040 |
| h5 DXY (filtro) | −0,250 | −0,226 | −0,109 |
| h1 Fear&Greed (filtro) | −0,905 | −0,889 | −0,807 |

Ninguna estrategia con Sharpe negativo cruza a edge positivo ni siquiera a **costo cero**. El funding-filter sube hacia el gate in-sample a costo cero pero igual falla walk-forward W3 (su test decisivo). Conclusión: la restricción vinculante es **la calidad de la señal, no el costo de transacción**. El punto del reviewer aplica solo a estrategias de alta frecuencia que no perseguimos — e incluso ahí, un backtest maker-only sin modelar incertidumbre de fill (Sección 4.5) sería en sí mismo un nuevo artefacto de fill.

### 6.2 ¿Es el timeframe de 4h? (No.)

Crítica: 4h es "tierra de nadie" — demasiado lento para microestructura, demasiado rápido para macro-trend. Resampleamos a diario y re-corrimos SuperTrend.

| Variante | Sharpe | Δ vs B&H | MaxDD | Final ($1k) | Trades |
|---|---:|---:|---:|---:|---:|
| B&H BTC | +0,690 | — | −77,0% | $6.734 | 1 |
| SuperTrend 4h | +0,972 | +0,282 | −25,6% | $3.663 | 213 |
| SuperTrend 1d | +0,911 | +0,221 | −25,4% | $4.130 | 39 |

El diario no le gana al 4h en Sharpe, y ninguno alcanza el gate de 1,2. (El diario es más eficiente en capital — menos trades, Sharpe similar — pero eso no cambia el veredicto.) El régimen de microestructura sub-minuto que el reviewer menciona es el dominio del HFT, donde un participante retail no compite; perseguirlo contradiría su propia crítica 6.4.

### 6.3 ¿Es la fecha de inicio? (En parte — y va en contra del reviewer.)

Crítica: el inicio en 2017 de B&H captura la beta de adopción institucional de BTC; empezar en un año bear-pesado haría que las activas se vieran geniales. Corrimos B&H y SuperTrend desde cinco fechas de inicio.

| Inicio | B&H Sharpe | B&H MaxDD | SuperTrend Sharpe | ST MaxDD | Δ Sharpe |
|---|---:|---:|---:|---:|---:|
| 2017-08 | +0,809 | −83,9% | +0,980 | −25,6% | +0,170 |
| 2018-01 | +0,632 | −81,4% | +0,893 | −25,6% | +0,261 |
| 2020-01 | +0,901 | −77,0% | +0,999 | −25,6% | +0,098 |
| 2021-11 | +0,320 | −77,0% | +0,274 | −23,8% | **−0,046** |
| 2022-01 | +0,435 | −67,2% | +0,323 | −20,9% | **−0,112** |

La predicción del reviewer es **empíricamente incorrecta** en base ajustada por riesgo: empezando desde el techo de 2021 o desde 2022, SuperTrend *rinde por debajo* de B&H en Sharpe, porque un trend-follower long-only se pierde la recuperación que no puede anticipar. Las estrategias activas ganan consistentemente solo en **drawdown** (prom. −24% vs −77%), nunca lo suficiente para alcanzar el gate de 1,2 en ninguna ventana. El benchmark es sensible a la fecha de inicio, pero no en la dirección que la crítica asumió.

### 6.4 ¿Es el universo de large-caps? (No — el survivorship lo hace el test más fuerte.)

Crítica: el edge vive en altcoins mid-cap ineficientes, no en los majors hiper-arbitrados. Corrimos SuperTrend en siete mid-caps líquidas (ADA, AVAX, LINK, DOT, ATOM, LTC, DOGE), con slippage ampliado (0,10%/lado) por libros más finos.

| Par | B&H Sharpe | SuperTrend Sharpe | ST MaxDD | Δ vs B&H | Gate (≥1,2) |
|---|---:|---:|---:|---:|:---:|
| ADA | +0,491 | +0,554 | −45,9% | +0,064 | fail |
| AVAX | +0,684 | +0,960 | −41,2% | +0,276 | fail |
| LINK | +0,912 | +0,683 | −50,4% | −0,230 | fail |
| DOT | +0,356 | +0,187 | −59,1% | −0,170 | fail |
| ATOM | +0,454 | +0,291 | −57,1% | −0,163 | fail |
| LTC | +0,265 | +0,266 | −45,4% | +0,001 | fail |
| DOGE | +0,959 | +0,726 | −61,1% | −0,233 | fail |

SuperTrend alcanza el gate de 1,2 en **0 de 7** pares (Sharpe medio +0,524, peor que los majors). Crucialmente, esto es una **cota superior sesgada por supervivencia**: cada par aquí sigue listado en 2026; las cientos de mid-caps deslistadas/muertas están ausentes (la API pública de Binance no las sirve). Dado que incluso el mejor caso (universo de sobrevivientes) falla el gate, la conclusión es *robusta* — un universo sin sesgo solo bajaría estos números. Un resultado positivo aquí habría exigido un universo point-in-time con pares deslistados; uno negativo no.

### 6.5 ¿Es la restricción long-only? (No — y fue la crítica más afilada.)

Crítica: prohibir la venta en corto en un mercado con bear markets del 80% es atarse una mano a la espalda; el retail moderno usa futuros perpetuos. Construimos un engine long/short de perpetuo 1x cobrando el **funding rate histórico real de 8h**, y corrimos SuperTrend (sus señales SELL ahora abren shorts) en la ventana con funding disponible (2019-09 en adelante).

| Estrategia | Sharpe | Δ vs B&H | MaxDD | Final ($1k) |
|---|---:|---:|---:|---:|
| B&H BTC | +0,784 | — | −77,0% | $6.722 |
| SuperTrend long-only (spot) | +0,908 | +0,125 | −25,6% | $2.545 |
| SuperTrend long/short (perp 1x) | +0,524 | −0,259 | −23,6% | $1.876 |

Agregar la capacidad de shortear **baja** el Sharpe de SuperTrend (0,908 → 0,524 en BTC; 0,957 → 0,535 en ETH). Dos fuerzas lo explican: el lado short de una señal de trend-following pierde dinero en un bull secular (shortea caídas que se recuperan), y el costo de funding (los longs pagaron ≈+11,9% anualizado en la muestra) es un drag persistente. La restricción long-only **no** era la limitación vinculante para esta familia de estrategias.

*Nota metodológica:* este experimento reportó primero un Sharpe de **2,7** — físicamente inconsistente con un drawdown de −66% y una equity final *por debajo* de la variante long-only. Tratamos el número demasiado-bueno como un bug (según nuestra propia regla de red-flags), encontramos un error de doble-conteo en el mark-to-market del perpetuo, lo arreglamos, y re-corrimos. El resultado corregido es el de arriba. Esta es la disciplina de la Sección 5.1 operando en tiempo real.

### 6.6 Qué establecen y qué no los chequeos de robustez

Establecen que el resultado negativo **no** es un artefacto de costo, timeframe, fecha de inicio, universo de activos, o direccionalidad, para las *familias de estrategias probadas*. **No** establecen que ninguna estrategia long/short pueda funcionar — solo que shortear mecánicamente una señal trend long-only no lo hace. Tampoco cubren carry apalancado, opciones, o ML. El envelope es más amplio tras la Sección 6, pero sigue siendo un envelope.

---

## 7. Amenazas a la Validez

Nos sometemos al mismo escrutinio que aplicamos a las estrategias.

- **Generalidad de un solo mercado.** Nuestras conclusiones son específicas de Binance Spot, long-only, costos retail, 2017–2026. No generalizan a futuros, otros venues, u horizontes más cortos.
- **Cobertura del espacio de estrategias.** Probamos un conjunto finito (aunque amplio) de señales clásicas más tres fuentes externas. La ausencia de edge en este conjunto no prueba su ausencia en todos lados; restringe dónde uno debería buscar (Sección 7).
- **Cobertura del espacio de parámetros.** Aunque corrimos un barrido de 144 combinaciones y chequeos de sensibilidad ±20%, el espacio de parámetros es efectivamente infinito. Lo mitigamos con pre-registro (limitando el fishing post-hoc) pero no podemos eliminarlo.
- **Sesgo de supervivencia en los datos.** Nuestros cinco pares son sobrevivientes. Incluir pares deslistados/muertos, en todo caso, *debilitaría* los resultados de las estrategias activas, no los fortalecería, así que este sesgo es conservador respecto de nuestra conclusión negativa.
- **Multiple testing en v1.** Los 20+ experimentos no registrados de v1 inflan el riesgo de falsos positivos; esto es exactamente por qué el ganador eventual falló OOS, y exactamente por qué adoptamos el pre-registro de ahí en más.
- **Supuestos de lag de señales externas (v6).** Modelamos lags de publicación conservadores (p.ej., 4h para F&G, 2 días para DXY). Lags más agresivos (menos realistas) *mejorarían* los resultados del backtest, así que nuestros supuestos son conservadores.
- **Muestra de regímenes.** El registro 2017–2026 contiene solo un puñado de ciclos completos bull/bear. El riesgo de régimen out-of-sample permanece, por definición, incuantificable hasta que llega.

---

## 8. Conclusión y Direcciones Futuras

Bajo un envelope spot-only, long-only, de costos realistas y capital retail, y a través de seis fases pre-registradas sobre 9.25 años de datos, **no encontramos ninguna estrategia algorítmica simple con un edge persistente y explotable que le gane a Buy-and-Hold BTC out-of-sample.** El único edge aparente se disolvió bajo un modelo de fill realista; el único ganador in-sample del ensemble colapsó out-of-sample; y una batería final de señales no-técnicas (sentiment, funding, macro) falló la validación walk-forward por completo.

Para el objetivo declarado — hacer crecer capital modesto — la evidencia apunta al **dollar-cost averaging en BTC** como la opción dominante: retorno efectivo comparable o mejor con capital bajo, sin nada del riesgo operacional, costo de infraestructura, o carga conductual de un bot activo.

Esto no es un consejo de desesperanza. Delimita dónde el edge *no* está e, implícitamente, dónde podría estar. Direcciones plausibles, cada una requiriendo un envelope de restricciones diferente y su propio estudio pre-registrado, incluyen: **carry de funding/basis de futuros perpetuos** (que tiene drivers estructurales documentados — nótese que el funding perpetuo de BTC promedió +11,86% anualizado en nuestra muestra, una asimetría real y persistente); **arbitraje cross-exchange o triangular**; **estrategias de volatilidad vía opciones**; y **enfoques de machine learning** con datos y latencia fuera del alcance de un participante retail típico. Cada una de estas viola una o más de nuestras restricciones autoimpuestas y constituiría un *proyecto diferente*, no una continuación de este.

El producto más duradero de Chocotrader no es una estrategia — es un **método**. Pre-registro, sellado OOS, walk-forward como sistema de alerta temprana, un modelo de fill realista por defecto, y gates escritos antes de que existieran los resultados, juntos previnieron el error más caro del trading retail: desplegar capital real sobre un edge ilusorio. Recomendamos este framework, más que cualquier resultado individual, a otros.

---

## 9. Reproducibilidad y Artefactos

En el espíritu del resultado, pretendemos publicar el aparato completo para que otros puedan reproducir, criticar y extender:

- **Fetchers de datos** para todas las series externas (Fear & Greed, funding rate de Binance, DXY de FRED), produciendo los datasets Parquet exactos usados aquí.
- **Generadores de señales** como funciones puras, unit-testeadas, incluyendo la capa de alineación que mergea series externas diarias/8h en velas de 4h *sin look-ahead* (una fuente común y silenciosa de leakage).
- **Motor de backtest** con el modelo de fill `next_open`, modelo de costos explícito, y métricas estandarizadas (Sharpe, Sortino, MaxDD, profit factor, Calmar).
- **Runner de walk-forward** con enforcement automático de gates.
- **Logs completos de resultados** (`run_log.jsonl`), reportes por experimento, y los documentos de pre-registro sellados con sus hashes de commit.
- **Artefactos de gobernanza**: la constitución, los architecture-decision records (ADRs), y las plantillas de pre-registro.

Todos los backtests de este paper son reproducibles desde el código committeado y los datasets regenerables. El dataset out-of-sample reservado para la fase final permanece sellado y sin usar.

---

## Agradecimientos

Este fue un programa de research autofinanciado y de autor único. No hubo capital externo en riesgo en ningún momento. El autor agradece a la disciplina de escribir las cosas antes de mirar los datos — es la única razón por la que se puede confiar en las conclusiones.

## Disponibilidad de Datos y Código

Se planea un repositorio público conteniendo los simuladores, fetchers de datos, datasets generados, y logs de resultados como complemento de este paper. Hasta entonces, todos los resultados numéricos están documentados en los reportes internos de research del proyecto, de los cuales se extrae cada tabla anterior.

## Nota sobre la Interpretación

Ninguna tabla de este paper debe leerse como consejo financiero. El desempeño pasado — incluyendo las cifras de Buy-and-Hold — no predice retornos futuros; la apreciación de BTC en 2017–2026 puede no repetirse. El mensaje central es metodológico: **testear honestamente, comparar despiadadamente, y tratar al "sin edge" como un resultado válido y valioso.**