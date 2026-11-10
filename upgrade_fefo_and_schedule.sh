#!/usr/bin/env bash
set -e

if [ -d "petcare_fullstack" ]; then
    cd petcare_fullstack
fi

# 1. ACTUALIZAR MODELOS: Agregar categoría (Medicamento/Insumo) y tiempo límite de uso tras apertura en LoteMedicamento + hora_programada en RecordatorioVacuna
cat << 'PYEOF' > patch_models.py
with open('clinica/models.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_lote = """class LoteMedicamento(models.Model):
    nombre = models.CharField('Medicamento / Insumo', max_length=120)
    codigo_lote = models.CharField('Código de Lote (Norma FEFO)', max_length=50, unique=True)
    presentacion = models.CharField('Presentación / Concentración', max_length=80, default='Comprimidos / Frasco Ampolla')
    fecha_vencimiento = models.DateField('Fecha de Vencimiento (FEFO)')
    stock_disponible = models.PositiveIntegerField('Unidades en Stock', default=10)
    activo = models.BooleanField('Habilitado para Dispensación', default=True)"""

new_lote = """class LoteMedicamento(models.Model):
    CATEGORIAS = [
        ('MEDICAMENTO', 'Medicamento / Fármaco'),
        ('VACUNA_BIO', 'Biológico / Vacuna'),
        ('INSUMO', 'Insumo Clínico / Quirúrgico'),
    ]
    nombre = models.CharField('Medicamento / Insumo', max_length=120)
    categoria = models.CharField('Categoría', max_length=20, choices=CATEGORIAS, default='MEDICAMENTO')
    codigo_lote = models.CharField('Código de Lote (Norma FEFO)', max_length=50, unique=True)
    presentacion = models.CharField('Presentación / Concentración', max_length=80, default='Comprimidos / Frasco Ampolla')
    fecha_vencimiento = models.DateField('Fecha Límite Vencimiento (FEFO)')
    tiempo_limite_uso = models.CharField(
        'Tiempo Límite de Uso (Abierto / Reconstituido)',
        max_length=100,
        default='Usar hasta fecha de vencimiento (Envase sellado)'
    )
    stock_disponible = models.PositiveIntegerField('Unidades en Stock', default=10)
    activo = models.BooleanField('Habilitado para Dispensación', default=True)"""

code = code.replace(old_lote, new_lote)

old_rec = """    nombre_vacuna_control = models.CharField('Vacuna, Examen o Control', max_length=120)
    fecha_programada = models.DateField('Fecha Programada')"""

new_rec = """    nombre_vacuna_control = models.CharField('Vacuna, Examen o Control', max_length=120)
    fecha_programada = models.DateField('Fecha Programada')
    hora_programada = models.TimeField('Hora de Citación', default='10:00')"""

code = code.replace(old_rec, new_rec)
code = code.replace("ordering = ['fecha_programada']", "ordering = ['fecha_programada', 'hora_programada']")

with open('clinica/models.py', 'w', encoding='utf-8') as f:
    f.write(code)
PYEOF
python patch_models.py
rm patch_models.py

# 2. ACTUALIZAR FORMULARIOS: Incluir categoria y tiempo_limite_uso en LoteMedicamentoForm + hora_programada en RecordatorioVacunaForm
cat << 'PYEOF' > patch_forms.py
with open('clinica/forms.py', 'r', encoding='utf-8') as f:
    forms_code = f.read()

old_lote_form = """class LoteMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['nombre', 'codigo_lote', 'presentacion', 'fecha_vencimiento', 'stock_disponible']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Amoxicilina + Ácido Clavulánico 250mg'}),
            'codigo_lote': forms.TextInput(attrs={'placeholder': 'Ej: LOTE-2026-A9'}),
            'presentacion': forms.TextInput(attrs={'placeholder': 'Ej: Caja 10 comprimidos / Frasco 50ml'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
            'stock_disponible': forms.NumberInput(attrs={'min': '1', 'max': '5000'}),
        }"""

new_lote_form = """class LoteMedicamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LoteMedicamento
        fields = ['nombre', 'categoria', 'codigo_lote', 'presentacion', 'fecha_vencimiento', 'tiempo_limite_uso', 'stock_disponible']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Meloxicam Inyectable 2% / Catéter IV 22G'}),
            'codigo_lote': forms.TextInput(attrs={'placeholder': 'Ej: FEFO-2026-M12'}),
            'presentacion': forms.TextInput(attrs={'placeholder': 'Ej: Frasco ampolla 50ml / Caja x 50 u.'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'tiempo_limite_uso': forms.TextInput(attrs={'placeholder': 'Ej: 28 días tras primera punción (entre 2°C y 8°C)'}),
            'stock_disponible': forms.NumberInput(attrs={'min': '1', 'max': '5000'}),
        }"""

forms_code = forms_code.replace(old_lote_form, new_lote_form)

old_rec_form = """    class Meta:
        model = RecordatorioVacuna
        fields = ['mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'estado', 'notificado', 'observaciones']
        widgets = {
            'nombre_vacuna_control': forms.TextInput(attrs={'placeholder': 'Ej: Vacuna Óctuple / Examen Bioquímico / Control Renal'}),
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Indicaciones previas (ej. ayuno 8 hrs)'}),
        }"""

new_rec_form = """    class Meta:
        model = RecordatorioVacuna
        fields = ['mascota', 'tipo', 'nombre_vacuna_control', 'fecha_programada', 'hora_programada', 'estado', 'notificado', 'observaciones']
        widgets = {
            'nombre_vacuna_control': forms.TextInput(attrs={'placeholder': 'Ej: Vacuna Óctuple / Examen Bioquímico / Control Renal'}),
            'fecha_programada': forms.DateInput(attrs={'type': 'date'}),
            'hora_programada': forms.TimeInput(attrs={'type': 'time'}),
            'observaciones': forms.TextInput(attrs={'placeholder': 'Indicaciones previas (ej. ayuno 8 hrs)'}),
        }"""

forms_code = forms_code.replace(old_rec_form, new_rec_form)

with open('clinica/forms.py', 'w', encoding='utf-8') as f:
    f.write(forms_code)
PYEOF
python patch_forms.py
rm patch_forms.py

# 3. ACTUALIZAR VISTA DASHBOARD PARA ENVIAR ALERTAS FEFO Y HORAS DE CITAS
cat << 'PYEOF' > patch_views.py
with open('clinica/views.py', 'r', encoding='utf-8') as f:
    v_code = f.read()

old_dash = """@login_required
def dashboard(request):
    hoy = date.today()
    citas_hoy = CitaMedica.objects.filter(fecha=hoy).select_related('mascota', 'veterinario')
    recordatorios_todos = RecordatorioVacuna.objects.select_related('mascota', 'mascota__tutor').filter(mascota__activo=True)
    alertas_urgentes = [r for r in recordatorios_todos if r.estado_asistencia in ('NO_ASISTIO', 'PROXIMO') and r.estado != 'ASISTIO']
    lotes_por_vencer = LoteMedicamento.objects.filter(activo=True, fecha_vencimiento__lte=hoy + timedelta(days=30)).order_by('fecha_vencimiento')

    context = {
        'total_tutores': Tutor.objects.filter(activo=True).count(),
        'total_mascotas': Mascota.objects.filter(activo=True).count(),
        'citas_hoy_count': citas_hoy.count(),
        'citas_hoy': citas_hoy,
        'alertas_urgentes': alertas_urgentes,
        'lotes_por_vencer': lotes_por_vencer,
        'ultimas_fichas': FichaClinica.objects.select_related('mascota', 'veterinario', 'medicamento_fefo')[:5],
    }
    return render(request, 'clinica/dashboard.html', context)"""

new_dash = """@login_required
def dashboard(request):
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
    return render(request, 'clinica/dashboard.html', context)"""

v_code = v_code.replace(old_dash, new_dash)
with open('clinica/views.py', 'w', encoding='utf-8') as f:
    f.write(v_code)
PYEOF
python patch_views.py
rm patch_views.py

# 4. ACTUALIZAR DASHBOARD.HTML: KPI de Alerta de Medicamentos por Vencer (Norma FEFO), Tabla FEFO con Días Restantes y Tiempo Límite de Uso, y Fechas + Horas en Citas/Fichas/Vacunas
cat << 'HTMLEOF' > templates/clinica/dashboard.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Centro de Control Clínico y Trazabilidad FEFO</h4>
    <p class="text-muted small mb-0">Monitoreo en tiempo real de agenda con fecha/hora, expediente clínico, control de asistencia y vencimiento de fármacos/insumos.</p>
  </div>
  <div class="d-flex gap-2">
    <span class="badge badge-soft-success px-3 py-2 rounded-pill"><i class="bi bi-database-fill-check me-1"></i> Sincronizado con PostgreSQL 16</span>
  </div>
</div>

<!-- 4 KPIs Superiores -->
<div class="row g-3 mb-4">
  <div class="col-sm-6 col-xl-3">
    <div class="kpi-card d-flex align-items-center justify-content-between">
      <div>
        <div class="text-muted small fw-semibold mb-1">Tutores Registrados</div>
        <h2 class="fw-bold mb-0">{{ total_tutores }}</h2>
        <small class="text-success fw-semibold"><i class="bi bi-person-check"></i> Verificados con RUT Mód. 11</small>
      </div>
      <div class="kpi-icon badge-soft-info"><i class="bi bi-people-fill"></i></div>
    </div>
  </div>
  <div class="col-sm-6 col-xl-3">
    <div class="kpi-card d-flex align-items-center justify-content-between">
      <div>
        <div class="text-muted small fw-semibold mb-1">Pacientes Activos</div>
        <h2 class="fw-bold mb-0">{{ total_mascotas }}</h2>
        <small class="text-primary fw-semibold"><i class="bi bi-folder2-open"></i> Ficha clínica electrónica</small>
      </div>
      <div class="kpi-icon badge-soft-purple">🐾</div>
    </div>
  </div>
  <div class="col-sm-6 col-xl-3">
    <div class="kpi-card d-flex align-items-center justify-content-between">
      <div>
        <div class="text-muted small fw-semibold mb-1">Citas Programadas Hoy</div>
        <h2 class="fw-bold mb-0">{{ citas_hoy_count }}</h2>
        <small class="text-secondary"><i class="bi bi-clock-history"></i> Bloques con Fecha y Hora</small>
      </div>
      <div class="kpi-icon badge-soft-success"><i class="bi bi-calendar2-check-fill"></i></div>
    </div>
  </div>
  <div class="col-sm-6 col-xl-3">
    <div class="kpi-card d-flex align-items-center justify-content-between" style="border-left: 4px solid #ef4444;">
      <div>
        <div class="text-danger small fw-bold mb-1">Alerta Medicamentos FEFO</div>
        <h2 class="fw-bold text-danger mb-0">{{ lotes_alerta_fefo|length }}</h2>
        <small class="text-danger"><i class="bi bi-capsule-pill"></i> Por vencer (&le;45 días) / Críticos</small>
      </div>
      <div class="kpi-icon badge-soft-danger"><i class="bi bi-exclamation-triangle-fill"></i></div>
    </div>
  </div>
</div>

<div class="row g-4 mb-4">
  <!-- Agenda Médica de Hoy con Fecha y Hora -->
  <div class="col-lg-6">
    <div class="saas-card h-100">
      <div class="saas-card-header">
        <div>
          <h6 class="fw-bold mb-0"><i class="bi bi-calendar-event text-primary me-2"></i>Citas Médicas de Hoy (Fecha y Hora)</h6>
          <small class="text-muted">Control de bloques horarios y asistencia de pacientes</small>
        </div>
        <a href="{% url 'agenda_citas' %}" class="btn btn-sm btn-light border fw-semibold">Ver Agenda Completa</a>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Fecha y Hora</th><th>Paciente / Tutor</th><th>Profesional</th><th>Asistencia</th><th class="text-end">Acción</th></tr>
          </thead>
          <tbody>
          {% for c in citas_hoy %}
            <tr>
              <td>
                <div class="fw-bold">{{ c.fecha|date:"d/m/Y" }}</div>
                <span class="badge bg-dark font-monospace">{{ c.hora|time:"H:i" }} hrs</span>
              </td>
              <td>
                <div class="fw-bold">{{ c.mascota.nombre }}</div>
                <small class="text-muted">{{ c.mascota.tutor.nombre_completo }}</small>
              </td>
              <td>
                <div class="fw-semibold">Dr(a). {{ c.veterinario.nombre }}</div>
                <small class="text-muted">{{ c.motivo|truncatechars:28 }}</small>
              </td>
              <td>
                {% if c.estado == 'ASISTIO' %}
                  <span class="badge badge-soft-success rounded-pill px-3">Asistió</span>
                {% elif c.estado == 'NO_ASISTIO' %}
                  <span class="badge badge-soft-danger rounded-pill px-3">No Asistió</span>
                {% elif c.estado == 'PROGRAMADA' %}
                  <span class="badge badge-soft-info rounded-pill px-3">Programada</span>
                {% else %}
                  <span class="badge bg-secondary rounded-pill px-3">Cancelada</span>
                {% endif %}
              </td>
              <td class="text-end">
                {% if c.estado == 'PROGRAMADA' %}
                <div class="btn-group btn-group-sm">
                  <form method="post" action="{% url 'cambiar_estado_cita' c.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-success me-1" title="Marcar Asistió"><i class="bi bi-check-lg"></i></button>
                  </form>
                  <form method="post" action="{% url 'cambiar_estado_cita' c.id 'NO_ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-outline-danger" title="Marcar No Asistió"><i class="bi bi-x-lg"></i></button>
                  </form>
                </div>
                {% endif %}
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="5" class="text-center text-muted py-4">No hay citas programadas para hoy.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Control de Asistencia a Vacunas, Exámenes y Controles (Con Fecha y Hora) -->
  <div class="col-lg-6">
    <div class="saas-card h-100">
      <div class="saas-card-header">
        <div>
          <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-clipboard2-check-fill me-2"></i>Citaciones a Vacunas, Exámenes y Controles</h6>
          <small class="text-muted">Registro de Fecha, Hora y estado de concurrencia (Asistió / No Asistió)</small>
        </div>
        <a href="{% url 'recordatorios_vacunas' %}" class="btn btn-sm btn-light border fw-semibold">Gestionar</a>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Paciente</th><th>Prestación</th><th>Fecha y Hora</th><th>Asistencia</th><th class="text-end">Marcar</th></tr>
          </thead>
          <tbody>
          {% for a in recordatorios_agenda %}
            <tr>
              <td>
                <div class="fw-bold">{{ a.mascota.nombre }}</div>
                <small class="text-muted"><i class="bi bi-telephone"></i> {{ a.mascota.tutor.telefono }}</small>
              </td>
              <td>
                <span class="badge bg-light text-dark border" style="font-size:0.68rem;">{{ a.get_tipo_display }}</span>
                <div class="fw-semibold">{{ a.nombre_vacuna_control }}</div>
              </td>
              <td>
                <div class="fw-bold">{{ a.fecha_programada|date:"d/m/Y" }}</div>
                <span class="badge bg-secondary font-monospace">{{ a.hora_programada|time:"H:i" }} hrs</span>
              </td>
              <td>
                {% if a.estado_asistencia == 'ASISTIO' %}
                  <span class="badge badge-soft-success rounded-pill px-2"><i class="bi bi-check-circle me-1"></i>Asistió</span>
                {% elif a.estado_asistencia == 'NO_ASISTIO' %}
                  <span class="badge badge-soft-danger rounded-pill px-2"><i class="bi bi-x-circle me-1"></i>No Asistió</span>
                {% elif a.estado_asistencia == 'PROXIMO' %}
                  <span class="badge badge-soft-warning rounded-pill px-2">Próximo (&le;7d)</span>
                {% else %}
                  <span class="badge badge-soft-info rounded-pill px-2">Pendiente</span>
                {% endif %}
              </td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' a.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-emerald py-1 px-2 me-1" title="Marcar que Asistió">Asistió</button>
                  </form>
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' a.id 'NO_ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-outline-danger py-1 px-2" title="Marcar que No Asistió">No</button>
                  </form>
                </div>
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="5" class="text-center text-muted py-4">Sin citaciones pendientes.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- NUEVO PANEL CENTRAL: Alerta de Medicamentos e Insumos por Vencer según Norma FEFO -->
<div class="saas-card mb-4" style="border-left: 4px solid #f59e0b;">
  <div class="saas-card-header">
    <div>
      <h6 class="fw-bold mb-0 text-dark">
        <i class="bi bi-capsule-pill text-danger me-2"></i>Alertas de Medicamentos e Insumos por Vencer — Norma FEFO (First Expired, First Out)
      </h6>
      <small class="text-muted">Prioridad de salida según días restantes para caducidad y tiempo límite de estabilidad tras apertura</small>
    </div>
    <a href="{% url 'farmacia_fefo' %}" class="btn btn-sm btn-emerald">
      <i class="bi bi-box-seam me-1"></i> Administrar Base de Datos FEFO
    </a>
  </div>
  <div class="table-responsive">
    <table class="table table-saas mb-0">
      <thead>
        <tr>
          <th>Prioridad FEFO</th>
          <th>Medicamento / Insumo Clínico</th>
          <th>Categoría</th>
          <th>Lote</th>
          <th>Fecha Vencimiento</th>
          <th>Días Restantes</th>
          <th>Tiempo Límite para Usarse (Abierto)</th>
          <th>Stock</th>
        </tr>
      </thead>
      <tbody>
      {% for l in lotes_inventario %}
        <tr>
          <td>
            {% if l.esta_vencido %}
              <span class="badge badge-soft-danger rounded-pill px-2"><i class="bi bi-lock-fill me-1"></i>BLOQUEADO</span>
            {% elif l.dias_para_vencer <= 30 %}
              <span class="badge badge-soft-warning rounded-pill px-2"><i class="bi bi-lightning-fill me-1"></i>1° USAR AHORA</span>
            {% else %}
              <span class="badge badge-soft-success rounded-pill px-2">Orden #{{ forloop.counter }} FEFO</span>
            {% endif %}
          </td>
          <td>
            <div class="fw-bold">{{ l.nombre }}</div>
            <small class="text-muted">{{ l.presentacion }}</small>
          </td>
          <td><span class="badge bg-light text-dark border">{{ l.get_categoria_display }}</span></td>
          <td><span class="badge bg-dark font-monospace">{{ l.codigo_lote }}</span></td>
          <td class="fw-bold">{{ l.fecha_vencimiento|date:"d/m/Y" }}</td>
          <td>
            {% if l.esta_vencido %}
              <span class="text-danger fw-bold">Vencido hace {{ l.dias_para_vencer|cut:"-" }} días</span>
            {% elif l.dias_para_vencer <= 30 %}
              <span class="text-danger fw-bold"><i class="bi bi-hourglass-split"></i> Quedan {{ l.dias_para_vencer }} días</span>
            {% else %}
              <span class="text-success fw-semibold">{{ l.dias_para_vencer }} días restantes</span>
            {% endif %}
          </td>
          <td>
            <span class="small text-secondary"><i class="bi bi-clock-history text-primary me-1"></i>{{ l.tiempo_limite_uso }}</span>
          </td>
          <td class="fw-bold">{{ l.stock_disponible }} u.</td>
        </tr>
      {% empty %}
        <tr><td colspan="8" class="text-center text-muted py-3">Sin insumos ni medicamentos cargados.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<!-- Últimas Atenciones y Fichas Clínicas con Fecha, Hora de Atención y Hora de Cita -->
<div class="saas-card mb-4">
  <div class="saas-card-header">
    <div>
      <h6 class="fw-bold mb-0"><i class="bi bi-journal-medical text-success me-2"></i>Últimas Atenciones y Fichas Clínicas Emitidas (Con Fecha, Hora y Lote FEFO)</h6>
    </div>
    <a href="{% url 'fichas_clinicas' %}" class="btn btn-sm btn-outline-dark">Historial Completo</a>
  </div>
  <div class="table-responsive">
    <table class="table table-saas mb-0">
      <thead>
        <tr><th>Ficha</th><th>Paciente</th><th>Fecha y Hora Atención</th><th>Veterinario</th><th>Signos Vitales</th><th>Diagnóstico, Receta y Lote FEFO</th><th class="text-end">Imprimir</th></tr>
      </thead>
      <tbody>
      {% for f in ultimas_fichas %}
        <tr>
          <td class="fw-bold text-secondary">#{{ f.id }}</td>
          <td>
            <div class="fw-bold">{{ f.mascota.nombre }}</div>
            <small class="text-muted">{{ f.mascota.tutor.nombre_completo }}</small>
          </td>
          <td>
            <div class="fw-bold">{{ f.fecha_atencion|date:"d/m/Y" }}</div>
            <span class="badge bg-dark font-monospace">{{ f.fecha_atencion|date:"H:i" }} hrs</span>
            {% if f.cita %}
              <small class="d-block text-success">Cita: {{ f.cita.hora|time:"H:i" }} hrs (Asistió)</small>
            {% endif %}
          </td>
          <td>Dr(a). {{ f.veterinario.nombre }}</td>
          <td>
            <span class="badge bg-light text-dark border me-1">{{ f.peso_registrado }} kg</span>
            <span class="badge bg-light text-dark border">{{ f.temperatura_c }} °C</span>
          </td>
          <td>
            <div class="fw-semibold">{{ f.diagnostico|truncatechars:55 }}</div>
            {% if f.medicamento_fefo %}
              <span class="badge badge-soft-success" style="font-size:0.7rem;">FEFO: {{ f.medicamento_fefo.nombre }} (Lote {{ f.medicamento_fefo.codigo_lote }})</span>
            {% endif %}
            {% if f.receta_medica %}<small class="d-block text-primary"><i class="bi bi-capsule"></i> {{ f.receta_medica|truncatechars:55 }}</small>{% endif %}
          </td>
          <td class="text-end">
            <a href="{% url 'imprimir_ficha_individual' f.id %}" target="_blank" class="btn btn-sm btn-light border" title="Imprimir Solo Esta Ficha">
              <i class="bi bi-printer-fill text-success"></i>
            </a>
          </td>
        </tr>
      {% empty %}
        <tr><td colspan="7" class="text-center text-muted py-3">Sin fichas registradas aún.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<!-- Analítica Clínica en Tiempo Real -->
<div class="row g-4">
  <div class="col-md-6">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-pie-chart-fill text-primary me-2"></i>Distribución de Pacientes por Especie</h6>
      <div style="max-height: 220px;" class="d-flex justify-content-center">
        <canvas id="chartEspecies"></canvas>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-bar-chart-fill text-success me-2"></i>Estado de Asistencia en Agenda Médica</h6>
      <div style="max-height: 220px;" class="d-flex justify-content-center">
        <canvas id="chartCitas"></canvas>
      </div>
    </div>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<script>
fetch('/metricas-json/')
  .then(r => r.json())
  .then(data => {
    new Chart(document.getElementById('chartEspecies'), {
      type: 'doughnut',
      data: {
        labels: data.especies.map(e => e.especie),
        datasets: [{ data: data.especies.map(e => e.total), backgroundColor: ['#10b981', '#6366f1', '#f59e0b'] }]
      },
      options: { plugins: { legend: { position: 'bottom' } } }
    });
    new Chart(document.getElementById('chartCitas'), {
      type: 'bar',
      data: {
        labels: data.estados_citas.map(c => c.estado),
        datasets: [{ label: 'Total Citas', data: data.estados_citas.map(c => c.total), backgroundColor: '#0ea5e9', borderRadius: 6 }]
      },
      options: { plugins: { legend: { display: false } } }
    });
  });
</script>
{% endblock %}
HTMLEOF

# 5. ACTUALIZAR FARMACIA_FEFO.HTML Y RECORDATORIOS.HTML PARA MOSTRAR TIEMPO LÍMITE DE USO Y HORA DE CITACIÓN
cat << 'HTMLEOF' > templates/clinica/farmacia_fefo.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Base de Datos de Medicamentos e Insumos Clínicos — Norma FEFO</h4>
    <p class="text-muted small mb-0"><strong>FEFO (First Expired, First Out):</strong> Ordenamiento estricto por días restantes hasta el vencimiento y control del tiempo límite de uso tras apertura.</p>
  </div>
</div>

<div class="row g-4">
  <div class="col-lg-4">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-capsule text-success me-2"></i>Registrar Lote de Medicamento o Insumo</h6>
      <form method="post">
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-12"><label class="form-label">Nombre de Medicamento o Insumo</label>{{ form.nombre }}</div>
          <div class="col-md-6"><label class="form-label">Categoría</label>{{ form.categoria }}</div>
          <div class="col-md-6"><label class="form-label">Código de Lote</label>{{ form.codigo_lote }}</div>
          <div class="col-md-8"><label class="form-label">Presentación</label>{{ form.presentacion }}</div>
          <div class="col-md-4"><label class="form-label">Stock</label>{{ form.stock_disponible }}</div>
          <div class="col-12"><label class="form-label">Fecha de Vencimiento (Criterio FEFO)</label>{{ form.fecha_vencimiento }}</div>
          <div class="col-12"><label class="form-label">Tiempo Límite para Usarse (Una vez abierto)</label>{{ form.tiempo_limite_uso }}</div>
          <div class="col-12 pt-2">
            <button type="submit" class="btn btn-emerald w-100 py-2">
              <i class="bi bi-plus-circle me-1"></i> Guardar en Base de Datos FEFO
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-sort-numeric-down text-primary me-2"></i>Catálogo de Farmacia e Insumos Ordenado por Vencimiento ({{ lotes|length }})</h6>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Prioridad FEFO</th><th> Fármaco / Insumo</th><th>Lote</th><th>Vencimiento y Días Restantes</th><th>Tiempo Límite de Uso</th><th>Stock</th></tr>
          </thead>
          <tbody>
          {% for l in lotes %}
            <tr>
              <td>
                {% if l.esta_vencido %}
                  <span class="badge badge-soft-danger rounded-pill px-2">BLOQUEADO</span>
                {% elif l.dias_para_vencer <= 30 %}
                  <span class="badge badge-soft-warning rounded-pill px-2">1° EN SALIR (&le;30d)</span>
                {% else %}
                  <span class="badge badge-soft-success rounded-pill px-2">#{{ forloop.counter }} Vigente</span>
                {% endif %}
              </td>
              <td>
                <div class="fw-bold">{{ l.nombre }}</div>
                <small class="text-muted">{{ l.get_categoria_display }} • {{ l.presentacion }}</small>
              </td>
              <td><span class="badge bg-dark font-monospace">{{ l.codigo_lote }}</span></td>
              <td>
                <div class="fw-bold">{{ l.fecha_vencimiento|date:"d/m/Y" }}</div>
                {% if l.esta_vencido %}
                  <small class="text-danger fw-bold">Vencido hace {{ l.dias_para_vencer|cut:"-" }} días</small>
                {% elif l.dias_para_vencer <= 30 %}
                  <small class="text-danger fw-bold">Quedan {{ l.dias_para_vencer }} días</small>
                {% else %}
                  <small class="text-success fw-semibold">Quedan {{ l.dias_para_vencer }} días</small>
                {% endif %}
              </td>
              <td><small class="text-secondary"><i class="bi bi-clock-history text-primary me-1"></i>{{ l.tiempo_limite_uso }}</small></td>
              <td class="fw-bold">{{ l.stock_disponible }} u.</td>
            </tr>
          {% empty %}
            <tr><td colspan="6" class="text-center py-4 text-muted">Sin lotes registrados.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
HTMLEOF

cat << 'HTMLEOF' > templates/clinica/recordatorios.html
{% extends "clinica/base.html" %}
{% block content %}
<div class="d-flex flex-wrap justify-content-between align-items-center mb-4">
  <div>
    <h4 class="fw-bold mb-1">Control de Asistencia a Vacunaciones, Exámenes y Controles</h4>
    <p class="text-muted small mb-0">Cada citación incluye <strong>Fecha y Hora exacta</strong> y registra si el paciente <strong>Asistió</strong> o <strong>No Asistió</strong>.</p>
  </div>
</div>

<div class="row g-4">
  <div class="col-lg-4">
    <div class="saas-card p-4">
      <h6 class="fw-bold mb-3"><i class="bi bi-calendar2-plus text-success me-2"></i>Programar Vacuna, Examen o Control</h6>
      <form method="post">
        {% csrf_token %}
        <div class="row g-3">
          <div class="col-12"><label class="form-label">Paciente Activo</label>{{ form.mascota }}</div>
          <div class="col-12"><label class="form-label">Tipo de Citación</label>{{ form.tipo }}</div>
          <div class="col-md-6"><label class="form-label">Fecha Programada</label>{{ form.fecha_programada }}</div>
          <div class="col-md-6"><label class="form-label">Hora de Citación</label>{{ form.hora_programada }}</div>
          <div class="col-12"><label class="form-label">Vacuna, Examen o Control</label>{{ form.nombre_vacuna_control }}</div>
          <div class="col-md-7"><label class="form-label">Estado de Asistencia</label>{{ form.estado }}</div>
          <div class="col-md-5 d-flex align-items-end">
            <div class="form-check mb-2">
              {{ form.notificado }} <label class="form-check-label small fw-semibold">Notificado</label>
            </div>
          </div>
          <div class="col-12"><label class="form-label">Observaciones / Preparación</label>{{ form.observaciones }}</div>
          <div class="col-12 pt-2">
            <button type="submit" class="btn btn-emerald w-100 py-2">
              <i class="bi bi-check2-circle me-1"></i> Guardar Citación con Hora
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="col-lg-8">
    <div class="saas-card">
      <div class="saas-card-header">
        <h6 class="fw-bold mb-0"><i class="bi bi-clipboard2-check text-primary me-2"></i>Registro de Asistencia con Fecha y Hora ({{ recordatorios|length }})</h6>
      </div>
      <div class="table-responsive">
        <table class="table table-saas mb-0">
          <thead>
            <tr><th>Paciente / Tutor</th><th>Tipo / Prestación</th><th>Fecha y Hora</th><th>Estado Asistencia</th><th class="text-end">Marcar Asistencia</th></tr>
          </thead>
          <tbody>
          {% for r in recordatorios %}
            <tr>
              <td>
                <div class="fw-bold">{{ r.mascota.nombre }}</div>
                <small class="text-muted">{{ r.mascota.tutor.nombre_completo }} • {{ r.mascota.tutor.telefono }}</small>
              </td>
              <td>
                <span class="badge bg-light text-dark border">{{ r.get_tipo_display }}</span>
                <div class="fw-semibold mt-1">{{ r.nombre_vacuna_control }}</div>
              </td>
              <td>
                <div class="fw-bold">{{ r.fecha_programada|date:"d/m/Y" }}</div>
                <span class="badge bg-dark font-monospace">{{ r.hora_programada|time:"H:i" }} hrs</span>
              </td>
              <td>
                {% if r.estado_asistencia == 'ASISTIO' %}
                  <span class="badge badge-soft-success rounded-pill px-3 py-1"><i class="bi bi-check-circle-fill me-1"></i>ASISTIÓ</span>
                {% elif r.estado_asistencia == 'NO_ASISTIO' %}
                  <span class="badge badge-soft-danger rounded-pill px-3 py-1"><i class="bi bi-x-circle-fill me-1"></i>NO ASISTIÓ</span>
                {% elif r.estado_asistencia == 'PROXIMO' %}
                  <span class="badge badge-soft-warning rounded-pill px-3 py-1"><i class="bi bi-clock-fill me-1"></i>PRÓXIMO (&le;7d)</span>
                {% else %}
                  <span class="badge badge-soft-info rounded-pill px-3 py-1">PENDIENTE</span>
                {% endif %}
              </td>
              <td class="text-end">
                <div class="d-flex justify-content-end gap-1">
                  <a href="https://wa.me/{{ r.mascota.tutor.telefono|cut:'+'|cut:' ' }}?text=Hola%20{{ r.mascota.tutor.nombre_completo }},%20recordatorio%20PetCare%20para%20{{ r.mascota.nombre }}:%20{{ r.nombre_vacuna_control }}%20el%20{{ r.fecha_programada|date:'d/m/Y' }}%20a%20las%20{{ r.hora_programada|time:'H:i' }}%20hrs." target="_blank" class="btn btn-sm btn-outline-success" title="Avisar por WhatsApp">
                    <i class="bi bi-whatsapp"></i>
                  </a>
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' r.id 'ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-emerald">Asistió</button>
                  </form>
                  <form method="post" action="{% url 'actualizar_asistencia_recordatorio' r.id 'NO_ASISTIO' %}">
                    {% csrf_token %}
                    <button class="btn btn-sm btn-outline-danger">No Asistió</button>
                  </form>
                </div>
              </td>
            </tr>
          {% empty %}
            <tr><td colspan="5" class="text-center py-4 text-muted">Sin registros.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
HTMLEOF

# 6. POBLAR BASE DE DATOS CON EJEMPLOS REALISTAS DE MEDICAMENTOS E INSUMOS FEFO, CITAS DE HOY Y CITACIONES CON HORA
cat << 'PYEOF' > clinica/management/commands/seed_petcare.py
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
PYEOF

python manage.py makemigrations clinica
python manage.py migrate
python manage.py seed_petcare
rm upgrade_fefo_and_schedule.sh
echo "Panel general y base de datos FEFO actualizados con éxito."
