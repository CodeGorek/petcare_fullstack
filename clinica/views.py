from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Tutor, Mascota, Veterinario, LoteMedicamento, CitaMedica, FichaClinica, RecordatorioVacuna
from .forms import (
    TutorForm, MascotaForm, LoteMedicamentoForm, CitaMedicaForm,
    FichaClinicaForm, RecordatorioVacunaForm, CrearProfesionalForm
)
from .serializers import (
    TutorSerializer, MascotaSerializer, VeterinarioSerializer, LoteMedicamentoSerializer,
    CitaMedicaSerializer, FichaClinicaSerializer, RecordatorioVacunaSerializer
)


def es_root(user):
    return user.is_authenticated and user.is_superuser


@login_required
def dashboard(request):
    asegurar_catalogo_fefo_inicial()
    hoy = date.today()
    citas_hoy = CitaMedica.objects.filter(fecha=hoy).select_related('mascota', 'mascota__tutor', 'veterinario').order_by('hora')
    recordatorios_todos = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').filter(mascota__activo=True).order_by('fecha_programada', 'hora_programada')
    # Alertas FEFO: medicamentos e insumos vencidos o que vencen en los próximos 45 días
    lotes_alerta_fefo = LoteMedicamento.objects.filter(activo=True, fecha_vencimiento__lte=hoy + timedelta(days=45)).order_by('fecha_vencimiento')
    lotes_inventario = LoteMedicamento.objects.filter(activo=True).order_by('fecha_vencimiento')[:8]

    context = {
        'total_tutores': Tutor.objects.filter(activo=True).count(),
        'total_mascotas': Mascota.objects.filter(activo=True).count(),
        'citas_hoy_count': citas_hoy.count(),
        'citas_hoy': citas_hoy,
        'recordatorios_agenda': recordatorios_todos[:6],
        'lotes_alerta_fefo': lotes_alerta_fefo,
        'lotes_inventario': lotes_inventario,
        'ultimas_fichas': FichaClinica.objects.select_related('mascota', 'veterinario', 'cita', 'medicamento_fefo')[:5],
    }
    return render(request, 'clinica/dashboard.html', context)


@login_required
def api_metricas_dashboard(request):
    especies = list(Mascota.objects.filter(activo=True).values('especie').annotate(total=Count('id')))
    estados_citas = list(CitaMedica.objects.values('estado').annotate(total=Count('id')))
    return JsonResponse({'especies': especies, 'estados_citas': estados_citas})


# 1. GESTIÓN DE TUTORES Y MASCOTAS CON DESHABILITACIÓN LÓGICA (SOFT DELETE)
@login_required
def gestion_tutores_mascotas(request):
    mostrar_inactivos = request.GET.get('inactivos') == '1'
    if mostrar_inactivos:
        tutores = Tutor.objects.prefetch_related('mascotas').all()
        mascotas = Mascota.objects.select_related('tutor').all()
    else:
        tutores = Tutor.objects.filter(activo=True).prefetch_related('mascotas')
        mascotas = Mascota.objects.filter(activo=True, tutor__activo=True).select_related('tutor')

    tutor_form = TutorForm()
    mascota_form = MascotaForm()

    if request.method == 'POST':
        tipo_form = request.POST.get('tipo_form')
        if tipo_form == 'tutor':
            tutor_form = TutorForm(request.POST)
            if tutor_form.is_valid():
                tutor_form.save()
                messages.success(request, 'Tutor validado y registrado correctamente.')
                return redirect('tutores_mascotas')
            else:
                messages.error(request, 'Error de validación al registrar el Tutor. Verifique RUT, Nombre o Teléfono.')
        elif tipo_form == 'mascota':
            mascota_form = MascotaForm(request.POST)
            if mascota_form.is_valid():
                mascota_form.save()
                messages.success(request, 'Paciente registrado correctamente.')
                return redirect('tutores_mascotas')
            else:
                messages.error(request, 'Error de validación en los datos de la Mascota.')

    return render(request, 'clinica/tutores_mascotas.html', {
        'tutores': tutores,
        'mascotas': mascotas,
        'tutor_form': tutor_form,
        'mascota_form': mascota_form,
        'mostrar_inactivos': mostrar_inactivos,
    })


@login_required
def editar_tutor(request, pk):
    tutor = get_object_or_404(Tutor, pk=pk)
    form = TutorForm(request.POST or None, instance=tutor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos del tutor {tutor.nombre_completo} actualizados.')
        return redirect('tutores_mascotas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Tutor: {tutor.nombre_completo}'})


@login_required
def toggle_estado_tutor(request, pk):
    tutor = get_object_or_404(Tutor, pk=pk)
    if request.method == 'POST':
        tutor.activo = not tutor.activo
        tutor.save(update_fields=['activo'])
        if not tutor.activo:
            tutor.mascotas.update(activo=False)
            messages.warning(request, f'Tutor {tutor.nombre_completo} y sus mascotas han sido deshabilitados (historial clínico conservado).')
        else:
            tutor.mascotas.update(activo=True)
            messages.success(request, f'Tutor {tutor.nombre_completo} y sus mascotas fueron reactivados.')
    return redirect('tutores_mascotas')


@login_required
def editar_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    form = MascotaForm(request.POST or None, instance=mascota)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Datos de {mascota.nombre} actualizados.')
        return redirect('tutores_mascotas')
    return render(request, 'clinica/form_generico.html', {'form': form, 'titulo': f'Editar Paciente: {mascota.nombre}'})


@login_required
def toggle_estado_mascota(request, pk):
    mascota = get_object_or_404(Mascota, pk=pk)
    if request.method == 'POST':
        mascota.activo = not mascota.activo
        mascota.save(update_fields=['activo'])
        estado_txt = "reactivado" if mascota.activo else "deshabilitado (sin pérdida de fichas clínicas)"
        messages.info(request, f'Paciente {mascota.nombre} {estado_txt}.')
    return redirect('tutores_mascotas')


@login_required
def expediente_mascota(request, pk):
    mascota = get_object_or_404(Mascota.objects.select_related('tutor'), pk=pk)
    fichas = mascota.fichas.select_related('veterinario', 'cita', 'medicamento_fefo').all()
    citas = mascota.citas.select_related('veterinario').all()
    recordatorios = mascota.recordatorios.all()
    return render(request, 'clinica/expediente_mascota.html', {
        'mascota': mascota,
        'fichas': fichas,
        'citas': citas,
        'recordatorios': recordatorios,
    })


# 2. AGENDA Y CONTROL DE ASISTENCIA
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


@login_required
def api_disponibilidad_veterinario(request):
    vet_id = request.GET.get('veterinario_id')
    fecha_str = request.GET.get('fecha')
    if not vet_id or not fecha_str:
        return JsonResponse({'bloques': []})

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

    return JsonResponse({
        'veterinario': vet.nombre,
        'especialidad': vet.get_especialidad_display(),
        'bloques': bloques
    })


# 3. FICHA CLÍNICA DIGITAL + IMPRESIÓN INDIVIDUAL + DISPENSACIÓN FEFO
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


# 4. FARMACIA E INVENTARIO BAJO NORMA FEFO
@login_required
def farmacia_fefo(request):
    lotes = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    form = LoteMedicamentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lote de medicamento ingresado y ordenado según Norma FEFO (First Expired, First Out).')
        return redirect('farmacia_fefo')
    return render(request, 'clinica/farmacia_fefo.html', {'lotes': lotes, 'form': form})


# 5. RECORDATORIOS DE VACUNAS, EXÁMENES Y CONTROLES (ASISTIÓ / NO ASISTIÓ)
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


# 6. GESTIÓN DE CUENTAS PROFESIONALES (SOLO ROOT)
@user_passes_test(es_root, login_url='dashboard')
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('-is_superuser', 'username')
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
        messages.success(request, f"Cuenta profesional '{nuevo_user.username}' habilitada exitosamente.")
        return redirect('gestion_usuarios')

    return render(request, 'clinica/usuarios.html', {'usuarios': usuarios, 'form': form})


@user_passes_test(es_root, login_url='dashboard')
def eliminar_usuario(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST' and not u.is_superuser:
        u.is_active = not u.is_active
        u.save(update_fields=['is_active'])
        estado = "habilitada" if u.is_active else "deshabilitada"
        messages.info(request, f'Cuenta de usuario {u.username} {estado}.')
    return redirect('gestion_usuarios')


def error_404_view(request, exception=None, ruta_invalida=None):
    return render(request, '404.html', {'ruta_solicitada': ruta_invalida}, status=404)


def error_403_view(request, exception=None):
    return render(request, '403.html', status=403)


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


class LoteMedicamentoViewSet(viewsets.ModelViewSet):
    queryset = LoteMedicamento.objects.all().order_by('fecha_vencimiento')
    serializer_class = LoteMedicamentoSerializer


class CitaMedicaViewSet(viewsets.ModelViewSet):
    queryset = CitaMedica.objects.select_related('mascota', 'veterinario').all()
    serializer_class = CitaMedicaSerializer


class FichaClinicaViewSet(viewsets.ModelViewSet):
    queryset = FichaClinica.objects.select_related('mascota', 'veterinario', 'medicamento_fefo').all()
    serializer_class = FichaClinicaSerializer


class RecordatorioVacunaViewSet(viewsets.ModelViewSet):
    queryset = RecordatorioVacuna.objects.select_related('mascota').all()
    serializer_class = RecordatorioVacunaSerializer

def asegurar_catalogo_fefo_inicial():
    if LoteMedicamento.objects.count() > 0:
        return
    hoy = date.today()
    iniciales = [
        {
            'codigo_lote': 'FEFO-2026-VAC8',
            'nombre': 'Vacuna Óctuple Canina (Nobivac DHPPi+L)',
            'categoria': 'VACUNA_BIO',
            'presentacion': 'Frasco monodosis liofilizado 1 ml',
            'fecha_vencimiento': hoy + timedelta(days=9),
            'tiempo_limite_uso': 'Usar dentro de 2 horas tras reconstitución (Mantener 2°C-8°C)',
            'stock_disponible': 14,
        },
        {
            'codigo_lote': 'FEFO-2026-SYN1',
            'nombre': 'Amoxicilina + Ácido Clavulánico 250 mg (Synulox)',
            'categoria': 'MEDICAMENTO',
            'presentacion': 'Caja x 10 comprimidos palatables',
            'fecha_vencimiento': hoy + timedelta(days=16),
            'tiempo_limite_uso': 'Blíster abierto: máximo 14 días en ambiente seco (<25°C)',
            'stock_disponible': 22,
        },
        {
            'codigo_lote': 'FEFO-2026-MEL2',
            'nombre': 'Meloxicam Inyectable 2% (Metacam)',
            'categoria': 'MEDICAMENTO',
            'presentacion': 'Frasco ampolla multidosis 50 ml',
            'fecha_vencimiento': hoy + timedelta(days=25),
            'tiempo_limite_uso': '28 días máximo tras primera punción del tapón de goma',
            'stock_disponible': 8,
        },
        {
            'codigo_lote': 'FEFO-2026-TRIF',
            'nombre': 'Vacuna Triple Felina (Feligen CRP)',
            'categoria': 'VACUNA_BIO',
            'presentacion': 'Vial monodosis 1 ml',
            'fecha_vencimiento': hoy + timedelta(days=34),
            'tiempo_limite_uso': 'Uso inmediato tras reconstitución (máx. 1 hora)',
            'stock_disponible': 12,
        },
        {
            'codigo_lote': 'FEFO-2026-RING',
            'nombre': 'Solución Ringer Lactato Estéril + Bajada Venoclisis',
            'categoria': 'INSUMO',
            'presentacion': 'Matraz flexible 500 ml',
            'fecha_vencimiento': hoy + timedelta(days=42),
            'tiempo_limite_uso': 'Máximo 24 horas una vez perforado el puerto estéril',
            'stock_disponible': 19,
        },
        {
            'codigo_lote': 'FEFO-2027-RAB9',
            'nombre': 'Vacuna Antirrábica Inactivada (Nobivac Rabies)',
            'categoria': 'VACUNA_BIO',
            'presentacion': 'Frasco ampolla 10 dosis (10 ml)',
            'fecha_vencimiento': hoy + timedelta(days=95),
            'tiempo_limite_uso': '10 horas tras primera extracción manteniendo cadena de frío',
            'stock_disponible': 30,
        },
        {
            'codigo_lote': 'FEFO-2027-BRAV',
            'nombre': 'Fluralaner 500 mg Antiparasitario (Bravecto)',
            'categoria': 'MEDICAMENTO',
            'presentacion': 'Comprimido masticable 10-20 kg',
            'fecha_vencimiento': hoy + timedelta(days=140),
            'tiempo_limite_uso': 'Administrar inmediatamente al abrir el sobre de aluminio',
            'stock_disponible': 18,
        },
        {
            'codigo_lote': 'FEFO-2027-CAT22',
            'nombre': 'Catéter Intravenoso 22G + Sutura Absorbible Vicryl 3-0',
            'categoria': 'INSUMO',
            'presentacion': 'Blíster estéril individual',
            'fecha_vencimiento': hoy + timedelta(days=210),
            'tiempo_limite_uso': 'Uso único inmediato al abrir empaque estéril',
            'stock_disponible': 45,
        },
    ]
    for item in iniciales:
        LoteMedicamento.objects.update_or_create(codigo_lote=item['codigo_lote'], defaults=item)


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
