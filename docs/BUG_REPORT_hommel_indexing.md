# Bug Report: Off-by-one indexing crash in hommel findDiscoveries

**Date discovered:** 2026-04-17
**Branch:** feature/stand-alone-build
**Severity:** Critical — segfault or silently wrong TDP values

---

## Symptoms

The app crashes with a macOS `EXC_BAD_ACCESS (SIGSEGV)` when running the ARI
analysis after loading a stat map. The crash is intermittent: some datasets
trigger it, others don't. The crash report points to:

```
hommel.cpython-310-darwin.so → findDiscoveries() + 136
KERN_INVALID_ADDRESS at 0x00000007383ffff8
```

## Root cause

An indexing mismatch between the Python caller and the C++ function.

The C++ function `findDiscoveries` (in `cpp_extensions/cpp_sources/hommel.cpp`)
expects **1-based** indices in the `idx` vector. It accesses p-values as:

```cpp
allp[idx[i] - 1]   // line 216 — subtracts 1, expects idx values starting at 1
```

The Python caller (`analyses/hommel.py`, line 141) used 0-based indexing.
The correct 1-based version was present as a commented-out line directly above.
Both lines were committed this way in the initial commit (`e744273`,
2025-05-13 "add ar_application root dir") — the bug has existed since the
file was first added to the repo:

```python
# Commented out (correct):
# ix_sorted_p[self.sorter] = np.arange(1, m + 1)   # 1-based: [1, 2, ..., m]

# Active (broken):
ix_sorted_p[self.sorter] = np.arange(m)              # 0-based: [0, 1, ..., m-1]
```

## Why it was intermittent

The 0-based indices shift every value down by 1. The C++ code then does
`idx[i] - 1`, so:

| `idx[i]` value | C++ accesses        | Result                              |
|-----------------|---------------------|-------------------------------------|
| `0`             | `allp[-1]`          | Unsigned underflow → **segfault**   |
| `1` to `m-1`    | `allp[0]` to `[m-2]` | Valid memory, **wrong values**    |
| `m`             | `allp[m-1]`         | Correct, but never produced         |

The crash only happens when the voxel with the smallest p-value (sorter
rank 0) is included in the selected cluster. If that voxel isn't in the
selection, all indices are >= 1 and the memory access stays in bounds — but
the TDP values are silently wrong because every index is off by one.

## The fix

One-line change in `ari_application/analyses/hommel.py`, line 141:

```python
# Before (broken):
ix_sorted_p[self.sorter] = np.arange(m)

# After (fixed):
ix_sorted_p[self.sorter] = np.arange(1, m + 1)
```

This restores 1-based indexing to match the C++ expectation.

## Impact

- **Crash case:** segfault, app terminates immediately with no Python traceback
- **Non-crash case:** TDP (True Discovery Proportion) values were computed from
  wrong p-value lookups. Every index was off by one, meaning each voxel's
  discovery status was evaluated against a neighboring p-value in the sorted
  order. Results appeared plausible but were statistically incorrect.
