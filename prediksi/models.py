from django.db import models


class Riwayat(models.Model):
    """Menyimpan setiap prediksi yang pernah dibuat pengguna."""

    jarak_km = models.FloatField()
    rating = models.FloatField()
    ac = models.CharField(max_length=5)
    harga_prediksi = models.FloatField(help_text="dalam ribu rupiah / bulan")
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name_plural = "riwayat"

    def __str__(self):
        return f"{self.jarak_km} km, rating {self.rating}, AC {self.ac} -> Rp {self.harga_prediksi:.0f} rb"
