from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets

from .forms import MascotaForm, TutorForm
from .models import Mascota, Tutor
from .serializers import MascotaSerializer, TutorSerializer


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
            messages.error(request, 'Error de validación al registrar el Tutor. Verifique RUT, Nombre o Teléfono.')
        elif tipo_form == 'mascota':
            mascota_form = MascotaForm(request.POST)
            if mascota_form.is_valid():
                mascota_form.save()
                messages.success(request, 'Paciente registrado correctamente.')
                return redirect('tutores_mascotas')
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


class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer


class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.select_related('tutor').all()
    serializer_class = MascotaSerializer
