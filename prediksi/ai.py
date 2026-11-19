"""Penjelasan hasil prediksi memakai AI (Groq atau Gemini) dengan fallback lokal.

API key TIDAK ditulis di kode. Key dibaca dari environment variable / file .env:
  GROQ_API_KEY   atau   GEMINI_API_KEY
Pilih penyedia lewat AI_PROVIDER=groq|gemini (opsional).
"""
import json
import os
import urllib.error
import urllib.request

WAKTU_TUNGGU = 20  # detik

PETUNJUK = (
    "Kamu asisten yang menjelaskan hasil prediksi harga sewa kos di Madiun kepada mahasiswa. "
    "Jawab dalam bahasa Indonesia, 3 sampai 4 kalimat, ringkas dan jelas. "
    "Gunakan hanya data yang diberikan dan jangan mengarang angka. "
    "Satuan harga adalah ribu rupiah per bulan. "
    "Jika R kuadrat model rendah (di bawah 0,3), sebutkan dengan jujur bahwa prediksi ini kurang akurat."
)


def _penyedia():
    pilihan = os.environ.get("AI_PROVIDER", "").strip().lower()
    ada = {
        "groq": bool(os.environ.get("GROQ_API_KEY", "").strip()),
        "gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
    }
    if pilihan in ada:
        return pilihan if ada[pilihan] else None
    for nama in ("groq", "gemini"):
        if ada[nama]:
            return nama
    return None


def _susun_prompt(k):
    mirip = "; ".join(
        f'{x["nama"]} ({x["jarak_km"]} km, rating {x["rating"]}, AC {x["ac"]}, Rp {x["harga"]} rb)'
        for x in k.get("kos_mirip", [])
    )
    rata_ac = ", ".join(f'AC {x["ac"]}: Rp {x["rata"]} rb' for x in k.get("rata_ac", []))
    return (
        f'Input pengguna: jarak {k["jarak_km"]} km, rating {k["rating"]}, AC {k["ac"]}.\n'
        f'Prediksi model: Rp {k["harga_prediksi"]} ribu per bulan.\n'
        f'Model regresi linear: harga = {k["intercept"]} + ({k["koef_jarak"]} x jarak) '
        f'+ ({k["koef_rating"]} x rating) + ({k["koef_ac"]} x AC, ya=1 tidak=0).\n'
        f'R kuadrat model pada data: {k["r2"]}.\n'
        f'Rata-rata harga seluruh data: Rp {k["rata_harga"]} rb. Rata-rata per AC: {rata_ac}.\n'
        f'Tiga kos nyata yang paling mirip: {mirip}.\n'
        "Jelaskan hasil prediksi ini, bandingkan dengan kos yang mirip, dan sebutkan keterbatasannya."
    )


def _fallback_lokal(k, alasan):
    """Susun penjelasan ringkas berbasis data konteks saat AI tidak tersedia."""
    harga_pred = k.get("harga_prediksi", "-")
    rata_harga = k.get("rata_harga")
    r2 = k.get("r2")
    mirip_list = k.get("kos_mirip") or []

    kalimat_1 = (
        f"Perkiraan sewa untuk jarak {k.get('jarak_km')} km, rating {k.get('rating')}, "
        f"dan AC '{k.get('ac')}' adalah Rp {harga_pred} ribu per bulan"
    )
    if rata_harga is not None:
        kalimat_1 += f" (rata-rata keseluruhan data Rp {rata_harga} ribu per bulan)."
    else:
        kalimat_1 += "."

    if mirip_list:
        contoh = ", ".join(
            f"{x['nama']} (Rp {x['harga']} rb, {x['jarak_km']} km, rating {x['rating']})"
            for x in mirip_list[:2]
        )
        kalimat_2 = f"Kos terdekat secara karakteristik antara lain {contoh}."
    else:
        kalimat_2 = "Perbandingan kos serupa belum tersedia pada data saat ini."

    catatan_r2 = ""
    try:
        if r2 is not None and float(r2) < 0.3:
            catatan_r2 = f" Nilai R kuadrat model ({r2}) tergolong rendah sehingga prediksi ini kurang akurat."
        elif r2 is not None:
            catatan_r2 = f" Nilai R kuadrat model pada data adalah {r2}."
    except (TypeError, ValueError):
        catatan_r2 = ""

    kalimat_3 = f"Catatan: {alasan}.{catatan_r2}".strip()
    return "\n".join([kalimat_1, kalimat_2, kalimat_3])


def _kirim(url, headers, badan):
    permintaan = urllib.request.Request(
        url,
        data=json.dumps(badan).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "kosmadiun-django/1.0", **headers},
        method="POST",
    )
    with urllib.request.urlopen(permintaan, timeout=WAKTU_TUNGGU) as respons:
        return json.loads(respons.read().decode("utf-8"))


def _panggil_groq(prompt):
    data = _kirim(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": "Bearer " + os.environ["GROQ_API_KEY"].strip()},
        {
            "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
            "messages": [{"role": "system", "content": PETUNJUK}, {"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 500,
        },
    )
    return data["choices"][0]["message"]["content"].strip()


def _panggil_gemini(prompt):
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro").strip()
    data = _kirim(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"x-goog-api-key": os.environ["GEMINI_API_KEY"].strip()},
        {
            "system_instruction": {"parts": [{"text": PETUNJUK}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 900},
        },
    )
    bagian = data["candidates"][0]["content"]["parts"]
    return "".join(b.get("text", "") for b in bagian).strip()


def jelaskan(konteks):
    """Kembalikan (teks, None) baik dari LLM maupun fallback lokal agar UI tetap informatif."""
    penyedia = _penyedia()
    if penyedia is None:
        return _fallback_lokal(konteks, "Mode ringkasan otomatis aktif karena API key Groq/Gemini belum diatur"), None

    try:
        prompt = _susun_prompt(konteks)
        teks = _panggil_groq(prompt) if penyedia == "groq" else _panggil_gemini(prompt)
        if not teks:
            return _fallback_lokal(konteks, "Mode ringkasan otomatis aktif karena respon AI kosong"), None
        return teks, None
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            alasan = "Mode ringkasan otomatis aktif karena API key ditolak"
        elif e.code == 404:
            alasan = "Mode ringkasan otomatis aktif karena model AI tidak ditemukan"
        elif e.code == 429:
            alasan = "Mode ringkasan otomatis aktif karena batas permintaan AI tercapai"
        else:
            alasan = f"Mode ringkasan otomatis aktif (galat layanan AI {e.code})"
        return _fallback_lokal(konteks, alasan), None
    except urllib.error.URLError:
        return _fallback_lokal(konteks, "Mode ringkasan otomatis aktif karena koneksi ke layanan AI gagal"), None
    except (KeyError, IndexError, ValueError, TimeoutError):
        return _fallback_lokal(konteks, "Mode ringkasan otomatis aktif karena format respon AI tidak sesuai"), None