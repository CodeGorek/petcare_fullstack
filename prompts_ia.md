# Registro de Apoyo de Inteligencia Artificial (`prompts_ia.md`)

**Asignatura:** Desarrollo Backend - Evaluación Parcial N°3
**Proyecto Asignado:** Proyecto 1 - Sistema de Gestión de Citas y Fichas Médicas para Veterinaria (PetCare)
**Arquitectura:** Django 5 + Django REST Framework (DRF) + PostgreSQL + AWS EC2

---

## Metodología de Ingeniería de Prompts Utilizada
Se empleó una secuencia estructurada de prompts incrementales (paso a paso) para asistir en la codificación de reglas de negocio, personalización del administrador, seguridad y scripts de despliegue en AWS EC2.

### Paso 1: Configuración de Arquitectura y Conexión a PostgreSQL
**Prompt enviado a la IA:**
> "Actúa como Arquitecto de Software experto en Django 5 y PostgreSQL. Necesito estructurar la configuración `settings.py` para el sistema veterinario 'PetCare' usando `python-dotenv` y `psycopg2-binary`. El sistema debe leer las credenciales de PostgreSQL (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) desde un archivo `.env`, configurar la zona horaria en `America/Santiago` y activar protecciones de sesión y cabeceras HTTP seguras."

**Resultado aplicado:**
Se implementó la carga dinámica de variables de entorno en `petcare/settings.py` permitiendo alternar limpiamente entre desarrollo y la instancia PostgreSQL local en AWS EC2.

---

### Paso 2: Modelado Relacional y Regla de Negocio Anti-Solapamiento
**Prompt enviado a la IA:**
> "Diseña en `clinica/models.py` los modelos del dominio para la clínica veterinaria PetCare: `Tutor` (con validador regex de RUT chileno), `Mascota`, `Veterinario` (con horario de inicio y fin de jornada), `CitaMedica`, `FichaClinica` y `RecordatorioVacuna`. Incorpora en el método `clean()` de `CitaMedica` y mediante `UniqueConstraint` la validación estricta que impida agendar dos citas activas al mismo veterinario en la misma fecha y hora, validando además que la hora esté dentro de su jornada laboral."

**Resultado aplicado:**
Se codificaron los 6 modelos relacionales en `clinica/models.py` incluyendo `UniqueConstraint` parcial en PostgreSQL y validación de negocio en `CitaMedica.clean()`.

---

### Paso 3: Personalización Avanzada de Django Admin con Templates
**Prompt enviado a la IA:**
> "Configura `clinica/admin.py` y el template `templates/admin/base_site.html` para personalizar el administrador de Django del proyecto PetCare. Todos los modelos deben incluir `list_display`, `list_filter`, `search_fields`, `inlines` de mascotas dentro de tutores y funciones visuales con `format_html` que muestren badges de colores según el estado de las citas y el nivel de alerta de vacunación (vencido, próximo <= 7 días, al día)."

**Resultado aplicado:**
Se personalizaron las vistas administrativas y la cabecera institucional mediante `templates/admin/base_site.html` junto con indicadores semafóricos en `clinica/admin.py`.

---

### Paso 4: Serializadores DRF, API de Disponibilidad y Automatización de Vacunas
**Prompt enviado a la IA:**
> "Genera los serializadores y `ModelViewSet` en Django REST Framework para exponer el CRUD completo en `/api/`. Adicionalmente, crea un endpoint AJAX en `clinica/views.py` que reciba `veterinario_id` y `fecha` y devuelva los bloques de 30 minutos disponibles descontando las citas programadas. Finalmente, agrega la regla de negocio para que al marcar una vacuna como `APLICADA`, se genere automáticamente el recordatorio del refuerzo anual (+365 días)."

**Resultado aplicado:**
Se implementaron los `ViewSets` protegidos con `IsAuthenticated`, el endpoint `/agenda/disponibilidad/` consumido vía Fetch API en el frontend y la creación automática del refuerzo anual en `marcar_recordatorio_aplicado`.

---

### Paso 5: Puesta en Producción sobre AWS EC2 (PostgreSQL + Gunicorn + Nginx)
**Prompt enviado a la IA:**
> "Genera una guía paso a paso para Ubuntu Server en AWS EC2 que instale PostgreSQL, cree la base de datos `petcare_db`, configure el servicio systemd de Gunicorn para el proyecto Django y publique la aplicación en el puerto 80 mediante Nginx."

**Resultado aplicado:**
Se documentó y automatizó el flujo de despliegue en `README.md` para la defensa en vivo en AWS Academy.

---

### Paso 6: Rediseño de Interfaz SaaS, Control de Roles (RBAC) y Manejo de Errores HTTP (404/403)
**Prompt enviado a la IA:**
> "Actualiza el frontend a un dashboard clínico SaaS con Bootstrap 5.3 y barra lateral fija. Implementa control de acceso basado en roles (RBAC) donde únicamente el superusuario (`admin`) pueda visualizar y acceder a Django Admin, API REST (DRF) y al módulo `/usuarios/` para crear cuentas profesionales de veterinarios y recepción. Agrega vistas personalizadas para errores HTTP 404 y 403 con retorno al panel principal."

**Resultado aplicado:**
Se implementó el decorador `@user_passes_test(es_root)` en las vistas administrativas, `IsAdminUser` en DRF, creación automatizada de cuentas profesionales vinculadas a la agenda médica y plantillas `404.html` / `403.html` integradas en `petcare/urls.py`.
