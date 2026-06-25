# ADR-0007: Zero-Dependency Log Parsing

## Status
Accepted

## Context
The project rules originally mandated the use of `Pydantic` models to strictly validate incoming GCP log JSON and prevent application crashes from loose dictionary lookups. However, introducing `Pydantic` would require adding an external dependency to the project (e.g. via a `requirements.txt` or a virtual environment), complicating the distribution and execution model of the simple Python daemon script `scout_daemon.py`.

## Decision
We decided to remove the `Pydantic` mandate and instead use standard library `dataclasses` alongside explicit `try/except` blocks to parse and validate the incoming JSON logs. 

## Consequences
- **Positive:** We maintain a zero-dependency architecture. Users can run the plugin script immediately using only the Python standard library.
- **Positive:** We still achieve structural validation and type clarity over the raw JSON payload, mitigating the risk of crashing on unexpected schemas.
- **Negative:** We lose the automatic type coercion and deeper validation features that Pydantic provides out-of-the-box.
