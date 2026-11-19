"""Melatih model & menyimpannya dengan joblib (Kegiatan 2 pada modul).

Jalankan dari folder utama proyek:  python ml/train_model.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

BASE = Path(__file__).resolve().parent.parent

df = pd.read_csv(BASE / "data" / "kos_madiun.csv")
df["ac_num"] = df["ac"].map({"ya": 1, "tidak": 0})

X = df[["jarak_km", "rating", "ac_num"]]
y = df["harga"]
model = LinearRegression().fit(X, y)

joblib.dump(model, BASE / "model" / "model_kos.joblib")
print("Model tersimpan! Koefisien:", model.coef_.round(1), "| intercept:", round(model.intercept_, 1))
print("R^2 pada data latih:", round(model.score(X, y), 3))
