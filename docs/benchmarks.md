# Benchmarks

8 scenarios with these parameters:
- 100 messages
- body : simple string `test`

| Scenario | Time (s) |
| --- | --- |
| Python BP to Python BO with Iris Message | 0.239 |
| Python BP to Python BO with Python Message | 0.232 |
| ObjectScript BP to Python BO with Iris Message | 0.294 |
| ObjectScript BP to Python BO with Python Message | 0.242 |
| Python BP to ObjectScript BO with Iris Message | 0.242 |
| Python BP to ObjectScript BO with Python Message | 0.275 |
| ObjectScript BP to ObjectScript BO with Iris Message | 0.159 |
| ObjectScript BP to ObjectScript BO with Python Message | 0.182 |

Benchmarks can be run in the unit test with the following command :

```bash
pytest src/tests/test_bench.py
```