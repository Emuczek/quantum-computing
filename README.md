# QAOA Backend API

REST API dla Quantum Approximate Optimization Algorithm (QAOA) - kwantowego algorytmu optymalizacji przybliżonej.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-green.svg)](https://fastapi.tiangolo.com/)
[![Qiskit](https://img.shields.io/badge/Qiskit-2.2.3-purple.svg)](https://qiskit.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## O projekcie

System umożliwia rozwiązywanie problemów optymalizacji kombinatorycznej przy użyciu algorytmu QAOA poprzez interfejs REST API. Konwertuje wyrażenia matematyczne do formatu kwantowego, wykonuje optymalizację i zwraca rozkład prawdopodobieństwa rozwiązań.

**Funkcjonalności:**
- Automatyczna konwersja wyrażeń do formatu QUBO
- Budowa i optymalizacja obwodów kwantowych QAOA
- Wsparcie dla symulatora lokalnego i sprzętu IBM Quantum
- REST API z automatyczną dokumentacją (OpenAPI)
- Konteneryzacja Docker

## Szybki start

### Docker

```bash
git clone https://github.com/Emuczek/quantum-computing.git
cd quantum-computing
docker compose up --build
```

API dostępne na: http://localhost:8000

### Instalacja lokalna

```bash
git clone https://github.com/Emuczek/quantum-computing.git
cd quantum-computing
pip install -r requirements.txt
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Użycie

### Przykład podstawowy

```bash
curl -X POST http://localhost:8000/solve-qaoa \
  -H "Content-Type: application/json" \
  -d '{
    "expression": "5*x[0] + 3*x[1] - 2*x[0]*x[1]",
    "p": 1,
    "maxiter": 50,
    "backend": "simulator",
    "shots": 1024
  }'
```

### Odpowiedź

```json
{
  "success": true,
  "optimal_cost": -2.6747,
  "optimal_params": [2.674, 2.370],
  "probabilities": {
    "00": 0.862,
    "10": 0.073,
    "11": 0.040,
    "01": 0.025
  },
  "num_qubits": 2,
  "backend": "simulator"
}
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/solve-qaoa",
    json={
        "expression": "x[0]*x[1] + x[1]*x[2]",
        "p": 2,
        "maxiter": 100,
        "backend": "simulator"
    }
)

result = response.json()
print(f"Optimal cost: {result['optimal_cost']}")
```

## Dokumentacja API

Po uruchomieniu serwera:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Główny endpoint

**POST /solve-qaoa**

| Parametr   | Typ    | Domyślnie | Opis                           |
|------------|--------|-----------|--------------------------------|
| expression | string | wymagane  | Wyrażenie Python (np. `x[0] + x[1]`) |
| p          | int    | 1         | Głębokość QAOA (1-5)           |
| maxiter    | int    | 50        | Maksymalna liczba iteracji     |
| backend    | string | simulator | "simulator" lub "ibm"          |
| shots      | int    | 1024      | Liczba pomiarów                |

## Konfiguracja IBM Quantum

Dla użycia rzeczywistego sprzętu IBM, wystarczy wykonać jednorazowo:

```bash
# 1. Skopiuj szablon
cp src/core/save_ibm_credentials.py src/core/save_ibm_credentials_local.py

# 2. Edytuj plik lokalny i wpisz token z https://quantum.ibm.com/account
# IBM_TOKEN = "twój_token"
# CRN = "twój_crn"

# 3. Zapisz credentials
python src/core/save_ibm_credentials_local.py
```