## Case Studies: Where KLEE Fails on Tulipindicators

### Case Study 1: Nonlinear Floating-Point Math Functions as Opaque Black Boxes

**Problem:** KLEE performs symbolic execution at the LLVM IR level. Transcendental math functions like `sqrt()`, `log()`, `sin()`, `cos()`, `atan()`, `exp()`, and `pow()` are **external calls** into `libm` (or uclibc's math library). KLEE cannot symbolically reason about these — it must **concretize** their arguments before calling them, silently forcing a single concrete path through downstream branches.

**Affected indicators (pervasive):**

- **`ti_msw` (Mesa Sine Wave)** — `tulipindicators.c:3054-3056`: The inner loop calls `cos()` and `sin()` with `weight = input[i-j]` where `input` is symbolic. KLEE must concretize `weight` to call these functions, then the branch at line 3058 (`if (fabs(rp) > .001)`) and the subsequent `atan(ip/rp)` at line 3059 are evaluated on the concretized residue, not explored symbolically.

- **`ti_fisher` (Fisher Transform)** — `tulipindicators.c:2516`: `fish = 0.5 * log((1.0+val1)/(1.0-val1)) + 0.5 * fish`. The `log()` call forces concretization of `val1`, which was itself derived from symbolic `high[]` and `low[]` inputs. The clipping branches at lines 2513-2514 (`if (val1 > 0.99)`, `if (val1 < -0.99)`) produce **three** interesting paths (above, below, and within the range), but KLEE will only explore whichever concrete path the concretized value happens to land on.

- **`ti_bbands` (Bollinger Bands)** — `tulipindicators.c:2037` and line 2047: `sqrt(sum2 * scale - (sum * scale) * (sum * scale))` operates on a symbolic accumulation. KLEE concretizes the argument to `sqrt()`.

- **`ti_kama` (Kaufman Adaptive MA)** — `tulipindicators.c:2625`: `pow(er * (short_per - long_per) + long_per, 2)` where `er` is derived from symbolic `input[]` at line 2621.

- **`ti_volatility`** — `tulipindicators.c:4077`: `input[i]/input[i-1]-1.0` feeds symbolic divisions into `sqrt()` at line 4081.

- **`ti_ln`, `ti_log10`, `ti_sqrt`, `ti_exp`, `ti_sin`, `ti_cos`** etc. — all the `TI_TYPE_SIMPLE` vector operators (e.g., line 2734, line 3430) apply transcendental math to every symbolic element. KLEE produces at most 1 concrete evaluation per element rather than exploring the function's domain.

**Impact:** KLEE loses the ability to explore branches that depend on the *output* of transcendental functions. Any conditional that tests a variable derived (even indirectly) from a `sqrt`/`log`/`sin`/etc. result will be explored only along the concretized path. This is the single most pervasive limitation.

---

### Case Study 2: Floating-Point Comparison Branching — SMT Solver Limitations

**Problem:** Even where no transcendental function is involved, KLEE's underlying SMT solvers (STP and Z3) have **weak or incomplete support for floating-point arithmetic**. STP has no native FP theory at all; Z3's `QF_FP` theory is expensive. Symbolic floating-point comparisons (`<`, `>`, `==`) on expressions involving symbolic `double` multiplication, addition, and subtraction produce constraints that solvers either reject, time out on, or approximate poorly (by bit-blasting the IEEE 754 representation).

**Affected code:**

- **`ti_stoch` (Stochastic Oscillator)** — `tulipindicators.c:3531-3558`: The sliding min/max logic has **four** distinct symbolic branch paths per iteration:
  - `if (maxi < trail)` (line 3531) — integer, solvable
  - `if (bar >= max)` (line 3537 inner, 3542 outer) — **FP comparison of two symbolic doubles**
  - `if (mini < trail)` (line 3547) — integer, solvable
  - `if (bar <= min)` (line 3553 inner, 3558 outer) — **FP comparison of two symbolic doubles**

  The FP comparisons involve `high[j]` vs `max` (both symbolic), which the solver must reason about across all possible 64-bit IEEE 754 representations. The equality at line 3562 `kdiff == 0.0` is a further FP-equality check.

- **`ti_fisher`** — `tulipindicators.c:2485` and 2501: `if (bar >= max)` and `if (bar <= min)` where `bar = 0.5 * (high[j] + low[j])` — FP addition and multiplication feeding into comparisons, repeated in a nested while loop.

- **`ti_cmo` (Chande Momentum Oscillator)** — `tulipindicators.c:2127-2128`: `input[i] > input[i-1]` and `input[i] < input[i-1]` — each iteration of the loop creates **two** FP comparison branches on symbolic data, creating a combinatorial explosion of `2^(2*period)` path combinations that the FP-aware solver must handle.

- **`ti_psar` (Parabolic SAR)** — `tulipindicators.c:3193`: `high[0] + low[0] <= high[1] + low[1]` — symbolic FP addition and comparison at the very first branch. Then lines 3209-3232 contain 8+ additional FP comparisons per loop iteration on symbolic `high[i]`, `low[i]`, `sar`, and `extreme`.

- **`ti_bop` (Balance of Power)** — `tulipindicators.c:2072`: `if (hl <= 0.0)` where `hl = high[i] - low[i]` — subtraction of two symbolic doubles compared to zero.

**Impact:** The solver either returns UNKNOWN (KLEE treats the branch as infeasible), times out (KLEE may concretize and lose a path), or bit-blasts 64-bit IEEE 754 numbers (exponential blowup). In practice, many feasible paths through these branches will simply not be explored.

---

### Case Study 3: Path Explosion from Loop Unrolling with Symbolic Branches

**Problem:** The driver passes `DATA_SIZE = 8` as the `size` parameter (`klee_driver.c:18`, line 46). Although `size` is concrete, many indicator loops contain **symbolic branches inside the loop body**. KLEE must fork the execution state at each symbolic branch, and with nested loops, this creates exponential path explosion.

**Worst offenders:**

- **`ti_cci` (Commodity Channel Index)** — `tulipindicators.c:2095-2108`: The outer loop runs `size` iterations. Inside, `ti_buffer_push` at line 2097 includes the branch `if ((BUFFER)->pushes >= (BUFFER)->size)` (from the macro at line 1390). More critically, the inner loop at line 2101 `for (j = 0; j < period; ++j)` computes `fabs(avg - sum->vals[j])`. With `period=3` (from the driver's `options[0]`) and `size=8`, the total symbolic `fabs()` calls = `O(size * period)`. Though `fabs` is relatively simple, each one's result feeds into an accumulation that ultimately affects code paths.

- **`ti_stoch`** — `tulipindicators.c:3528-3573`: The outer loop runs 8 iterations. Each iteration has up to **6 symbolic FP branches** (two for the max sliding window, two for the min sliding window, one for `kdiff == 0.0`, and inner while-loops for window rescans). With period=3, the window rescan (`while(++j <= i)`) nests another `O(period)` FP branches per rescan event. The worst-case state count is approximately `2^(6*8) = 2^48` paths — KLEE will exhaust memory or time.

- **`ti_fisher`** — `tulipindicators.c:2477-2518`: Similar sliding min/max pattern to `ti_stoch`, with nested `while` loops (lines 2483-2489, lines 2499-2505) that fork on symbolic FP comparisons. Plus the `mm == 0.0` branch at line 2511 and the two clipping branches at lines 2513-2514, totaling ~8 symbolic branches per outer loop iteration across 6 iterations (size=8, period=3).

- **`ti_psar`** — `tulipindicators.c:3207-3234`: 7 iterations of the loop, each with ~10 symbolic FP branches (lines 3209-3232 contain comparisons on `sar`, `low[i-2]`, `low[i-1]`, `high[i]`, `extreme`, `accel`, plus the trend-reversal check at line 3226). Theoretical paths: `O(2^70)`.

- **`ti_cmo`** — `tulipindicators.c:2126-2137`: Each loop iteration has **4** symbolic branches (two `>` checks and two `<` checks for the sliding window update at lines 2132-2135). With ~5 iterations, this is `2^20 ~ 1M` paths from this indicator alone.

**Impact:** KLEE's state space grows exponentially. With 104 indicators called sequentially, the accumulated state count becomes intractable. In practice, KLEE will hit its memory limit or instruction limit long before exploring even a fraction of the paths in the more complex indicators.

---

### Case Study 4: Dynamic Memory Allocation via `malloc()` Inside Indicator Functions

**Problem:** Several indicators call `malloc()` internally. KLEE models `malloc()` but this creates challenges: (a) the symbolic executor must track dynamically allocated memory objects, increasing per-state overhead; (b) if `malloc` returns `NULL`, a separate error path is exercised; (c) the `ti_buffer_new` function at `tulipindicators.c:4335-4342` computes allocation size from the concrete `period` parameter, but does not check for `malloc` returning `NULL` — line 4338 (`ret->size = size`) will **dereference a NULL pointer** if memory is exhausted, which KLEE would report as an error but which masks the real analysis.

**Affected indicators:**

- **`ti_cci`** — line 2093: `ti_buffer *sum = ti_buffer_new(period)` — allocates a ring buffer. The buffer is used throughout lines 2095-2109 and freed at line 2110.

- **`ti_stoch`** — lines 3525-3526: Two `ti_buffer_new()` calls (`k_sum` and `d_sum`), freed at lines 3574-3575.

- **`ti_stochrsi`** — line 3590: `ti_buffer *rsi = ti_buffer_new(period)`.

- **`ti_atr_ref`** — line 1921: `malloc((unsigned int)tr_size * sizeof(TI_REAL))` — allocates a temporary true-range array. This one *does* check for NULL at line 1922, but then at line 1924 it calls `ti_tr()` which itself processes symbolic inputs, followed by `ti_wilders()` at line 1930 — a chain of function calls on dynamically allocated buffers that KLEE must track per-state.

- **`ti_atr_stream_new`** — line 1947: `malloc(sizeof(ti_stream_atr))`.

**Impact:** Each `malloc` in KLEE creates a new `MemoryObject` per execution state. Since the driver calls all 104 indicators sequentially, states from early indicators accumulate allocated memory objects. The `ti_buffer_new` / `ti_buffer_free` pattern means KLEE also must model `free()` semantics per state. This significantly increases per-state memory overhead and slows exploration. Additionally, `ti_buffer_new` lacks a NULL check, so KLEE will fork on the NULL-return path and immediately hit a NULL dereference, generating a spurious error report.

---

### Case Study 5: Indirect Calls Through the `ti_indicators[]` Function Pointer Table

**Problem:** The driver dispatches all 104 indicators through an **indirect call** at `klee_driver.c:46-50`:

```c
ti_indicators[i].indicator(
    DATA_SIZE,
    (TI_REAL const *const *)inputs,
    options,
    (TI_REAL *const *)outputs);
```

The loop index `i` is concrete (the loop is over `TI_INDICATOR_COUNT` with a concrete counter), so KLEE can resolve which function pointer is called at each iteration. **However**, the structural problem is subtler:

1. **State accumulation across iterations:** Because the loop at line 44 calls all 104 indicators **sequentially on the same symbolic inputs**, execution states fork within indicator `i` and each forked state then proceeds to call indicator `i+1`. If indicator 0 creates 4 states, and indicator 1 creates 4 states per incoming state, after just 10 indicators KLEE may have `4^10 ~ 1M` states. In practice, KLEE's searcher (default: interleaved RandomPath + CoveringNew) will starve most states, causing **severely incomplete coverage** of later indicators.

2. **Shared symbolic arrays reused across indicators:** All 104 indicators read from the same `input0`-`input3` symbolic arrays (`klee_driver.c:29-32`). Path constraints added by indicator `i` (e.g., `input0[0] > input0[1]`) remain in the state's constraint set when indicator `i+1` runs. This means later indicators operate under **artificially constrained** symbolic inputs — they see only input values that satisfied all earlier indicators' branch conditions, not the full symbolic domain. This fundamentally undermines the purpose of symbolic testing.

3. **Shared output arrays:** The same `out0`, `out1`, `out2` arrays (lines 40-41) are reused across all indicator calls. Indicator `i+1` overwrites what indicator `i` wrote. While this doesn't affect correctness of individual indicator execution, it means KLEE's generated test cases capture only the **last** indicator's output state, making it harder to validate results.

**Impact:** The sequential single-driver design means KLEE will practically explore only a tiny subset of indicators thoroughly (likely the first few simple ones like `abs`, `acos`, `ad`) before the state space becomes intractable. Complex indicators that appear later in the sorted `ti_indicators[]` array (like `volatility` at index 94, `wma` at index 103) will receive almost no exploration.

---

### Case Study 6: Option Mismatch — Fixed Options Array vs. Per-Indicator Requirements

**Problem:** The driver uses a single **hardcoded concrete options array** at `klee_driver.c:38`:

```c
TI_REAL options[] = { 3.0, 5.0, 2.0 };
```

This same array is passed to all 104 indicators. Different indicators interpret these values completely differently, and some require specific constraints between option values that `{3.0, 5.0, 2.0}` violates.

**Specific failures:**

- **`ti_psar` (Parabolic SAR)** — `tulipindicators.c:3189-3190`: Requires `accel_step > 0` AND `accel_max > accel_step`. With `options = {3.0, 5.0}`, this passes (`3.0 > 0` and `5.0 > 3.0`). But realistic SAR uses `accel_step = 0.02, accel_max = 0.2`. With `accel_step = 3.0`, the acceleration factor immediately saturates at line 3214 (`if (accel > accel_max) accel = accel_max`), causing the trend-reversal logic at line 3226 to behave abnormally — KLEE explores only unrealistic execution paths.

- **`ti_bbands` (Bollinger Bands)** — `tulipindicators.c:2025-2026`: Uses `options[0]` as period (=3) and `options[1]` as standard-deviation multiplier (=5.0). A `stddev` multiplier of 5.0 is extreme (typical is 2.0); the bands will be so wide that certain code paths testing whether prices cross bands will never trigger.

- **`ti_stoch` (Stochastic Oscillator)** — `tulipindicators.c:3507-3514`: Takes **three** options: `k_period` (=3), `k_slowing_period` (=5), and `d_period` (=2). The start offset is `k_period + k_slowing_period + d_period - 3 = 3+5+2-3 = 7`. With `DATA_SIZE = 8`, only **1 output value** will be produced (size - start = 8 - 7 = 1). This means the main output loop body at lines 3568-3571 executes only once, severely limiting path coverage.

- **`ti_vidya`** — Uses three options: `short_period`, `long_period`, `alpha`. With `{3.0, 5.0, 2.0}`, `alpha = 2.0` is far outside the typical `[0, 1]` range, causing unrealistic smoothing behavior.

- **`ti_macd`** — Takes `short_period` (=3), `long_period` (=5), `signal_period` (=2). With `DATA_SIZE = 8`, the start offset is `long_period - 1 = 4`, leaving only 4 data points. This gives very little room for KLEE to explore the signal EMA smoothing loop.

- **`ti_ultosc` (Ultimate Oscillator)** — Takes `short_period` (=3), `medium_period` (=5), `long_period` (=2). But the code requires `short < medium < long`. With `long_period = 2 < short_period = 3`, the function likely returns `TI_INVALID_OPTION` or computes nonsensical results, meaning **zero** meaningful paths are explored for this indicator.

**Impact:** Many indicators are either tested with degenerate parameters (producing <=1 output value and trivial execution paths), unrealistic parameters (exercising only edge-case behavior), or invalid parameters (producing immediate early-return with no real code exploration). KLEE achieves poor coverage of the indicator logic that would actually matter.

---

### Summary Table

| # | Failure Mode | Root Cause | Key Code Locations | Severity |
|---|---|---|---|---|
| 1 | Transcendental FP as black boxes | `sqrt`/`log`/`sin`/`cos`/`pow`/`exp` are external calls | Lines 2037, 2516, 3054-3056, 2625, 4081 | **Critical** — affects 30+ indicators |
| 2 | FP comparison unsolvability | STP lacks FP theory; Z3 FP is expensive | Lines 3531-3558, 2485-2508, 2127-2128, 3193 | **Critical** — affects all indicators with FP branches |
| 3 | Path explosion in loops | Symbolic branches inside iterated loops | Lines 3528-3573, 2477-2518, 3207-3234, 2126-2137 | **High** — exponential state blowup |
| 4 | Dynamic allocation overhead | `malloc`/`free` per state, no NULL checks | Lines 4335-4342, 2093, 3525-3526, 1921 | **Medium** — increased memory, spurious errors |
| 5 | Sequential dispatch + state accumulation | 104 indicators on shared symbolic state | Driver lines 44-52, 29-32 | **High** — later indicators starved |
| 6 | Fixed options mismatch | One `{3, 5, 2}` array for all 104 indicators | Driver line 38 vs. per-indicator constraints | **High** — degenerate/invalid paths |
