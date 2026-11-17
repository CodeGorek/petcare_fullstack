from datetime import date, timedelta

from .models import LoteMedicamento


def asegurar_catalogo_fefo_inicial():
    """Populate initial FEFO catalog when the inventory table is empty."""
    if LoteMedicamento.objects.count() > 0:
        return
    hoy = date.today()
    iniciales = [
        {
            'codigo_lote': 'FEFO-2026-VAC8',
            'codigo_barras': '7801000001011',
            'nombre': 'Vacuna Óctuple Canina (Nobivac DHPPi+L)',
            'categoria': 'VACUNA_BIO',
            'presentacion': 'Frasco monodosis liofilizado 1 ml',
            'fecha_vencimiento': hoy + timedelta(days=9),
            'tiempo_limite_uso': 'Usar dentro de 2 horas tras reconstitución (Mantener 2°C-8°C)',
            'stock_disponible': 14,
        },
        {
            'codigo_lote': 'FEFO-2026-SYN1',
            'codigo_barras': '7801000001028',
            'nombre': 'Amoxicilina + Ácido Clavulánico 250 mg (Synulox)',
            'categoria': 'MEDICAMENTO',
            'presentacion': 'Caja x 10 comprimidos palatables',
            'fecha_vencimiento': hoy + timedelta(days=16),
            'tiempo_limite_uso': 'Blíster abierto: máximo 14 días en ambiente seco (<25°C)',
            'stock_disponible': 22,
        },
        {
            'codigo_lote': 'FEFO-2026-MEL2',
            'codigo_barras': '7801000001035',
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
