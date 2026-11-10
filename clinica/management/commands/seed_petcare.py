from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinica.models import Tutor, Mascota, Veterinario, LoteMedicamento, CitaMedica, FichaClinica, RecordatorioVacuna


class Command(BaseCommand):
    help = 'Carga catálogo completo de medicamentos/insumos FEFO, pacientes, citas de hoy y fichas clínicas'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@petcare.cl', 'AdminPetCare2026!')
        if not User.objects.filter(username='dra.herrera').exists():
            User.objects.create_user(
                username='dra.herrera', email='vherrera@petcare.cl',
                password='VetPetCare2026!', first_name='Dra. Valentina Herrera',
                is_staff=False, is_superuser=False
            )

        t1, _ = Tutor.objects.update_or_create(
            rut='18456789-2',
            defaults={'nombre_completo': 'Camila Soto Riquelme', 'telefono': '+56987654321', 'email': 'camila.soto@email.cl', 'direccion': 'Av. Alemania 0840, Temuco', 'activo': True}
        )
        t2, _ = Tutor.objects.update_or_create(
            rut='16234987-K',
            defaults={'nombre_completo': 'Rodrigo Muñoz Lagos', 'telefono': '+56912345678', 'email': 'rmunoz@email.cl', 'direccion': 'Los Pablos 1420, Temuco', 'activo': True}
        )
        t3, _ = Tutor.objects.update_or_create(
            rut='13308857-2',
            defaults={'nombre_completo': 'Javiera Morales Pizarro', 'telefono': '+56976543210', 'email': 'jmorales@email.cl', 'direccion': 'Av. Pedro de Valdivia 0320, Temuco', 'activo': True}
        )

        m1, _ = Mascota.objects.update_or_create(
            tutor=t1, nombre='Thor',
            defaults={'especie': 'CANINO', 'raza': 'Pastor Alemán', 'sexo': 'M', 'fecha_nacimiento': date(2022, 5, 14), 'peso_kg': 32.5, 'alergias_conocidas': 'Sensibilidad gástrica a AINEs no selectivos', 'activo': True}
        )
        m2, _ = Mascota.objects.update_or_create(
            tutor=t2, nombre='Mishi',
            defaults={'especie': 'FELINO', 'raza': 'Común Europeo', 'sexo': 'H', 'fecha_nacimiento': date(2023, 9, 1), 'peso_kg': 4.2, 'activo': True}
        )
        m3, _ = Mascota.objects.update_or_create(
            tutor=t3, nombre='Kira',
            defaults={'especie': 'CANINO', 'raza': 'Golden Retriever', 'sexo': 'H', 'fecha_nacimiento': date(2021, 11, 20), 'peso_kg': 27.8, 'activo': True}
        )

        v1, _ = Veterinario.objects.update_or_create(
            rut='15333444-5',
            defaults={'nombre': 'Valentina Herrera', 'especialidad': 'GENERAL', 'email': 'vherrera@petcare.cl', 'hora_inicio': time(9, 0), 'hora_fin': time(18, 0), 'activo': True}
        )
        v2, _ = Veterinario.objects.update_or_create(
            rut='14222888-1',
            defaults={'nombre': 'Sebastián Valdés', 'especialidad': 'CIRUGIA', 'email': 'svaldes@petcare.cl', 'hora_inicio': time(10, 0), 'hora_fin': time(19, 0), 'activo': True}
        )

        hoy = date.today()

        # CATÁLOGO COMPLETO DE MEDICAMENTOS E INSUMOS BAJO NORMA FEFO
        catalogo_fefo = [
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
                'codigo_lote': 'FEFO-2026-A1',
                'nombre': 'Amoxicilina + Ácido Clavulánico 250 mg (Synulox)',
                'categoria': 'MEDICAMENTO',
                'presentacion': 'Caja x 10 comprimidos palatables',
                'fecha_vencimiento': hoy + timedelta(days=18),
                'tiempo_limite_uso': 'Blíster abierto: máximo 14 días en lugar seco (<25°C)',
                'stock_disponible': 22,
            },
            {
                'codigo_lote': 'FEFO-2026-MEL2',
                'nombre': 'Meloxicam Inyectable 2% (Antiinflamatorio)',
                'categoria': 'MEDICAMENTO',
                'presentacion': 'Frasco ampolla multidosis 50 ml',
                'fecha_vencimiento': hoy + timedelta(days=27),
                'tiempo_limite_uso': '28 días máximo tras primera punción del tapón de goma',
                'stock_disponible': 8,
            },
            {
                'codigo_lote': 'FEFO-2026-INS1',
                'nombre': 'Solución Ringer Lactato Estéril + Bajada de Suero',
                'categoria': 'INSUMO',
                'presentacion': 'Matraz flexible 500 ml',
                'fecha_vencimiento': hoy + timedelta(days=40),
                'tiempo_limite_uso': 'Uso inmediato: máximo 24 horas una vez perforado el puerto',
                'stock_disponible': 19,
            },
            {
                'codigo_lote': 'FEFO-2027-INS4',
                'nombre': 'Catéter Intravenoso Veterinario 22G + Sutura Vicryl 3-0',
                'categoria': 'INSUMO',
                'presentacion': ' Sobre estéril individual',
                'fecha_vencimiento': hoy + timedelta(days=150),
                'tiempo_limite_uso': 'Uso único inmediato al abrir empaque estéril',
                'stock_disponible': 45,
            },
            {
                'codigo_lote': 'FEFO-2027-B4',
                'nombre': 'Amoxicilina + Ácido Clavulánico 250 mg (Lote Respaldo)',
                'categoria': 'MEDICAMENTO',
                'presentacion': 'Caja x 10 comprimidos palatables',
                'fecha_vencimiento': hoy + timedelta(days=240),
                'tiempo_limite_uso': 'Blíster abierto: máximo 14 días en lugar seco (<25°C)',
                'stock_disponible': 50,
            },
        ]
        lotes_creados = {}
        for item in catalogo_fefo:
            obj, _ = LoteMedicamento.objects.update_or_create(
                codigo_lote=item['codigo_lote'],
                defaults=item
            )
            lotes_creados[item['codigo_lote']] = obj

        # CITAS PARA EL DÍA DE HOY CON HORAS CLARAS
        c1, _ = CitaMedica.objects.update_or_create(
            veterinario=v1, fecha=hoy, hora=time(10, 30),
            defaults={'mascota': m1, 'motivo': 'Control general y refuerzo inmunológico', 'estado': 'ASISTIO'}
        )
        CitaMedica.objects.update_or_create(
            veterinario=v1, fecha=hoy, hora=time(11, 30),
            defaults={'mascota': m2, 'motivo': 'Evaluación preventiva felina y perfil renal', 'estado': 'PROGRAMADA'}
        )
        CitaMedica.objects.update_or_create(
            veterinario=v2, fecha=hoy, hora=time(15, 0),
            defaults={'mascota': m3, 'motivo': 'Control traumatológico y retiro de puntos', 'estado': 'PROGRAMADA'}
        )

        # FICHA CLÍNICA ASOCIADA A CITA E INSUMO FEFO
        if FichaClinica.objects.exists():
            ficha = FichaClinica.objects.first()
            ficha.cita = c1
            ficha.medicamento_fefo = lotes_creados['FEFO-2026-A1']
            ficha.cantidad_dispensada = 1
            ficha.save()

        # CITACIONES DE VACUNAS, EXÁMENES Y CONTROLES CON FECHA Y HORA
        RecordatorioVacuna.objects.update_or_create(
            mascota=m1, nombre_vacuna_control='Vacuna Antirrábica Anual',
            defaults={'tipo': 'VACUNA', 'fecha_programada': hoy - timedelta(days=1), 'hora_programada': time(10, 0), 'estado': 'NO_ASISTIO', 'observaciones': 'Tutor solicita reagendar para esta semana'}
        )
        RecordatorioVacuna.objects.update_or_create(
            mascota=m2, nombre_vacuna_control='Vacuna Triple Felina',
            defaults={'tipo': 'VACUNA', 'fecha_programada': hoy, 'hora_programada': time(12, 0), 'estado': 'ASISTIO', 'observaciones': 'Aplicada sin reacciones adversas'}
        )
        RecordatorioVacuna.objects.update_or_create(
            mascota=m3, nombre_vacuna_control='Examen Perfil Bioquímico y Hemograma',
            defaults={'tipo': 'EXAMEN', 'fecha_programada': hoy + timedelta(days=2), 'hora_programada': time(9, 30), 'estado': 'PENDIENTE', 'observaciones': 'Acudir con ayuno sólido de 8 horas'}
        )

        self.stdout.write(self.style.SUCCESS('Base de datos actualizada con catálogo FEFO, citas de hoy y horas de citación.'))
