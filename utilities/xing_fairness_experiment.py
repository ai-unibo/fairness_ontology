#!/usr/bin/env python3
"""XING fairness-aware re-ranking experiment.

This script is adapted to XING57/2017 JSON files like the one uploaded in the
conversation. It:
  1) loads one JSON query file (or a directory of such files),
  2) builds a baseline ranking from the original order,
  3) applies a simple fairness-aware post-processing re-ranking,
  4) computes fairness and utility metrics before/after reranking.

Assumptions:
- Sex (m/f) is used as the sensitive attribute.
- Since the files do not contain external relevance judgments, the original XING order is used as a utility proxy.

Dependencies:
    pip install pandas numpy
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


# -----------------------------
# Parsing helpers
# -----------------------------

def parse_months(text: Optional[str]) -> float:
    """Parse coarse duration strings into months.

    Examples:
        '3 Jahr, 11 Monat ' -> 47
        '1 Jahr' -> 12
        '5 Monat ' -> 5
        'bis heute' / None / '' -> np.nan
    """
    if not text:
        return float("nan")
    s = str(text).strip().lower()
    if not s or s == "bis heute":
        return float("nan")

    years = 0
    months = 0

    # Very small, robust parser for the strings present in the dataset.
    import re

    y = re.search(r"(\d+)\s*(jahr|jahre|years?|anos?|a\b)", s)
    m = re.search(r"(\d+)\s*(monat|monate|months?|meses?)", s)

    if y:
        years = int(y.group(1))
    if m:
        months = int(m.group(1))

    if not y and not m:
        # Fallback: try a bare integer
        num = re.search(r"(\d+)", s)
        if num:
            return float(int(num.group(1)))
        return float("nan")

    return float(years * 12 + months)


def exposure_weight(rank: int) -> float:
    """Position bias weight used for exposure-based fairness metrics."""
    return 1.0 / math.log2(rank + 1)


# -----------------------------
# Data loading
# -----------------------------

def load_xing_file(path: Union[str, Path]) -> pd.DataFrame:
    """Load one XING JSON query file into a flat dataframe."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows: List[Dict] = []
    for rank, entry in enumerate(data.get("profiles", []), start=1):
        prof = (entry.get("profile") or [{}])[0]
        sex = prof.get("sex")
        jobs = prof.get("jobs") or []
        education = entry.get("education") or []
        awards = entry.get("awards") or []
        languages = entry.get("languages") or []

        # Optional coarse features (useful if you want to extend the experiment later)
        job_months = [parse_months(j.get("jobDuration")) for j in jobs if isinstance(j, dict)]
        edu_months = [parse_months(e.get("eduDuration")) for e in education if isinstance(e, dict)]

        rows.append(
            {
                "candidate_id": f"{path.stem}_{rank}",
                "orig_rank": rank,
                "sex": sex,
                "category": data.get("category"),
                "dominantSexXing": data.get("dominantSexXing"),
                "n_jobs": len(jobs),
                "n_education": len(education),
                "n_awards": len(awards),
                "n_languages": len(languages),
                "job_months_sum": np.nanmean(job_months) if len(job_months) else np.nan,
                "edu_months_sum": np.nanmean(edu_months) if len(edu_months) else np.nan,
                # Utility proxy: higher for better original positions.
                "utility_score": 1.0 / rank,
            }
        )

    df = pd.DataFrame(rows)
    return df


def load_xing_input(path: Union[str, Path]) -> pd.DataFrame:
    """Load one JSON file or a directory of JSON files."""
    path = Path(path)
    if path.is_dir():
        frames = [load_xing_file(p) for p in sorted(path.glob("*.json"))]
        if not frames:
            raise FileNotFoundError(f"No JSON files found in directory: {path}")
        return pd.concat(frames, ignore_index=True)
    return load_xing_file(path)


# -----------------------------
# Fairness metrics
# -----------------------------

def _protected_group(df: pd.DataFrame, sex_col: str = "sex") -> Optional[str]:
    """Use the minority sex in the candidate set as the protected group.

    This keeps the experiment data-driven and avoids hard-coding a sex label.
    """
    counts = df[sex_col].dropna().value_counts()
    if len(counts) < 2:
        return None
    return counts.idxmin()


def group_exposure_metrics(
    order_df: pd.DataFrame,
    sex_col: str = "sex",
    top_k: Optional[int] = None,
    protected_value: Optional[str] = None,
) -> Dict[str, float]:
    """Compute exposure-based metrics for a ranked list."""
    if top_k is None:
        top_k = len(order_df)
    top_k = min(top_k, len(order_df))

    df = order_df.head(top_k).copy()
    if protected_value is None:
        protected_value = _protected_group(order_df, sex_col=sex_col)
    if protected_value is None:
        return {
            "disparate_impact": float("nan"),
            "exposure_gap": float("nan"),
            "rND": float("nan"),
            "protected_share_topk": float("nan"),
            "protected_share_all": float("nan"),
        }

    all_counts = order_df[sex_col].value_counts(dropna=False)
    if protected_value not in all_counts.index:
        return {
            "disparate_impact": float("nan"),
            "exposure_gap": float("nan"),
            "rND": float("nan"),
            "protected_share_topk": float("nan"),
            "protected_share_all": float("nan"),
        }

    unprotected_values = [v for v in all_counts.index if v != protected_value]
    if not unprotected_values:
        return {
            "disparate_impact": float("nan"),
            "exposure_gap": float("nan"),
            "rND": float("nan"),
            "protected_share_topk": float("nan"),
            "protected_share_all": float("nan"),
        }

    # Aggregate exposure by group.
    exp = {protected_value: 0.0, "other": 0.0}
    cnt = {protected_value: 0, "other": 0}
    prot_prefix_exposure = 0.0
    total_prefix_exposure = 0.0
    rnd_num = 0.0
    rnd_den = 0.0

    overall_protected_share = (order_df[sex_col] == protected_value).mean()

    for pos, (_, row) in enumerate(df.iterrows(), start=1):
        w = exposure_weight(pos)
        is_protected = row[sex_col] == protected_value
        if is_protected:
            exp[protected_value] += w
            cnt[protected_value] += 1
        else:
            exp["other"] += w
            cnt["other"] += 1

        total_prefix_exposure += w
        if is_protected:
            prot_prefix_exposure += w

        prefix_share = prot_prefix_exposure / total_prefix_exposure if total_prefix_exposure else 0.0
        rnd_num += abs(prefix_share - overall_protected_share) / math.log2(pos + 1)
        rnd_den += 1.0 / math.log2(pos + 1)

    avg_protected = exp[protected_value] / max(cnt[protected_value], 1)
    avg_other = exp["other"] / max(cnt["other"], 1)

    disparate_impact = avg_protected / avg_other if avg_other > 0 else float("inf")
    exposure_gap = abs(avg_protected - avg_other)
    rnd = rnd_num / rnd_den if rnd_den > 0 else float("nan")

    return {
        "disparate_impact": disparate_impact,
        "exposure_gap": exposure_gap,
        "rND": rnd,
        "protected_share_topk": (df[sex_col] == protected_value).mean(),
        "protected_share_all": overall_protected_share,
    }


def ndcg_at_k(order_df: pd.DataFrame, k: int = 10) -> float:
    """nDCG using the original ranking as a relevance proxy.

    Relevance is defined as a monotonically decreasing function of the original rank,
    so the original order attains nDCG=1.0 by construction.
    """
    k = min(k, len(order_df))
    df = order_df.head(k).copy()

    # Proxy relevance: higher for earlier original ranks.
    rel = np.array([1.0 / r for r in df["orig_rank"].to_list()], dtype=float)

    def dcg(vals: np.ndarray) -> float:
        return float(np.sum((2.0**vals - 1.0) / np.log2(np.arange(2, len(vals) + 2))))

    actual = dcg(rel)
    ideal = dcg(np.sort(rel)[::-1])
    return actual / ideal if ideal > 0 else float("nan")


def mrr_at_k(order_df: pd.DataFrame, k: int = 10, relevant_cutoff: int = 10) -> float:
    """MRR@k using the original top-`relevant_cutoff` items as relevant."""
    k = min(k, len(order_df))
    relevant_ids = set(order_df.loc[order_df["orig_rank"] <= relevant_cutoff, "candidate_id"].tolist())
    for i, (_, row) in enumerate(order_df.head(k).iterrows(), start=1):
        if row["candidate_id"] in relevant_ids:
            return 1.0 / i
    return 0.0


# -----------------------------
# Fairness-aware reranking
# -----------------------------

def fair_rerank_greedy(
    df: pd.DataFrame,
    k: int = 10,
    sex_col: str = "sex",
    protected_value: Optional[str] = None,
    lambda_fair: float = 0.7,
    lambda_util: float = 0.3,
) -> pd.DataFrame:
    """A simple, explainable post-processing reranker.

    At each position, select the candidate minimizing a weighted combination of:
      - deviation from the target protected-group exposure share,
      - loss of utility (based on original rank).

    The target share is the overall protected-group proportion in the candidate set.
    """
    if k <= 0:
        raise ValueError("k must be positive")

    work = df.sort_values("orig_rank", ascending=True).copy().reset_index(drop=True)
    if protected_value is None:
        protected_value = _protected_group(work, sex_col=sex_col)
    if protected_value is None:
        return work.head(k).copy()

    target_share = (work[sex_col] == protected_value).mean()
    remaining = work.copy()
    selected_rows = []
    prot_exp = 0.0
    total_exp = 0.0

    for pos in range(1, min(k, len(work)) + 1):
        pos_exp = exposure_weight(pos)
        best_idx = None
        best_obj = float("inf")

        for idx, row in remaining.iterrows():
            is_prot = row[sex_col] == protected_value
            new_total = total_exp + pos_exp
            new_prot = prot_exp + (pos_exp if is_prot else 0.0)

            fairness_penalty = abs(new_prot - target_share * new_total)
            utility_penalty = 1.0 - float(row["utility_score"])

            # Tie-breaker favors the original order if everything else is equal.
            obj = lambda_fair * fairness_penalty + lambda_util * utility_penalty + 1e-9 * row["orig_rank"]
            if obj < best_obj:
                best_obj = obj
                best_idx = idx

        chosen = remaining.loc[best_idx]
        selected_rows.append(chosen)
        is_prot = chosen[sex_col] == protected_value
        total_exp += pos_exp
        if is_prot:
            prot_exp += pos_exp
        remaining = remaining.drop(index=best_idx)

    return pd.DataFrame(selected_rows).reset_index(drop=True)


# -----------------------------
# Experiment runner
# -----------------------------

def run_experiment(path: Union[str, Path], k: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run baseline vs. reranked evaluation for one JSON file or a directory."""
    df = load_xing_input(path)
    if df.empty:
        raise ValueError("No candidates loaded from input.")

    # Baseline: original order.
    baseline = df.sort_values("orig_rank", ascending=True).reset_index(drop=True)

    # Fairness-aware reranking.
    reranked = fair_rerank_greedy(baseline, k=k)

    # Identify the protected group from the candidate set.
    protected_value = _protected_group(baseline)

    before_f = group_exposure_metrics(baseline, top_k=k, protected_value=protected_value)
    after_f = group_exposure_metrics(reranked, top_k=k, protected_value=protected_value)

    before_u = {
        "nDCG@k": ndcg_at_k(baseline, k=k),
        "MRR@k": mrr_at_k(baseline, k=k, relevant_cutoff=k),
    }
    after_u = {
        "nDCG@k": ndcg_at_k(reranked, k=k),
        "MRR@k": mrr_at_k(reranked, k=k, relevant_cutoff=k),
    }

    before = {**before_f, **before_u}
    after = {**after_f, **after_u}

    metrics = pd.DataFrame(
        [
            {
                "Metric": "Disparate Impact",
                "Original": before["disparate_impact"],
                "Re-ranked": after["disparate_impact"],
                "Delta": after["disparate_impact"] - before["disparate_impact"],
                "Direction": "higher is better",
            },
            {
                "Metric": "Exposure Gap",
                "Original": before["exposure_gap"],
                "Re-ranked": after["exposure_gap"],
                "Delta": after["exposure_gap"] - before["exposure_gap"],
                "Direction": "lower is better",
            },
            {
                "Metric": "rND",
                "Original": before["rND"],
                "Re-ranked": after["rND"],
                "Delta": after["rND"] - before["rND"],
                "Direction": "lower is better",
            },
            {
                "Metric": "nDCG@k",
                "Original": before["nDCG@k"],
                "Re-ranked": after["nDCG@k"],
                "Delta": after["nDCG@k"] - before["nDCG@k"],
                "Direction": "higher is better",
            },
            {
                "Metric": "MRR@k",
                "Original": before["MRR@k"],
                "Re-ranked": after["MRR@k"],
                "Delta": after["MRR@k"] - before["MRR@k"],
                "Direction": "higher is better",
            },
        ]
    )

    workflow = pd.DataFrame(
        [
            {"Reasoning Step": "Application Domain", "Ontology Outcome": baseline.loc[0, "category"]},
            {"Reasoning Step": "AI Type of Use", "Ontology Outcome": "Recommendation"},
            {"Reasoning Step": "AI Task", "Ontology Outcome": "Ranking"},
            {
                "Reasoning Step": "Fairness Concern",
                "Ontology Outcome": "Biased Historical Examples",
            },
            {
                "Reasoning Step": "Fairness Notions",
                "Ontology Outcome": "Statistical Parity; Exposure Fairness",
            },
            {
                "Reasoning Step": "Fairness Metrics",
                "Ontology Outcome": "Disparate Impact; Exposure-Based Metrics; rND",
            },
            {
                "Reasoning Step": "Mitigation Technique",
                "Ontology Outcome": "Fairness-aware re-ranking",
            },
            {
                "Reasoning Step": "Deployment Constraint",
                "Ontology Outcome": "No retraining / black-box setting",
            },
        ]
    )

    return workflow, metrics


# -----------------------------
# CLI
# -----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run XING fairness-aware reranking experiment.")
    parser.add_argument("--input", required=True, help="Path to a JSON file or a directory of JSON files.")
    parser.add_argument("--k", type=int, default=10, help="Top-k cutoff for evaluation.")
    parser.add_argument("--workflow-csv", default=None, help="Optional path to save the workflow table as CSV.")
    parser.add_argument("--metrics-csv", default=None, help="Optional path to save the metrics table as CSV.")
    args = parser.parse_args()

    workflow, metrics = run_experiment(args.input, k=args.k)

    pd.set_option("display.max_colwidth", 120)
    pd.set_option("display.width", 160)

    print("\n=== Ontology-driven workflow ===\n")
    print(workflow.to_string(index=False))

    print("\n=== Fairness / utility metrics (before vs after) ===\n")
    print(metrics.to_string(index=False))

    if args.workflow_csv:
        Path(args.workflow_csv).parent.mkdir(parents=True, exist_ok=True)
        workflow.to_csv(args.workflow_csv, index=False)

    if args.metrics_csv:
        Path(args.metrics_csv).parent.mkdir(parents=True, exist_ok=True)
        metrics.to_csv(args.metrics_csv, index=False)


if __name__ == "__main__":
    main()
