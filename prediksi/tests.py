from django.test import TestCase
from django.urls import reverse

from .models import Riwayat


class PrediksiTest(TestCase):
    def test_halaman_terbuka(self):
        r = self.client.get(reverse("index"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Prediksi Harga Kos Madiun")

    def test_prediksi_valid(self):
        r = self.client.post(reverse("index"), {"jarak_km": 1.0, "rating": 4.0, "ac": "ya"})
        self.assertContains(r, "per bulan")
        self.assertEqual(Riwayat.objects.count(), 1)

    def test_makin_jauh_makin_murah(self):
        dekat = self.client.post(reverse("index"), {"jarak_km": 0.5, "rating": 4.0, "ac": "ya"})
        jauh = self.client.post(reverse("index"), {"jarak_km": 4.5, "rating": 4.0, "ac": "ya"})
        h_dekat, h_jauh = [r.context["hasil"]["harga"] for r in (dekat, jauh)]
        self.assertGreater(h_dekat, h_jauh)

    def test_input_di_luar_batas_ditolak(self):
        r = self.client.post(reverse("index"), {"jarak_km": 99, "rating": 4.0, "ac": "ya"})
        self.assertContains(r, "Jarak maksimal 5 km.")
        self.assertEqual(Riwayat.objects.count(), 0)

    def test_input_kosong_ditolak(self):
        r = self.client.post(reverse("index"), {})
        self.assertEqual(Riwayat.objects.count(), 0)
        self.assertEqual(r.status_code, 200)

    def test_grafik_jarak_tampil(self):
        r = self.client.get(reverse("index"))
        self.assertContains(r, "Rata-rata harga per jarak ke kampus")
        self.assertTrue(len(r.context["grafik_jarak"]) >= 1)

    def test_daftar_kos_tampil(self):
        r = self.client.get(reverse("index"))
        self.assertGreater(len(r.context["kos_list"]), 0)
        self.assertContains(r, "Daftar kos")

    def test_filter_ac_dan_harga(self):
        r = self.client.get(reverse("index"), {"ac": "ya", "maks_harga": "900", "urut": "harga_naik"})
        daftar = r.context["kos_list"]
        self.assertTrue(all(k["ac"] == "ya" and k["harga"] <= 900 for k in daftar))
        harga = [k["harga"] for k in daftar]
        self.assertEqual(harga, sorted(harga))

    def test_filter_tidak_valid_tidak_error(self):
        r = self.client.get(reverse("index"), {"ac": "xx", "maks_harga": "abc", "urut": "zzz"})
        self.assertEqual(r.status_code, 200)

    def test_filter_tanpa_hasil(self):
        r = self.client.get(reverse("index"), {"maks_harga": "1"})
        self.assertEqual(len(r.context["kos_list"]), 0)
        self.assertContains(r, "Tidak ada kos yang cocok")


import os
import urllib.error
from unittest.mock import patch

from . import ai
from .ml import konteks_penjelasan


class AITest(TestCase):
    def setUp(self):
        self.k = konteks_penjelasan(1.0, 4.0, "ya", 1099)

    def test_konteks_lengkap(self):
        self.assertEqual(len(self.k["kos_mirip"]), 3)
        self.assertIn("r2", self.k)

    def test_tanpa_key(self):
        with patch.dict(os.environ, {}, clear=True):
            teks, galat = ai.jelaskan(self.k)
        self.assertIsNone(teks)
        self.assertIn("API key", galat)

    def test_groq_berhasil(self):
        resp = {"choices": [{"message": {"content": "Penjelasan uji."}}]}
        env = {"GROQ_API_KEY": "gsk_uji", "AI_PROVIDER": "groq"}
        with patch.dict(os.environ, env, clear=True), patch("prediksi.ai._kirim", return_value=resp) as m:
            teks, galat = ai.jelaskan(self.k)
        self.assertEqual(teks, "Penjelasan uji.")
        url, headers, badan = m.call_args[0]
        self.assertIn("api.groq.com", url)
        self.assertEqual(headers["Authorization"], "Bearer gsk_uji")
        self.assertEqual(badan["messages"][0]["role"], "system")

    def test_gemini_berhasil(self):
        resp = {"candidates": [{"content": {"parts": [{"text": "Halo "}, {"text": "uji."}]}}]}
        env = {"GEMINI_API_KEY": "kunci_uji", "AI_PROVIDER": "gemini"}
        with patch.dict(os.environ, env, clear=True), patch("prediksi.ai._kirim", return_value=resp) as m:
            teks, galat = ai.jelaskan(self.k)
        self.assertEqual(teks, "Halo uji.")
        url, headers, badan = m.call_args[0]
        self.assertIn("generativelanguage.googleapis.com", url)
        self.assertEqual(headers["x-goog-api-key"], "kunci_uji")

    def test_galat_http_ramah(self):
        env = {"GROQ_API_KEY": "gsk_uji"}
        for kode, kata in ((401, "ditolak"), (404, "tidak ditemukan"), (429, "Batas")):
            err = urllib.error.HTTPError("http://x", kode, "x", {}, None)
            with patch.dict(os.environ, env, clear=True), patch("prediksi.ai._kirim", side_effect=err):
                teks, galat = ai.jelaskan(self.k)
            self.assertIsNone(teks)
            self.assertIn(kata, galat)

    def test_key_tidak_bocor_di_pesan(self):
        err = urllib.error.HTTPError("http://x", 500, "x", {}, None)
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_rahasia"}, clear=True), patch("prediksi.ai._kirim", side_effect=err):
            teks, galat = ai.jelaskan(self.k)
        self.assertNotIn("gsk_rahasia", galat)

    def test_view_menampilkan_penjelasan(self):
        with patch("prediksi.views.jelaskan", return_value=("Teks dari AI.", None)):
            r = self.client.post(reverse("index"), {"jarak_km": 1.0, "rating": 4.0, "ac": "ya"})
        self.assertContains(r, "Teks dari AI.")

    def test_view_tanpa_key_tetap_jalan(self):
        with patch.dict(os.environ, {}, clear=True):
            r = self.client.post(reverse("index"), {"jarak_km": 1.0, "rating": 4.0, "ac": "ya"})
        self.assertContains(r, "per bulan")
        self.assertContains(r, "belum aktif")
