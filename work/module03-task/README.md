# Simple Python Calculator

A small calculator that can add, subtract, and multiply two numbers.

## Files

- `calculator.py` — `add()`, `subtract()`, and `multiply()` functions
- `main.py` — runs the calculator with sample values

## Usage

```bash
python main.py
```

## `multiply(a, b)`

Defined in `calculator.py`. Returns the product of two numbers.

| Argument | Description |
| -------- | ----------- |
| `a` | First number |
| `b` | Second number |

**Returns:** `a * b`

### Example

```python
from calculator import multiply

multiply(5, 3)   # 15
multiply(-2, 4)  # -8
```

`main.py` also prints `5 * 3 = 15` when you run it.
