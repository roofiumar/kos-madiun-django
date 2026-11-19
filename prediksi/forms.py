from django import forms

PILIHAN_AC = [("ya", "Ya, ada AC"), ("tidak", "Tidak ada AC")]


class PrediksiForm(forms.Form):
    jarak_km = forms.FloatField(
        label="Jarak ke kampus (km)", min_value=0.3, max_value=5.0, initial=1.0,
        widget=forms.NumberInput(attrs={"step": "0.1", "min": "0.3", "max": "5.0"}),
        error_messages={"min_value": "Jarak minimal 0,3 km.", "max_value": "Jarak maksimal 5 km."},
    )
    rating = forms.FloatField(
        label="Rating kos (3,0 sampai 5,0)", min_value=3.0, max_value=5.0, initial=4.0,
        widget=forms.NumberInput(attrs={"step": "0.1", "min": "3.0", "max": "5.0"}),
        error_messages={"min_value": "Rating minimal 3,0.", "max_value": "Rating maksimal 5,0."},
    )
    ac = forms.ChoiceField(label="Fasilitas AC", choices=PILIHAN_AC, initial="ya",
                           widget=forms.RadioSelect)
