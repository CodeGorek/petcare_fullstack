from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets

from .forms import LoteMedicamentoForm
from .models import LoteMedicamento
from .serializers import LoteMedicamentoSerializer
from .services import asegurar_catalogo_fefo_inicial


@login_required
def farmacia_fefo(request):
    asegurar_catalogo_fefo_inicial()
    lotes = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    form = LoteMedicamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lote registrado y ordenado automáticamente según Norma FEFO.')
        return redirect('farmacia_fefo')
    return render(request, 'clinica/farmacia_fefo.html', {'lotes': lotes, 'form': form})


@login_required
def ajustar_stock_lote(request, pk, accion):
    lote = get_object_or_404(LoteMedicamento, pk=pk)
    if request.method == 'POST':
        if accion == 'dispensar':
            if lote.esta_vencido:
                messages.error(request, f'Norma FEFO: El lote {lote.codigo_lote} está vencido y bloqueado.')
            elif lote.stock_disponible > 0:
                lote.stock_disponible -= 1
                lote.save(update_fields=['stock_disponible'])
                messages.success(request, f'Se dispensó 1 u. de {lote.nombre} (Lote FEFO: {lote.codigo_lote}).')
        elif accion == 'sumar':
            lote.stock_disponible += 5
            lote.save(update_fields=['stock_disponible'])
            messages.info(request, f'Se agregaron +5 u. al lote {lote.codigo_lote}.')
    return redirect('farmacia_fefo')


class LoteMedicamentoViewSet(viewsets.ModelViewSet):
    queryset = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    serializer_class = LoteMedicamentoSerializer
