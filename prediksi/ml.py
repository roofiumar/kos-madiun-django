"""Pemuatan model & data. Model dimuat SEKALI (setara @st.cache_resource di Streamlit)."""
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

# Urutan kolom HARUS sama persis dengan saat model dilatih (ml/train_model.py).
FITUR = ["jarak_km", "rating", "ac_num"]


@lru_cache(maxsize=1)
def muat_model():
    return joblib.load(settings.MODEL_PATH)


@lru_cache(maxsize=1)
def muat_data():
    return pd.read_csv(settings.DATA_PATH)


def prediksi_harga(jarak_km, rating, ac):
    data_baru = pd.DataFrame({
        "jarak_km": [jarak_km],
        "rating": [rating],
        "ac_num": [1 if ac == "ya" else 0],
    })[FITUR]
    harga = float(muat_model().predict(data_baru)[0])
    return max(harga, 0.0)  # harga tidak boleh negatif


def rata_harga_per_ac():
    df = muat_data()
    rata = df.groupby("ac")["harga"].mean().round(0)
    return [{"ac": k, "rata": int(v)} for k, v in rata.items()]


def rata_harga_per_jarak():
    """Rata-rata harga per rentang jarak ke kampus."""
    df = muat_data().copy()
    df["rentang"] = pd.cut(df["jarak_km"], bins=[0, 1, 2, 3, 5],
                           labels=["0-1 km", "1-2 km", "2-3 km", "3-5 km"])
    rata = df.groupby("rentang", observed=True)["harga"].mean().round(0)
    return [{"rentang": str(k), "rata": int(v)} for k, v in rata.items()]


def daftar_kos(ac="semua", maks_harga=None, urut="harga_naik"):
    """Daftar kos dari CSV, dengan filter AC, batas harga, dan urutan."""
    df = muat_data().copy()
    if "nama" not in df.columns:
        df["nama"] = [f"Kos {i + 1}" for i in range(len(df))]
    if ac in ("ya", "tidak"):
        df = df[df["ac"] == ac]
    if maks_harga is not None:
        df = df[df["harga"] <= maks_harga]
    kunci = {
        "harga_naik": ("harga", True),
        "harga_turun": ("harga", False),
        "jarak": ("jarak_km", True),
        "rating": ("rating", False),
    }
    kolom, naik = kunci.get(urut, kunci["harga_naik"])
    df = df.sort_values(kolom, ascending=naik, kind="stable")
    return df[["nama", "jarak_km", "rating", "ac", "harga"]].to_dict("records")


def konteks_penjelasan(jarak_km, rating, ac, harga_prediksi):
    """Kumpulkan fakta dari model & data untuk dijelaskan oleh AI."""
    model = muat_model()
    df = muat_data().copy()
    df["ac_num"] = df["ac"].map({"ya": 1, "tidak": 0})
    if "nama" not in df.columns:
        df["nama"] = [f"Kos {i + 1}" for i in range(len(df))]

    r2 = float(model.score(df[FITUR], df["harga"]))
    rentang_j = (df["jarak_km"].max() - df["jarak_km"].min()) or 1
    rentang_r = (df["rating"].max() - df["rating"].min()) or 1
    jauh = ((df["jarak_km"] - jarak_km) / rentang_j) ** 2 + ((df["rating"] - rating) / rentang_r) ** 2
    mirip = df.loc[jauh.nsmallest(3).index, ["nama", "jarak_km", "rating", "ac", "harga"]].to_dict("records")

    koef = [float(x) for x in model.coef_]
    return {
        "jarak_km": float(jarak_km), "rating": float(rating), "ac": ac,
        "harga_prediksi": round(float(harga_prediksi)),
        "koef_jarak": round(koef[0], 1), "koef_rating": round(koef[1], 1), "koef_ac": round(koef[2], 1),
        "intercept": round(float(model.intercept_), 1),
        "r2": round(r2, 3),
        "rata_harga": round(float(df["harga"].mean())),
        "rata_ac": rata_harga_per_ac(),
        "kos_mirip": mirip,
    }
