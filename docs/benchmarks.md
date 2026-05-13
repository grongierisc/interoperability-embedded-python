# Benchmarks

24 scenarios with these parameters:
- 100 messages
- body: simple string `test`

The benchmark matrix covers these routes:
- Python BP to Python BO
- Python BP to ObjectScript BO
- ObjectScript BP to Python BO
- ObjectScript BP to ObjectScript BO

Each route is tested with these message types:
- IRIS `Ens.StringRequest`
- `Message`
- `PydanticMessage`
- `PersistentMessage`
- `PickleMessage`
- `PydanticPickleMessage`

The test writes current timing results to `src/tests/e2e/local/bench/result.txt`.

Benchmarks can be run in the unit test with the following command :

```bash
PYTHONPATH=src pytest src/tests/e2e/local/test_bench.py
```
