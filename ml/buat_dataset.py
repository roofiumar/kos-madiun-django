"""Membuat dataset SINTETIS kos_madiun.csv (harga dalam ribu rupiah / bulan).

Gunakan file ini hanya jika kamu tidak punya kos_madiun.csv asli dari praktikum P8.
Jika sudah punya, taruh file aslinya di data/kos_madiun.csv (kolom: jarak_km, rating, ac, harga).
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 60
jarak = rng.uniform(0.3, 5.0, n).round(1)
rating = rng.uniform(3.0, 5.0, n).round(1)
ac = rng.choice(["ya", "tidak"], n)
harga = 300 - 28.5 * jarak + 27.1 * rating + 7.4 * (ac == "ya") + rng.normal(0, 25, n)

df = pd.DataFrame({"jarak_km": jarak, "rating": rating, "ac": ac, "harga": harga.round(0).astype(int)})
out = Path(__file__).resolve().parent.parent / "data" / "kos_madiun.csv"
df.to_csv(out, index=False)
print("Dataset dibuat:", out, df.shape)
