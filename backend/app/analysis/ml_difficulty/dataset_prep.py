"""
Dataset Preparation & Preprocessing Pipeline for Codeforces Difficulty Prediction.

Responsibilities:
- Ingest raw Codeforces dataset.
- Extract official Codeforces difficulty rating (*R).
- Strip out algorithm tags, editorials, and solutions to prevent data leakage.
- Clean text while preserving mathematical formulas, constraints, and variables.
- Split chronologically into Train (70%), Validation/Calibration (15%), and Test (15%).
- Deduplicate across splits.
"""
from __future__ import annotations

import os
import re
import json
from typing import Dict, Tuple, List, Optional
import pandas as pd


def extract_official_rating(tags_str: str) -> Optional[int]:
    """Extracts official Codeforces difficulty rating like *1600 or *2400."""
    if not isinstance(tags_str, str):
        return None
    m = re.search(r"\*(\d+)", tags_str)
    if m:
        r = int(m.group(1))
        if 800 <= r <= 3500:
            return r
    return None


def clean_problem_statement(text: str) -> str:
    """Cleans problem statement text without removing math, variables, or constraints."""
    if not isinstance(text, str):
        return ""
    # Normalize unicode spaces and math symbols
    cleaned = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Collapse excess whitespace while preserving line breaks
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    return "\n".join(lines).strip()


def prepare_dataset(
    raw_csv_path: str,
    output_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> Dict[str, int]:
    """
    Cleans, deduplicates, and chronologically splits Codeforces problems.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(raw_csv_path)

    # 1. Extract official rating
    df["rating"] = df["tags"].apply(extract_official_rating)
    df = df.dropna(subset=["rating"]).copy()
    df["rating"] = df["rating"].astype(int)

    # 2. Clean statements & exclude leakages (drop tags column entirely)
    df["problem_statement"] = df["problem_statement"].apply(clean_problem_statement)
    df["input"] = df["input"].fillna("").astype(str)
    df["output"] = df["output"].fillna("").astype(str)
    df["time_limit"] = df["time_limit"].fillna("").astype(str)
    df["memory_limit"] = df["memory_limit"].fillna("").astype(str)

    # Remove the tags column to prevent data leakage
    df = df.drop(columns=["tags"])

    # 3. Deduplicate by problem statement
    df = df.drop_duplicates(subset=["problem_statement"]).reset_index(drop=True)

    # 4. Chronological split:
    # Since the raw data is ordered newest to oldest, reverse to oldest -> newest
    df_chronological = df.iloc[::-1].reset_index(drop=True)

    n_total = len(df_chronological)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_df = df_chronological.iloc[:n_train].copy()
    val_df = df_chronological.iloc[n_train : n_train + n_val].copy()
    test_df = df_chronological.iloc[n_train + n_val :].copy()

    # Save to disk
    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    summary = {
        "total_rated": n_total,
        "train_count": len(train_df),
        "val_calibration_count": len(val_df),
        "test_count": len(test_df),
        "rating_min": int(df["rating"].min()),
        "rating_max": int(df["rating"].max()),
        "rating_mean": float(round(df["rating"].mean(), 2)),
    }

    summary_path = os.path.join(output_dir, "dataset_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("Dataset prepared successfully:")
    print(f"  Train: {len(train_df)} | Val/Calibration: {len(val_df)} | Test: {len(test_df)}")
    return summary


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    raw_path = os.path.join(base_dir, "data", "codeforces_raw.csv")
    data_dir = os.path.join(base_dir, "data")
    prepare_dataset(raw_path, data_dir)
