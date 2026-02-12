# Stats237 API (v1.3)

The API is callable and reproducible: every response includes a `provenance` envelope
with versioning + runtime metadata + request hash + effective seed.

## Start the server

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e stats237_quantlib
python -m pip install -r requirements.txt

uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Interactive docs live at `/docs`.

## Endpoints

### Meta
- `GET /health`
- `GET /meta`

### Black–Scholes (supports dividend yield `q`)
- `POST /price/black_scholes`
- `POST /greeks/black_scholes`
- `POST /implied_vol`

### Binomial (CRR)
- `POST /price/binomial` (European/American, call/put)

### Monte Carlo (variance reduction)
- `POST /mc/asian/arithmetic_call`
- `POST /mc/basket/call`

### Calibration (new in v1.3)
- `POST /calibration/iv_curve/from_prices`
- `POST /calibration/iv_curve/from_vols`
- `POST /calibration/iv_surface/query`

## Example: Black–Scholes call with dividend yield

```bash
curl -s http://127.0.0.1:8000/price/black_scholes \
  -H "Content-Type: application/json" \
  -d '{"S0":100,"K":100,"r":0.02,"q":0.01,"T":1.0,"sigma":0.2,"is_call":true}'
```

## Example: IV curve from prices → PCHIP smile

```bash
curl -s http://127.0.0.1:8000/calibration/iv_curve/from_prices \
  -H "Content-Type: application/json" \
  -d '{
    "S0":100,
    "r":0.02,
    "q":0.01,
    "T":0.5,
    "is_call":true,
    "strikes":[80,90,100,110,120],
    "prices":[21.9,13.1,6.2,2.5,0.9],
    "fit":"pchip",
    "query_strikes":[95,105]
  }'
```
