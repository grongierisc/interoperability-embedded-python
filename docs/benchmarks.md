# Benchmarks

8 senarios with thoses parameters :
- 100 messages
- body : simple string `test`

| Scenario | Time (s) |
| --- | --- |
| Python BP to Python BO with Iris Message | 0.239 |
| Python BP to Python BO with Python Message | 0.232 |
| ObjetScript BP to Python BO with Iris Message | 0.294 |
| ObjetScript BP to Python BO with Python Message | 0.242 |
| Python BP to ObjetScript BO with Iris Message | 0.242 |
| Python BP to ObjetScript BO with Python Message | 0.275 |
| ObjetScript BP to ObjetScript BO with Iris Message | 0.159 |
| ObjetScript BP to ObjetScript BO with Python Message | 0.182 |

Benchmarked can be run in the unit test with the following command :

```bash
pytest src/tests/test_bench.py
```