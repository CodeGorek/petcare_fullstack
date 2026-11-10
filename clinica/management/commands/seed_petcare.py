from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinica.models import Tutor, Mascota, Veterinario, CitaMedica, FichaClinica, RecordatorioVacuna

class Command(BaseCommand):
    help = 'Carga datos iniciales de demostración para PetCare'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@petcare.cl', 'AdminPetCare2026!')
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin / AdminPetCare2026!'))

        t1, _ = Tutor.objects.get_or_create(
            rut='18456789-2',
            defaults={'nombre_completo': 'Camila Soto Riquelme', 'telefono': '+56987654321', 'email': 'camila.soto@email.cl', 'direccion': 'Av. Alemania 0840, Temuco'}
        )
        t2, _ = Tutor.objects.get_or_create(
            rut='16234987-K',
            defaults={'nombre_completo': 'Rodrigo Muñoz Lagos', 'telefono': '+56912345678', 'email': 'rmunoz@email.cl', 'direccion': 'Los Pablos 1420, Temuco'}
        )

        m1, _ = Mascota.objects.get_or_create(
            tutor=t1, nombre='Thor',
            defaults={'especie': 'CANINO', 'raza': 'Pastor Alemán', 'sexo': 'M', 'fecha_nacimiento': date(2022, 5, 14), 'peso_kg': 32.5, 'alergias_conocidas': 'Sensibilidad a AINEs'}
        )
        m2, _ = Mascota.objects.get_or_create(
            tutor=t2, nombre='Mishi',
            defaults={'especie': 'FELINO', 'raza': 'Común Europeo', 'sexo': 'H', 'fecha_nacimiento': date(2023, 9, 1), 'peso_kg': 4.2}
        )

        v1, _ = Veterinario.objects.get_or_create(
            rut='15333444-5',
            defaults={'nombre': 'Valentina Herrera', 'especialidad': 'GENERAL', 'email': 'vherrera@petcare.cl', 'hora_inicio': time(9, 0), 'hora_fin': time(18, 0)}
        )
        v2, _ = Veterinario.objects.get_or_create(
            rut='14222888-1',
            defaults={'nombre': 'Sebastián Valdés', 'especialidad': 'CIRUGIA', 'email': 'svaldes@petcare.cl', 'hora_inicio': time(10, 0), 'hora_fin': time(19, 0)}
        )

        hoy = date.today()
        cita1, _ = CitaMedica.objects.get_or_create(
            veterinario=v1, fecha=hoy, hora=time(10, 30),
            defaults={'mascota': m1, 'motivo': 'Control anual y refuerzo séxtuple', 'estado': 'PROGRAMADA'}
        )

        if not FichaClinica.objects.filter(mascota=m1).exists():
            FichaClinica.objects.create(
                mascota=m1, veterinario=v1, peso_registrado=32.5, temperatura_c=38.4,
                diagnostico='Paciente clínicamente sano. Mucosas rosadas, hidratación normal.',
                tratamiento='Administración de vacuna Óctuple y desparasitación interna.',
                receta_medica='Drontal Plus 1 comprimido cada 10kg dosis única.',
                examenes_solicitados='Perfil bioquímico preventivo en 6 meses.'
            )

        RecordatorioVacuna.objects.get_or_create(
            mascota=m1, nombre_vacuna_control='Vacuna Antirrábica',
            defaults={'tipo': 'VACUNA', 'fecha_programada': hoy + timedelta(days=3), 'estado': 'PENDIENTE'}
        )
        RecordatorioVacuna.objects.get_or_create(
            mascota=m2, nombre_vacuna_control='Triple Felina',
            defaults={'tipo': 'VACUNA', 'fecha_programada': hoy - timedelta(days=2), 'estado': 'PENDIENTE'}
        )

        self.stdout.write(self.style.SUCCESS('Datos semilla de PetCare cargados correctamente.'))

        if not User.objects.filter(username='dra.herrera').exists():
            User.objects.create_user(
                username='dra.herrera',
                email='vherrera@petcare.cl',
                password='VetPetCare2026!',
                first_name='Dra. Valentina Herrera',
                is_staff=False,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS('Cuenta profesional creada: dra.herrera / VetPetCare2026!'))
