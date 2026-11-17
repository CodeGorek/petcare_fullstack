from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from agenda.models import Veterinario
from .forms import CrearProfesionalForm
from .permissions import es_root
from .serializers import UsuarioSerializer


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


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('-is_superuser', 'username')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def perfil(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Issue a DRF token for decoupled frontend clients."""
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password') or ''
    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': UsuarioSerializer(user).data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Revoke the active DRF token for the authenticated user."""
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': 'Sesión cerrada correctamente.'})
