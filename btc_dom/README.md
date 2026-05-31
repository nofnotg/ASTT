# BTCDOM Percent Converted Data

## Conversion rule

`percent_display = raw_index_value / 100`

Example:

`5572.7 -> 55.7270%`

## Important note

These files convert the uploaded Binance BTCDOM-style raw index values into percent-style display values.
They should be used as a strategy/backtest filter dataset, not as a guaranteed CoinMarketCap/CoinGecko/TradingView market-cap BTC dominance definition.

## Output columns

- `timestamp_ms`: original Unix timestamp in milliseconds
- `datetime_utc`: UTC datetime
- `datetime_kst`: Korea Standard Time datetime
- `open_raw`, `high_raw`, `low_raw`, `close_raw`: original raw index values
- `open_pct`, `high_pct`, `low_pct`, `close_pct`: raw values divided by 100
- `close_pct_label`: text label with `%`
- `volume`: original volume
- `source_note`: conversion caution

## Files

- `btcdom_1d_percent.csv`
- `btcdom_4h_percent.csv`
- `btcdom_1h_percent.csv`
- `btcdom_percent_summary.csv`
