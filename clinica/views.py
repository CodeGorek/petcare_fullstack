from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Tutor, Mascota, Veterinario, CitaMedica, FichaClinica, RecordatorioVacuna
from .forms import TutorForm, MascotaForm, CitaMedicaForm, FichaClinicaForm, RecordatorioVacunaForm
from .serializers import (
    TutorSerializer, MascotaSerializer, VeterinarioSerializer,
    CitaMedicaSerializer, FichaClinicaSerializer, RecordatorioVacunaSerializer
)


@login_required
def dashboard(request):
    hoy = date.today()
    citas_hoy = CitaMedica.objects.filter(fecha=hoy).select_related('mascota', 'veterinario')
    recordatorios_pendientes = RecordatorioVacuna.objects.filter(estado='PENDIENTE').select_related('mascota', 'mascota__tutor')
    alertas_urgentes = [r for r in recordatorios_pendientes if r.nivel_alerta in ('VENCIDO', 'PROXIMO')]

    context = {
        'total_tutores': Tutor.objects.count(),
        'total_mascotas': Mascota.objects.count(),
        'citas_hoy_count': citas_hoy.count(),
        'citas_hoy': citas_hoy,
        'alertas_urgentes': alertas_urgentes,
        'ultimas_fichas': FichaClinica.objects.select_related('mascota', 'veterinario')[:5],
    }
    return render(request, 'clinica/dashboard.html', context)


# 1. CRUD TUTORES Y MASCOTAS
@login_required
def gestion_tutores_mascotas(request):
    tutores = Tutor.objects.prefetch_related('mascotas').all()
    mascotas = Mascota.objects.select_related('tutor').all()
    tutor_form = TutorForm()
    mascota_form = MascotaForm()

    if request.method == 'POST':
        tipo_form = request.POST.get('tipo_form')
        if tipo_form == 'tutor':
            tutor_form = TutorForm(request.POST)
            if tutor_form.is_valid():
                tutor_form.save()
                messages.success(request, 'Tutor registrado correctamente.')
                return redirect('tutores_mascotas')
        elif tipo_form == 'mascota':
            mascota_form = MascotaForm(request.POST)
            if mascota_form.is_valid():
                mascota_form.save()
                messages.success(request, 'Mascota registrada correctamente.')
                return redirect('tutores_mascotas')

    return render(request, 'clinica/tutores_mascotas.html', {
        'tutores': tutores,
        'mascotas': mascotas,
        'tutor_form': tutor_form,
        'mascota_form': mascota_form,
    })


@login_required
def editar_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    form = MascotaForm(request.POST or None, instance=mascota)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos de {mascota.nombre} actualizados.')
        return redirect('tutores_mascotas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Mascota: {mascota.nombre}'})


@login_required
def eliminar_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    if request.method == 'POST':
        mascota.delete()
        messages.warning(request, 'Mascota eliminada del registro.')
    return redirect('tutores_mascotas')


# 2. AGENDAMIENTO Y DISPONIBILIDAD POR PROFESIONAL
@login_required
def agenda_citas(request):
    citas = CitaMedica.objects.select_related('mascota', 'mascota__tutor', 'veterinario').all()
    veterinarios = Veterinario.objects.filter(activo=True)
    form = CitaMedicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita agendada sin conflictos de horario.')
        return redirect('agenda_citas')

    return render(request, 'clinica/agenda_citas.html', {
        'citas': citas,
        'veterinarios': veterinarios,
        'form': form,
    })


@login_required
def cambiar_estado_cita(request, pk, nuevo_estado):
    cita = get_object_or_404(CitaMedica, pk=pk)
    if request.method == 'POST' and nuevo_estado in ('COMPLETADA', 'CANCELADA'):
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])
        messages.info(request, f'Cita actualizada a {cita.get_estado_display()}.')
    return redirect('agenda_citas')


@login_required
def api_disponibilidad_veterinario(request):
    vet_id = request.GET.get('veterinario_id')
    fecha_str = request.GET.get('fecha')
    if not vet_id or not fecha_str:
        return JsonResponse({'bloques_disponibles': []})

    vet = get_object_or_404(Veterinario, pk=vet_id)
    ocupadas = set(
        CitaMedica.objects.filter(veterinario=vet, fecha=fecha_str)
        .exclude(estado='CANCELADA')
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

    return JsonResponse({
        'veterinario': vet.nombre,
        'especialidad': vet.get_especialidad_display(),
        'bloques': bloques
    })


# 3. FICHA CLÍNICA DIGITAL
@login_required
def fichas_clinicas(request):
    fichas = FichaClinica.objects.select_related('mascota', 'mascota__tutor', 'veterinario', 'cita').all()
    form = FichaClinicaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ficha = form.save()
        messages.success(request, f'Ficha clínica #{ficha.id} guardada y peso de mascota actualizado.')
        return redirect('fichas_clinicas')

    return render(request, 'clinica/fichas_clinicas.html', {'fichas': fichas, 'form': form})


# 4. RECORDATORIOS DE VACUNACIÓN Y CONTROLES
@login_required
def recordatorios_vacunas(request):
    recordatorios = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').all()
    form = RecordatorioVacunaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Recordatorio preventivo programado.')
        return redirect('recordatorios_vacunas')

    return render(request, 'clinica/recordatorios.html', {'recordatorios': recordatorios, 'form': form})


@login_required
def marcar_recordatorio_aplicado(request, pk):
    rec = get_object_or_404(RecordatorioVacuna, pk=pk)
    if request.method == 'POST':
        rec.estado = 'APLICADA'
        rec.notificado = True
        rec.save()
        # Regla de negocio: programar refuerzo anual automático si es vacuna
        if rec.tipo == 'VACUNA':
            RecordatorioVacuna.objects.create(
                mascota=rec.mascota,
                tipo='VACUNA',
                nombre_vacuna_control=f"Refuerzo Anual: {rec.nombre_vacuna_control}",
                fecha_programada=date.today() + timedelta(days=365),
                observaciones='Generado automáticamente tras aplicación de dosis previa.'
            )
            messages.success(request, 'Vacuna marcada como aplicada y refuerzo anual programado automáticamente.')
        else:
            messages.success(request, 'Control marcado como realizado.')
    return redirect('recordatorios_vacunas')


# VIEWSETS API REST (DRF)
class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer


class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.select_related('tutor').all()
    serializer_class = MascotaSerializer


class VeterinarioViewSet(viewsets.ModelViewSet):
    queryset = Veterinario.objects.all()
    serializer_class = VeterinarioSerializer


class CitaMedicaViewSet(viewsets.ModelViewSet):
    queryset = CitaMedica.objects.select_related('mascota', 'veterinario').all()
    serializer_class = CitaMedicaSerializer


class FichaClinicaViewSet(viewsets.ModelViewSet):
    queryset = FichaClinica.objects.select_related('mascota', 'veterinario').all()
    serializer_class = FichaClinicaSerializer


class RecordatorioVacunaViewSet(viewsets.ModelViewSet):
    queryset = RecordatorioVacuna.objects.select_related('mascota').all()
    serializer_class = RecordatorioVacunaSerializer

    @action(detail=False, methods=['get'])
    def alertas_activas(self, request):
        pendientes = [r for r in self.get_queryset().filter(estado='PENDIENTE') if r.nivel_alerta in ('VENCIDO', 'PROXIMO')]
        serializer = self.get_serializer(pendientes, many=True)
        return Response(serializer.data)

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .forms import CrearProfesionalForm

def es_root(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(es_root, login_url='dashboard')
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('-is_superuser', 'username')
    veterinarios_map = {v.email: v for v in Veterinario.objects.all()}
    form = CrearProfesionalForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        nuevo_user = User.objects.create_user(
            username=cd['username'],
            email=cd['email'],
            password=cd['password'],
            first_name=cd['nombre_completo'],
            is_staff=False,
            is_superuser=False,
        )
        if cd['rol'] == 'VETERINARIO':
            Veterinario.objects.update_or_create(
                rut=cd['rut'],
                defaults={
                    'nombre': cd['nombre_completo'],
                    'especialidad': cd['especialidad'] or 'GENERAL',
                    'email': cd['email'],
                    'hora_inicio': cd['hora_inicio'],
                    'hora_fin': cd['hora_fin'],
                    'activo': True,
                }
            )
            messages.success(request, f"Cuenta profesional '{nuevo_user.username}' y perfil de agenda médica creados exitosamente.")
        else:
            messages.success(request, f"Cuenta de recepción '{nuevo_user.username}' creada exitosamente.")
        return redirect('gestion_usuarios')

    return render(request, 'clinica/usuarios.html', {
        'usuarios': usuarios,
        'veterinarios_map': veterinarios_map,
        'form': form,
    })

@user_passes_test(es_root, login_url='dashboard')
def eliminar_usuario(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if u.is_superuser:
            messages.error(request, 'No se puede eliminar la cuenta Root principal.')
        else:
            nombre = u.username
            u.delete()
            messages.warning(request, f'Cuenta de usuario {nombre} revocada y eliminada.')
    return redirect('gestion_usuarios')

def error_404_view(request, exception=None, ruta_invalida=None):
    return render(request, '404.html', {'ruta_solicitada': ruta_invalida}, status=404)

def error_403_view(request, exception=None):
    return render(request, '403.html', status=403)
