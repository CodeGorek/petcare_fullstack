import mimetypes
import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

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
    permission_classes = [IsAuthenticated]


class MascotaViewSet(viewsets.ModelViewSet):
    queryset = Mascota.objects.select_related('tutor').all()
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]

    @action(
        detail=True,
        methods=['post'],
        url_path='subir-foto',
        parser_classes=[MultiPartParser, FormParser],
    )
    def subir_foto(self, request, pk=None):
        """Upload a patient image directly from browser, mirroring to S3 if configured with local API fallback."""
        mascota = self.get_object()
        archivo = request.FILES.get('foto')
        if not archivo:
            return Response({'detail': 'Debes seleccionar un archivo de imagen.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = Path(archivo.name).suffix.lower()
        if ext not in {'.jpg', '.jpeg', '.png', '.webp', '.gif'}:
            return Response(
                {'detail': 'Formato no permitido. Usa JPG, PNG, WebP o GIF.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if archivo.size > 5 * 1024 * 1024:
            return Response(
                {'detail': 'La imagen supera el máximo permitido de 5 MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = archivo.read()
        content_type = getattr(archivo, 'content_type', None) or mimetypes.guess_type(archivo.name)[0] or 'image/jpeg'

        carpeta = Path(settings.MEDIA_ROOT) / 'mascotas'
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in carpeta.glob(f'mascota_{mascota.pk}.*'):
            viejo.unlink(missing_ok=True)
        destino = carpeta / f'mascota_{mascota.pk}{ext}'
        destino.write_bytes(data)

        url_final = f"{reverse('mascota-ver-foto', args=[mascota.pk])}?v={uuid4().hex[:8]}"

        bucket = os.getenv('S3_BUCKET', '').strip()
        if bucket:
            s3_key = f'fotos/mascota_{mascota.pk}_{uuid4().hex[:8]}{ext}'
            try:
                import boto3

                boto3.client('s3').put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=data,
                    ContentType=content_type,
                )
                if os.getenv('S3_PUBLIC_READ', '').lower() in ('true', '1', 'yes'):
                    url_final = f'https://{bucket}.s3.amazonaws.com/{s3_key}'
            except Exception:
                # Fall back silently to the Django media API URL when EC2 has no S3 write IAM role.
                pass

        mascota.foto_url = url_final
        mascota.save(update_fields=['foto_url'])
        return Response(self.get_serializer(mascota).data)

    @action(
        detail=True,
        methods=['get'],
        url_path='ver-foto',
        permission_classes=[AllowAny],
    )
    def ver_foto(self, request, pk=None):
        """Serve the locally stored patient photo for <img> tags without requiring Bearer headers."""
        mascota = self.get_object()
        carpeta = Path(settings.MEDIA_ROOT) / 'mascotas'
        archivos = sorted(carpeta.glob(f'mascota_{mascota.pk}.*'))
        if not archivos:
            raise Http404('Mascota sin foto local registrada.')
        archivo = archivos[0]
        ctype = mimetypes.guess_type(archivo.name)[0] or 'application/octet-stream'
        return FileResponse(open(archivo, 'rb'), content_type=ctype)

    @action(detail=False, methods=['get'], url_path='buscar-chip')
    def buscar_chip(self, request):
        """Find a patient quickly by its RFID microchip ISO code."""
        chip = (request.query_params.get('chip') or '').strip()
        if not chip:
            return Response({'encontrado': False, 'chip_consultado': '', 'mascota': None})
        mascota = Mascota.objects.select_related('tutor').filter(microchip__iexact=chip).first()
        if not mascota:
            return Response({'encontrado': False, 'chip_consultado': chip, 'mascota': None})
        return Response({
            'encontrado': True,
            'chip_consultado': chip,
            'mascota': self.get_serializer(mascota).data,
        })
