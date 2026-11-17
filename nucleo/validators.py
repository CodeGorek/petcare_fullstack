import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validar_rut_chileno(value):
    """Validate Chilean RUT using the standard Modulo 11 check digit."""
    rut_limpio = value.upper().replace('.', '').replace(' ', '')
    if not re.match(r'^\d{7,8}-[\dK]$', rut_limpio):
        raise ValidationError('Formato de RUT inválido. Ejemplo válido: 18456789-2.')
    cuerpo, dv = rut_limpio.split('-')
    suma = 0
    multiplo = 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = 11 - (suma % 11)
    dv_esperado = '0' if resto == 11 else ('K' if resto == 10 else str(resto))
    if dv != dv_esperado:
        raise ValidationError(f'RUT inválido (dígito verificador incorrecto, debería ser -{dv_esperado}).')


nombre_validator = RegexValidator(
    regex=r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]{3,120}$',
    message='Ingrese un nombre válido (solo letras y espacios, mínimo 3 caracteres).'
)

telefono_validator = RegexValidator(
    regex=r'^\+?56\s?9\s?\d{4}\s?\d{4}$',
    message='Formato telefónico chileno inválido. Use +56912345678.'
)
