from datetime import date, datetime, timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import CitaMedicaForm, FichaClinicaForm, RecordatorioVacunaForm
from .models import CitaMedica, FichaClinica, RecordatorioVacuna, Veterinario
from .serializers import (
    CitaMedicaSerializer,
    FichaClinicaSerializer,
    RecordatorioVacunaSerializer,
    VeterinarioSerializer,
)


@login_required
def agenda_citas(request):
    citas = CitaMedica.objects.select_related('mascota', 'mascota__tutor', 'veterinario').all()
    veterinarios = Veterinario.objects.filter(activo=True)
    form = CitaMedicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita agendada correctamente sin conflictos de horario.')
        return redirect('agenda_citas')

    return render(request, 'clinica/agenda_citas.html', {
        'citas': citas,
        'veterinarios': veterinarios,
        'form': form,
    })


@login_required
def editar_cita(request, pk):
    cita = get_object_or_404(CitaMedica, pk=pk)
    form = CitaMedicaForm(request.POST or None, instance=cita)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita médica reprogramada/actualizada.')
        return redirect('agenda_citas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Cita #{cita.id} - {cita.mascota.nombre}'})


@login_required
def cambiar_estado_cita(request, pk, nuevo_estado):
    cita = get_object_or_404(CitaMedica, pk=pk)
    if request.method == 'POST' and nuevo_estado in ('ASISTIO', 'NO_ASISTIO', 'CANCELADA'):
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])
        messages.info(request, f'Estado de cita actualizado a: {cita.get_estado_display()}.')
    return redirect('agenda_citas')


def _calcular_disponibilidad(vet_id, fecha_str):
    if not vet_id or not fecha_str:
        return {'bloques': []}

    vet = get_object_or_404(Veterinario, pk=vet_id)
    ocupadas = set(
        CitaMedica.objects.filter(veterinario=vet, fecha=fecha_str)
        .exclude(estado__in=['CANCELADA', 'NO_ASISTIO'])
        .values_list('hora', flat=True)
    )

    bloques = []
    actual = datetime.combine(date.today(), vet.hora_inicio)
    limite = datetime.combine(date.today(), vet.hora_fin)
    while actual < limite:
        hora_bloque = actual.time()
        bloques.append({
            'hora': hora_bloque.strftime('%H:%M'),
            'disponible': hora_bloque not in ocupadas
        })
        actual += timedelta(minutes=30)

    return {
        'veterinario': vet.nombre,
        'especialidad': vet.get_especialidad_display(),
        'bloques': bloques
    }


@login_required
def api_disponibilidad_veterinario(request):
    return JsonResponse(_calcular_disponibilidad(request.GET.get('veterinario_id'), request.GET.get('fecha')))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_disponibilidad_drf(request):
    """Expose veterinarian slot availability for decoupled API clients."""
    return Response(_calcular_disponibilidad(request.GET.get('veterinario_id'), request.GET.get('fecha')))


@login_required
def fichas_clinicas(request):
    fichas = FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'veterinario', 'cita', 'medicamento_fefo').all()
    form = FichaClinicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ficha = form.save()
        msg_fefo = f" y se descontaron {ficha.cantidad_dispensada} u. del lote FEFO {ficha.medicamento_fefo.codigo_lote}" if ficha.medicamento_fefo else ""
        messages.success(request, f'Ficha clínica #{ficha.id} emitida{msg_fefo}.')
        return redirect('fichas_clinicas')

    return render(request, 'clinica/fichas_clinicas.html', {'fichas': fichas, 'form': form})


@login_required
def imprimir_ficha_individual(request, pk):
    ficha = get_object_or_404(
        FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'veterinario', 'medicamento_fefo'),
        pk=pk
    )
    return render(request, 'clinica/ficha_print.html', {'f': ficha})


@login_required
def recordatorios_vacunas(request):
    recordatorios = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').all()
    form = RecordatorioVacunaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Citatorio de vacuna/examen/control programado.')
        return redirect('recordatorios_vacunas')

    return render(request, 'clinica/recordatorios.html', {'recordatorios': recordatorios, 'form': form})


@login_required
def actualizar_asistencia_recordatorio(request, pk, resultado):
    rec = get_object_or_404(RecordatorioVacuna, pk=pk)
    if request.method == 'POST' and resultado in ('ASISTIO', 'NO_ASISTIO'):
        rec.estado = resultado
        rec.notificado = True
        rec.save()
        if resultado == 'ASISTIO' and rec.tipo == 'VACUNA':
            RecordatorioVacuna.objects.create(
                mascota=rec.mascota,
                tipo='VACUNA',
                nombre_vacuna_control=f"Refuerzo Anual: {rec.nombre_vacuna_control}",
                fecha_programada=date.today() + timedelta(days=365),
                observaciones='Programado automáticamente tras asistencia a vacunación.'
            )
            messages.success(request, 'Asistencia registrada (ASISTIÓ) y refuerzo anual programado automáticamente.')
        elif resultado == 'ASISTIO':
            messages.success(request, f'Asistencia registrada: El paciente ASISTIÓ a {rec.nombre_vacuna_control}.')
        else:
            messages.warning(request, f'Inasistencia registrada: El paciente NO ASISTIÓ a {rec.nombre_vacuna_control}.')
    return redirect('recordatorios_vacunas')


class VeterinarioViewSet(viewsets.ModelViewSet):
    queryset = Veterinario.objects.all()
    serializer_class = VeterinarioSerializer


class CitaMedicaViewSet(viewsets.ModelViewSet):
    queryset = CitaMedica.objects.select_related('mascota', 'veterinario').all()
    serializer_class = CitaMedicaSerializer


class FichaClinicaViewSet(viewsets.ModelViewSet):
    queryset = FichaClinica.objects.select_related('mascota', 'veterinario', 'medicamento_fefo').all()
    serializer_class = FichaClinicaSerializer


class RecordatorioVacunaViewSet(viewsets.ModelViewSet):
    queryset = RecordatorioVacuna.objects.select_related('mascota').all()
    serializer_class = RecordatorioVacunaSerializer
