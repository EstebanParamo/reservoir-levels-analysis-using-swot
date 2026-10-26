#!/usr/bin/env python3
"""
metrics_calculator.py
---------------------
Standardized hydrological accuracy metrics calculator:
- Pearson correlation coefficient (r)
- Root Mean Square Error (RMSE)
- Mean Absolute Error (MAE)
- Bias (Mean Error / Sesgo)
- Relative Bias (%) and Relative MAE (% of usable reservoir capacity)
- Nash-Sutcliffe Efficiency (NSE)
"""

import numpy as np
import pandas as pd


def compute_hydrological_metrics(obs, sim, usable_capacity=None):
    """
    Computes standard validation metrics between observed and simulated/satellite series.

    Parameters:
        obs (array-like): Reference in situ values.
        sim (array-like): Satellite estimated values.
        usable_capacity (float, optional): Total usable capacity of the reservoir (for % MAE / % Bias).

    Returns:
        dict: Summary metrics.
    """
    obs_arr = np.asarray(obs, dtype=np.float64)
    sim_arr = np.asarray(sim, dtype=np.float64)

    # Filter out NaNs
    valid_mask = ~np.isnan(obs_arr) & ~np.isnan(sim_arr)
    x = obs_arr[valid_mask]
    y = sim_arr[valid_mask]
    n = len(x)

    if n < 2:
        return {
            "n": n, "r": np.nan, "rmse": np.nan, "mae": np.nan,
            "bias": np.nan, "nse": np.nan, "r2": np.nan
        }

    # Pearson correlation r
    cov = np.cov(x, y)[0, 1]
    std_x = np.std(x, ddof=1)
    std_y = np.std(y, ddof=1)
    r = cov / (std_x * std_y) if (std_x > 0 and std_y > 0) else np.nan

    # Errors
    diff = y - x
    rmse = np.sqrt(np.mean(diff ** 2))
    mae = np.mean(np.abs(diff))
    bias = np.mean(diff)

    # Nash-Sutcliffe Efficiency (NSE)
    var_obs = np.sum((x - np.mean(x)) ** 2)
    nse = 1.0 - (np.sum(diff ** 2) / var_obs) if var_obs > 0 else np.nan

    # Coefficient of determination R^2
    r2 = r ** 2 if not np.isnan(r) else np.nan

    result = {
        "n": int(n),
        "r": round(float(r), 3),
        "r2": round(float(r2), 3),
        "rmse": round(float(rmse), 3),
        "mae": round(float(mae), 3),
        "bias": round(float(bias), 3),
        "nse": round(float(nse), 3)
    }

    if usable_capacity and usable_capacity > 0:
        result["mae_pct_capacity"] = round(float((mae / usable_capacity) * 100.0), 2)
        result["bias_pct_capacity"] = round(float((bias / usable_capacity) * 100.0), 2)

    return result


if __name__ == "__main__":
    # Self-test example
    obs_test = [2980.5, 2975.2, 2972.1, 2965.8, 2963.4]
    sim_test = [2981.1, 2976.0, 2973.2, 2966.5, 2964.1]
    res = compute_hydrological_metrics(obs_test, sim_test, usable_capacity=220.0)
    print("Self-test metrics output:")
    for k, v in res.items():
        print(f"  {k}: {v}")
