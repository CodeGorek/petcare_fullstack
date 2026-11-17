from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from agenda.models import CitaMedica, FichaClinica, RecordatorioVacuna
from farmacia.models import LoteMedicamento
from farmacia.services import asegurar_catalogo_fefo_inicial
from pacientes.models import Mascota, Tutor


@login_required
def dashboard(request):
    asegurar_catalogo_fefo_inicial()
    hoy = date.today()
    citas_hoy = (
        CitaMedica.objects.filter(fecha=hoy)
        .select_related('mascota', 'mascota__tutor', 'veterinario')
        .order_by('hora')
    )
    recordatorios_todos = (
        RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor')
        .filter(mascota__activo=True)
        .order_by('fecha_programada', 'hora_programada')
    )
    lotes_alerta_fefo = LoteMedicamento.objects.filter(
        activo=True, fecha_vencimiento__lte=hoy + timedelta(days=45)
    ).order_by('fecha_vencimiento')
    lotes_inventario = LoteMedicamento.objects.filter(activo=True).order_by('fecha_vencimiento')[:8]

    context = {
        'total_tutores': Tutor.objects.filter(activo=True).count(),
        'total_mascotas': Mascota.objects.filter(activo=True).count(),
        'citas_hoy_count': citas_hoy.count(),
        'citas_hoy': citas_hoy,
        'recordatorios_agenda': recordatorios_todos[:6],
        'lotes_alerta_fefo': lotes_alerta_fefo,
        'lotes_inventario': lotes_inventario,
        'ultimas_fichas': FichaClinica.objects.select_related(
            'mascota', 'veterinario', 'cita', 'medicamento_fefo'
        )[:5],
    }
    return render(request, 'clinica/dashboard.html', context)


def _metricas_payload():
    especies = list(Mascota.objects.filter(activo=True).values('especie').annotate(total=Count('id')))
    estados_citas = list(CitaMedica.objects.values('estado').annotate(total=Count('id')))
    return {
        'resumen': {
            'tutores_activos': Tutor.objects.filter(activo=True).count(),
            'mascotas_activas': Mascota.objects.filter(activo=True).count(),
            'citas_hoy': CitaMedica.objects.filter(fecha=date.today()).count(),
            'lotes_por_vencer': LoteMedicamento.objects.filter(
                activo=True, fecha_vencimiento__lte=date.today() + timedelta(days=45)
            ).count(),
        },
        'especies': especies,
        'estados_citas': estados_citas,
    }


@login_required
def api_metricas_dashboard(request):
    return JsonResponse(_metricas_payload())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_metricas_drf(request):
    """Expose clinical dashboard metrics to token-authenticated frontend clients."""
    return Response(_metricas_payload())


def health_check(request):
    """Lightweight health probe for API Gateway, load balancers, and EC2 checks."""
    return JsonResponse({
        'status': 'ok',
        'service': 'petcare-backend',
        'modules': ['nucleo', 'usuarios', 'pacientes', 'agenda', 'farmacia', 'cobros'],
    })


def error_404_view(request, exception=None, ruta_invalida=None):
    return render(request, '404.html', {'ruta_solicitada': ruta_invalida}, status=404)


def error_403_view(request, exception=None):
    return render(request, '403.html', status=403)
