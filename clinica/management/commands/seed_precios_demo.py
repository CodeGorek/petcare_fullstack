from django.core.management.base import BaseCommand
from clinica.models import ServicioClinico, LoteMedicamento


class Command(BaseCommand):
    help = 'Agrega precios FICTICIOS para demostración, sin reemplazar precios existentes.'

    def handle(self, *args, **options):
        for nombre, precio in [
            ('Consulta general', 15000), ('Control médico', 10000),
            ('Vacunación (aplicación)', 8000), ('Examen de laboratorio', 20000),
            ('Curación', 12000), ('Procedimiento quirúrgico de ejemplo', 80000),
        ]:
            ServicioClinico.objects.get_or_create(nombre=nombre, defaults={'precio': precio})
        cantidad = LoteMedicamento.objects.filter(precio_unitario__isnull=True).update(precio_unitario=2000)
        self.stdout.write(self.style.SUCCESS(
            f'Precios FICTICIOS de demostración cargados. {cantidad} lotes sin precio recibieron $2.000 por unidad. '
            'Edita los valores desde Precios antes de crear cuentas. No se modificaron fichas ni stock.'
        ))
