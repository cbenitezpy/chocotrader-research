# Research v6 — Alignment spec entre OHLCV 4h y datasets externos

**Status:** PARTE DEL PRE-REGISTRO. Modificaciones requieren ADR enmienda.
**Fecha:** 2026-05-20

---

## 1. Propósito

Definir EXACTAMENTE cómo se merge cada vela OHLCV de 4h con las observaciones externas (F&G diario, funding 8h, DXY diario) sin introducir look-ahead. Este documento es el contrato que el código de Fase 2 (signal generators) debe respetar.

---

## 2. Definiciones

- **Vela OHLCV 4h**: timestamps `00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC`. La vela con timestamp `T` cubre `[T, T+4h)`. El precio `close` es el último observado dentro de ese intervalo.
- **Signal-at-close**: la señal se calcula con info disponible al cerrar la vela `T`. La orden se ejecuta al `open` de la vela `T+4h` (consistente con `fill_mode = next_open` del backtest).
- **Forward-fill explícito**: usar el último valor publicado ESTRICTAMENTE antes del cierre de la vela 4h. Nunca leer un valor publicado AL MISMO TIMESTAMP o después.

---

## 3. Por fuente externa

### 3.1 F&G (alternative.me)

- **Frecuencia**: 1 valor diario, timestamp = `00:00:00 UTC` del día.
- **Publicación real**: el valor `T` está disponible aproximadamente `T + few hours` (no instantáneo). Para conservatismo, asumimos disponibilidad al cerrar la vela 4h `T + 04:00 UTC` (es decir, **lag mínimo 4h**).
- **Regla de alineación**:
  ```python
  # Para señal en vela 4h con timestamp T:
  fng_value = fng_daily.loc[fng_daily.date < T_close_dt].iloc[-1].value
  ```
  Donde `T_close_dt` es el momento en que cierra la vela (= T+4h).
- **Esto evita el caso ambiguo**: el valor F&G del día `D` calculado a `D+00:00` NO debe entrar en una señal con vela `D+00:00` (mismo timestamp), porque la API publica con delay.
- **2 gap days documentados**: si el día previo no tiene valor, usar el más reciente disponible (forward-fill manual).

### 3.2 Funding rate (Binance perp)

- **Frecuencia**: 1 valor cada 8h, en `00:00, 08:00, 16:00 UTC`.
- **Publicación real**: la tasa para el período `[T, T+8h]` se settle al inicio del período (timestamp `T`). Disponible inmediatamente al timestamp.
- **Regla de alineación para H3**:
  ```python
  # Para señal en vela 4h con timestamp T (cerrando a T+4h):
  # Usar el último funding settled antes del CIERRE de la vela.
  last_funding = funding.loc[funding.funding_time < T_close_dt].iloc[-1]
  # Para H3 "promedio 24h": ventana rolling de 3 settlements anteriores.
  funding_24h_avg = funding.loc[funding.funding_time < T_close_dt].tail(3).funding_rate.mean()
  ```
- **Importante**: la señal usa funding del PERP, pero la orden se ejecuta en SPOT. La hipótesis H3 asume que el sentiment del perp anticipa el spot — la validación de esa asunción es el research mismo.

### 3.3 DXY (FRED)

- **Frecuencia**: 1 valor diario, business days only (sin sábados, domingos, holidays americanos).
- **Publicación real**: FRED actualiza con ~1 business day de lag. El valor del día `D` se publica el día `D+1` (a veces más).
- **Regla de alineación conservadora**:
  ```python
  # Asumimos disponibilidad 2 días después del cierre del día (margen seguro).
  cutoff = T_close_dt - pd.Timedelta(days=2)
  dxy_value = dxy.loc[dxy.date <= cutoff].iloc[-1].dxy
  ```
- **MA 20d** para "uptrend": calculada sobre cierres DXY ya disponibles a `cutoff`.
- **Gaps esperados**: weekends + ~10 holidays/año. Forward-fill es OK porque DXY se considera "estable" en weekends para fines de filtro macro.

---

## 4. Antipatrones explícitamente prohibidos

| Patrón | Por qué prohibido |
|---|---|
| `.shift(0)` o `merge_asof` con `direction='nearest'` | Permite look-ahead implícito |
| Usar valor F&G de `D` en señal de vela `D+00:00` | Publicación real tiene delay, asumirlo instantáneo sobreestima edge |
| Usar funding rate del settlement actual en señal que cierra al mismo timestamp | Race condition con el settlement |
| Llenar NaN de DXY weekends con valor del lunes siguiente | Look-ahead absoluto |
| Cualquier `groupby + transform` sin verificar boundary del rolling | Look-ahead típico de mean-reversion |

---

## 5. Funciones helper a implementar en Fase 2

En `research/v6/signals/_alignment.py` (módulo compartido):

```python
def align_daily_to_4h(daily_df, ohlcv_4h, value_col, lag_hours=4) -> pd.Series:
    """Para cada cierre de vela 4h, devuelve el último value_col publicado
    antes del cierre, con lag_hours de margen."""

def align_funding_8h_to_4h(funding_df, ohlcv_4h, agg='last') -> pd.Series:
    """Para cada cierre de vela 4h, devuelve la última (o avg ventana 24h)
    funding rate publicada antes del cierre."""

def align_dxy_to_4h(dxy_df, ohlcv_4h, lag_days=2) -> pd.Series:
    """Para cada cierre de vela 4h, devuelve el último DXY publicado al menos
    lag_days antes del cierre."""
```

Todas son funciones puras, testeables aisladamente. Tests obligatorios en
`research/v6/tests/test_alignment.py` antes de usarlas en cualquier signal generator.

---

## 6. Tests obligatorios pre-señal

Antes de que cualquier signal generator (Fase 2) use estos alignments:

1. **Sin look-ahead**: para cada `T_close_dt`, el `value` devuelto debe tener `source_timestamp < T_close_dt - lag_minimum`.
2. **Determinismo**: dos corridas sobre el mismo input devuelven exactamente la misma Series.
3. **No-NaN en el período de interés**: train+val+walk-forward debe tener todos los valores resueltos (NaN sólo aceptable en warm-up inicial < ventana del indicador más largo).
4. **Boundary sane**: el primer valor del alignment ocurre cuando ambos datasets se solapan (no antes).

Estos tests se commitean junto con `_alignment.py` y se corren en `pytest` antes de cualquier backtest. Si fallan, Fase 2 no avanza.

---

## 7. Hallazgos relevantes del fetch (2026-05-20)

| Fuente | Rows | Span | Observación |
|---|---|---|---|
| F&G | 3,027 | 2018-02-01 → 2026-05-20 | 22.7% en F&G ≤ 25 (sample sólido para H1) |
| DXY | 5,107 | 2006-01-02 → 2026-05-15 | Coverage excede el período de research por 12 años; sobra |
| Funding BTC | 7,333 | 2019-09-10 → 2026-05-20 | **0.9% en funding < -0.02% (66 eventos). Flag amarillo para H3-standalone con threshold negativo.** |
| Funding ETH | 7,099 | 2019-11-27 → 2026-05-20 | **0.7% en funding < -0.02% (52 eventos). Sample size más chico aún.** |

**Decisión metodológica derivada**: para H3-standalone, evaluar dos thresholds de capitulation (-0.02% y -0.01%) y reportar ambos con un asterisco sobre el de menor sample. NO ajustar threshold post-resultado para "encontrar el que funciona" — eso es data snooping.
