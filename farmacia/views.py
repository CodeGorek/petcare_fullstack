from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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

    @action(detail=False, methods=['get'], url_path='buscar-codigo')
    def buscar_codigo(self, request):
        """Search lots by barcode, lot code, or medication name and return total FEFO stock and price."""
        codigo = (request.query_params.get('codigo') or '').strip()
        if not codigo:
            return Response({'encontrado': False, 'total_stock': 0, 'precio_unitario': None, 'lotes': []})

        lotes = LoteMedicamento.objects.filter(
            Q(codigo_barras__iexact=codigo) | Q(codigo_lote__iexact=codigo)
        ).order_by('fecha_vencimiento')
        if not lotes.exists():
            lotes = LoteMedicamento.objects.filter(
                Q(codigo_barras__icontains=codigo) | Q(codigo_lote__icontains=codigo) | Q(nombre__icontains=codigo)
            ).order_by('fecha_vencimiento')

        serializados = self.get_serializer(lotes, many=True).data
        activos_vigentes = [l for l in lotes if l.activo and not l.esta_vencido]
        total_stock = sum(l.stock_disponible for l in activos_vigentes)
        precio_ref = next((l.precio_unitario for l in lotes if l.precio_unitario), None)

        return Response({
            'encontrado': len(serializados) > 0,
            'codigo_consultado': codigo,
            'total_stock': total_stock,
            'precio_unitario': precio_ref,
            'lotes': serializados,
        })
