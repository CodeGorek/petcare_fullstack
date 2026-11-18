from collections import defaultdict
from threading import Lock
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from agenda.models import Veterinario
from .forms import CrearProfesionalForm
from .models import NovedadPersonal
from .permissions import EsRootPermission, es_root
from .serializers import NovedadPersonalSerializer, UsuarioSerializer

LOGIN_MAX_ATTEMPTS = int(getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5) or 5)
LOGIN_LOCKOUT_SECONDS = int(getattr(settings, 'LOGIN_LOCKOUT_SECONDS', 300) or 300)
_LOGIN_FAILURES = defaultdict(list)
_LOGIN_LOCK = Lock()


def _login_key(request, username):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or 'unknown'
    return f'{ip}:{(username or "").lower()}'


def _login_bloqueado_segundos(key):
    ahora = time.monotonic()
    corte = ahora - LOGIN_LOCKOUT_SECONDS
    with _LOGIN_LOCK:
        intentos = [t for t in _LOGIN_FAILURES.get(key, []) if t > corte]
        _LOGIN_FAILURES[key] = intentos
        if len(intentos) >= LOGIN_MAX_ATTEMPTS:
            return max(1, int(intentos[0] + LOGIN_LOCKOUT_SECONDS - ahora))
    return 0


def _registrar_fallo_login(key):
    ahora = time.monotonic()
    with _LOGIN_LOCK:
        _LOGIN_FAILURES[key].append(ahora)
        return len(_LOGIN_FAILURES[key])


def _limpiar_fallos_login(key):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(key, None)


def _crear_cuenta_profesional(cd):
    """Create a standard user account and its optional Veterinario profile."""
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
                'especialidad': cd.get('especialidad') or 'GENERAL',
                'email': cd['email'],
                'hora_inicio': cd['hora_inicio'],
                'hora_fin': cd['hora_fin'],
                'activo': True,
            },
        )
    return nuevo_user


@user_passes_test(es_root, login_url='dashboard')
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('-is_superuser', 'username')
    form = CrearProfesionalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nuevo_user = _crear_cuenta_profesional(form.cleaned_data)
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


class UsuarioViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by('-is_superuser', 'username')
    serializer_class = UsuarioSerializer
    permission_classes = [EsRootPermission]

    def create(self, request, *args, **kwargs):
        data = {
            'username': request.data.get('username', ''),
            'password': request.data.get('password', ''),
            'nombre_completo': request.data.get('nombre_completo', ''),
            'rut': request.data.get('rut', ''),
            'email': request.data.get('email', ''),
            'rol': request.data.get('rol', 'VETERINARIO'),
            'especialidad': request.data.get('especialidad') or 'GENERAL',
            'hora_inicio': request.data.get('hora_inicio') or '09:00',
            'hora_fin': request.data.get('hora_fin') or '18:00',
        }
        form = CrearProfesionalForm(data)
        if not form.is_valid():
            errores = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
            return Response(errores, status=status.HTTP_400_BAD_REQUEST)
        nuevo_user = _crear_cuenta_profesional(form.cleaned_data)
        return Response(self.get_serializer(nuevo_user).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='toggle-activo')
    def toggle_activo(self, request, pk=None):
        """Enable or disable a non-superuser staff/clinical account."""
        usuario = self.get_object()
        if usuario.is_superuser:
            return Response(
                {'detail': 'No se puede deshabilitar una cuenta Root.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=['is_active'])
        return Response(self.get_serializer(usuario).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def perfil(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Issue a DRF token for decoupled frontend clients with brute-force lockout protection."""
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    key = _login_key(request, username)

    espera = _login_bloqueado_segundos(key)
    if espera > 0:
        return Response(
            {
                'detail': f'Demasiados intentos fallidos. Cuenta bloqueada temporalmente por {espera} segundos.',
                'retry_after_seconds': espera,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        intentos = _registrar_fallo_login(key)
        restantes = max(0, LOGIN_MAX_ATTEMPTS - intentos)
        if restantes == 0:
            return Response(
                {
                    'detail': f'Alcanzaste el límite de {LOGIN_MAX_ATTEMPTS} intentos fallidos. Reintenta en {LOGIN_LOCKOUT_SECONDS} segundos.',
                    'retry_after_seconds': LOGIN_LOCKOUT_SECONDS,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return Response(
            {'detail': f'Credenciales inválidas. Te quedan {restantes} intento(s) antes del bloqueo temporal.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    _limpiar_fallos_login(key)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UsuarioSerializer(user).data})


class NovedadPersonalViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Root-only endpoint for attendance, medical leave, vacation, resignation, and termination logs."""

    queryset = NovedadPersonal.objects.select_related('usuario', 'registrado_por').all()
    serializer_class = NovedadPersonalSerializer
    permission_classes = [EsRootPermission]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Revoke the active DRF token for the authenticated user."""
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': 'Sesión cerrada correctamente.'})
