from django import forms
from .forms import BootstrapFormMixin
from .models import ServicioClinico, LoteMedicamento


class ServicioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ServicioClinico
        fields = ['nombre', 'precio', 'activo']


class PrecioMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['precio_unitario']


class ServicioCuentaForm(BootstrapFormMixin, forms.Form):
    servicio = forms.ModelChoiceField(queryset=ServicioClinico.objects.none())
    cantidad = forms.IntegerField(min_value=1, max_value=100, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicio'].queryset = ServicioClinico.objects.filter(activo=True)
