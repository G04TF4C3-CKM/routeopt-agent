# Historical Karp/MMC regression fixture

`loads_5_8_hiring_firing_path.txt` is the five-load, twelve-hour scenario used in the original exploratory notebooks, especially:

- `KarpsMeanMinCycle_2.ipynb`
- `DoubleCheck_Optimality.ipynb`

The saved notebook run is the historical oracle for the production port.

## Expected augmentation sequence

The original Karp/MMC implementation first found three firing paths:

```text
[-1, 10, 1, 0]
[-1, 2, 7, 0]
[-1, 4, 5, 0]
```

Those discharges reduced the solution from five drivers to two. The ordinary search then stopped, but the modified residual optimality check still found one feasible improving cycle. The later multi-label hiring/reconnection search found:

```text
[0, 5, 4, 1, 10, 7, 2, -1, 6, 9, 0]
```

Applying that cycle kept the driver count at two while reducing total route time from approximately `21.78032107205433` to `21.677714866639274`.

## Purpose

This fixture is intentionally small and diagnostic. It should remain a regression target while the notebook algorithm is separated into production search and augmentation-application components.
