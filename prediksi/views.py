from django.shortcuts import render

from .ai import jelaskan
from .forms import PrediksiForm
from .ml import daftar_kos, konteks_penjelasan, prediksi_harga, rata_harga_per_ac, rata_harga_per_jarak
from .models import Riwayat


def _angka(teks):
    """Ubah teks jadi angka; kembalikan None jika kosong atau tidak valid."""
    try:
        return float(teks.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def index(request):
    hasil = None
    penjelasan = None
    if request.method == "POST":
        form = PrediksiForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            harga = prediksi_harga(d["jarak_km"], d["rating"], d["ac"])
            Riwayat.objects.create(jarak_km=d["jarak_km"], rating=d["rating"],
                                   ac=d["ac"], harga_prediksi=harga)
            hasil = {"harga": round(harga), "input": d}
            teks, galat = jelaskan(konteks_penjelasan(d["jarak_km"], d["rating"], d["ac"], harga))
            penjelasan = {"teks": teks, "galat": galat}
    else:
        form = PrediksiForm()

    grafik = rata_harga_per_ac()
    maks = max((g["rata"] for g in grafik), default=1)
    for g in grafik:
        g["persen"] = round(g["rata"] / maks * 100)

    grafik_jarak = rata_harga_per_jarak()
    maks_j = max((g["rata"] for g in grafik_jarak), default=1)
    for g in grafik_jarak:
        g["persen"] = round(g["rata"] / maks_j * 100)

    # Filter daftar kos (lewat GET, terpisah dari form prediksi)
    f_ac = request.GET.get("ac", "semua")
    f_urut = request.GET.get("urut", "harga_naik")
    f_maks = request.GET.get("maks_harga", "").strip()
    kos_list = daftar_kos(f_ac, _angka(f_maks), f_urut)

    return render(request, "prediksi/index.html", {
        "form": form,
        "hasil": hasil,
        "penjelasan": penjelasan,
        "grafik": grafik,
        "grafik_jarak": grafik_jarak,
        "kos_list": kos_list,
        "f": {"ac": f_ac, "urut": f_urut, "maks_harga": f_maks},
        "riwayat": Riwayat.objects.all()[:5],
    })
