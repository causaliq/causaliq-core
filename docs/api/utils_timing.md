# Timing Utilities

Performance measurement and timeout functionality for algorithm execution.

## Timing Collection

::: causaliq_core.utils.timing.Timing
    options:
      show_source: false

## Timeout Functions

::: causaliq_core.utils.timing.run_with_timeout
    options:
      show_source: false

::: causaliq_core.utils.timing.with_timeout
    options:
      show_source: false

::: causaliq_core.utils.timing.TimeoutError
    options:
      show_source: false

## Usage Examples

### Basic Timing Collection

```python
from causaliq_core.utils.timing import Timing
from time import sleep

# Enable timing collection
Timing.on(True)

# Time an operation
start = Timing.now()
sleep(0.1)  # Simulate work
Timing.record("sleep_test", 1, start)

# View timing summary
print(Timing.summary())

# Turn off timing
Timing.off()
```

### Filtered Timing

```python
from causaliq_core.utils.timing import Timing

# Only collect timing for specific actions
Timing.on(True, filter={"critical_operation", "slow_function"})

# This will be recorded
start = Timing.now()
# ... do critical operation ...
Timing.record("critical_operation", 100, start)

# This will be ignored
start = Timing.now()
# ... do normal operation ...
Timing.record("normal_operation", 50, start)
```

### Function Timeout Decorator

```python
from causaliq_core.utils.timing import with_timeout, TimeoutError

@with_timeout(5)  # 5 second timeout
def slow_function():
    # This function will be interrupted if it takes > 5 seconds
    import time
    time.sleep(10)  # Would normally take 10 seconds

try:
    slow_function()
except TimeoutError:
    print("Function timed out!")
```

### Direct Timeout Execution

```python
from causaliq_core.utils.timing import run_with_timeout, TimeoutError

def potentially_slow_task(data):
    # Process data...
    return processed_data

try:
    result = run_with_timeout(
        potentially_slow_task,
        args=(my_data,),
        timeout_seconds=30
    )
    print(f"Completed: {result}")
except TimeoutError:
    print("Task took too long!")
```

### Adding Pre-calculated Times

```python
from causaliq_core.utils.timing import Timing

# Enable timing
Timing.on(True)

# Add a timing measurement without calling now()/record()
Timing.add("algorithm_run", elapsed_time=1.234, scale=500)

# View results
print(Timing.summary())
```

## Features

- **Singleton pattern**: Global timing collection across application
- **Filtering**: Collect timing only for specified actions
- **Scale tracking**: Record scale indicators (e.g., number of nodes)
- **Statistical summary**: Automatic count, mean, and max calculations
- **Thread-safe timeouts**: Reliable timeout functionality for long-running operations
- **Decorator support**: Clean timeout decoration for functions
- **Flexible timeout**: Support both function decoration and direct execution