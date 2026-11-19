# Prediksi Harga Kos Madiun (Django)

Tugas individu Sistem Cerdas (TI24317), Pertemuan 14: deployment model ML ke aplikasi web.
Versi Django dari aplikasi Streamlit `app_kos.py` pada modul.

## Deskripsi
Pengguna mengisi **jarak ke kampus (km)**, **rating kos**, dan **fasilitas AC**. Aplikasi memuat model
`LinearRegression` (disimpan dengan `joblib`) lalu menampilkan perkiraan harga sewa per bulan
(dalam ribu rupiah). Halaman juga menampilkan grafik rata-rata harga per kategori AC dan 5 riwayat prediksi terakhir.

Alur: `data/kos_madiun.csv` -> `ml/train_model.py` -> `model/model_kos.joblib` -> Django (`prediksi/ml.py`) -> pengguna di browser.

## Cara menjalankan
```bash
pip install -r requirements.txt

# 1) (Opsional) jika belum punya kos_madiun.csv asli dari P8, buat dataset sintetis:
python ml/buat_dataset.py

# 2) Latih & simpan model (hasil: model/model_kos.joblib)
python ml/train_model.py

# 3) Siapkan database riwayat & jalankan server
python manage.py migrate
python manage.py runserver
```
Buka http://127.0.0.1:8000/ . Jalankan tes: `python manage.py test`.

> Gunakan versi scikit-learn yang sama saat melatih dan saat menjalankan aplikasi,
> agar model `.joblib` dapat dimuat tanpa peringatan.

## Struktur
```
kos_project/    pengaturan & URL Django
prediksi/       app: forms.py, views.py, models.py (Riwayat), ml.py (muat model), templates, static
ml/             train_model.py, buat_dataset.py
data/           kos_madiun.csv
model/          model_kos.joblib
```

## Padanan Streamlit -> Django
| Streamlit | Django |
|---|---|
| `@st.cache_resource` | `@lru_cache` pada `muat_model()` di `prediksi/ml.py` |
| `st.slider`, `st.selectbox` | `forms.py` (`FloatField` dengan batas, `ChoiceField`) |
| `if st.button(...)` | `if request.method == "POST"` di `views.py` |
| `st.success(...)` | blok `{% if hasil %}` di `index.html` |
| `st.bar_chart` | batang CSS dari `rata_harga_per_ac()` |

## Aturan emas deployment
Kolom input harus **persis** seperti saat training: `jarak_km`, `rating`, `ac_num` (urutan sama, `ya`=1, `tidak`=0).
Lihat `FITUR` di `prediksi/ml.py`.

## Dataset
- Sumber: `data/kos_madiun.csv`. Berkas bawaan proyek ini **sintetis** (dibuat `ml/buat_dataset.py`, seed 42), bukan data kos nyata.
- Lisensi: bebas dipakai untuk pembelajaran. Ganti dengan dataset asli dari P8 dan cantumkan sumber serta lisensinya di sini.
- Satuan `harga`: ribu rupiah per bulan.

## Pembuat dan pembagian tugas
Dikerjakan **individu** oleh: _(isi nama & NIM)_. Seluruh bagian (data, model, backend Django, tampilan, tes, dokumentasi) dikerjakan sendiri.
