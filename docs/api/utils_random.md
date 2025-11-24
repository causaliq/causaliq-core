# Random Number Utilities

Stable, reproducible random number generation for scientific computing and experimental repeatability.

## Core Functions

::: causaliq_core.utils.random.random_generator
    options:
      show_source: false

::: causaliq_core.utils.random.set_random_seed
    options:
      show_source: false

::: causaliq_core.utils.random.stable_random
    options:
      show_source: false

::: causaliq_core.utils.random.generate_stable_random
    options:
      show_source: false

::: causaliq_core.utils.random.init_stable_random
    options:
      show_source: false

## Classes

::: causaliq_core.utils.random.Randomise
    options:
      show_source: false

::: causaliq_core.utils.random.RandomIntegers
    options:
      show_source: false

## Usage Examples

### Basic Random Number Generation

```python
from causaliq_core.utils.random import random_generator, set_random_seed

# Set seed for reproducibility
set_random_seed(42)

# Get generator instance
gen = random_generator()
value = gen.random()  # Generate random float [0.0, 1.0)
```

### Stable Random Sequences

```python
from causaliq_core.utils.random import stable_random, init_stable_random

# Initialize stable random sequence
init_stable_random()

# Generate stable random numbers
for i in range(5):
    print(stable_random())  # Same sequence every run
```

### Random Integer Sequences

```python
from causaliq_core.utils.random import RandomIntegers

# Create iterator for random integers 1-10
rand_ints = RandomIntegers(1, 10)
for value in rand_ints:
    print(value)  # Each integer appears exactly once
```

### Experiment Randomization Types

```python
from causaliq_core.utils.random import Randomise

# Available randomization types for experiments
print(Randomise.ORDER)      # Randomize variable order
print(Randomise.NAMES)      # Randomize variable names  
print(Randomise.KNOWLEDGE)  # Randomize knowledge
print(Randomise.ROWS)       # Randomize row order
print(Randomise.SAMPLE)     # Randomize sample rows
```

## Features

- **Cross-platform reproducibility**: Same sequences on all platforms
- **Stable sequences**: Pre-generated sequence for consistent results
- **Configurable seeding**: Support for both deterministic and random seeding
- **Iterator patterns**: Clean iteration over random integer sequences
- **Experiment support**: Built-in randomization types for scientific experiments