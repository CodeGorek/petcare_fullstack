# PetCare: precios y Webpay Plus de prueba

Esta actualización agrega precios y cuentas de atención vinculadas a las fichas clínicas existentes. Solo permite el ambiente oficial de integración de Transbank: no hace cobros reales. No cambia la configuración de Nginx ni el comando seed_petcare.

## Qué incluye y dónde

| Archivo | Función |
| --- | --- |
| clinica/models.py | Precio por unidad de lote, catálogo de servicios, cuenta por ficha, detalle de cobro y pagos |
| clinica/migrations/0004_cobros_webpay_prueba.py | Nuevas tablas y columna de precio, sin borrar datos anteriores |
| clinica/cobros_forms.py | Validación de precios y cantidades |
| clinica/cobros_views.py | Crear cuentas, agregar servicios, iniciar y confirmar pagos |
| clinica/webpay_service.py | SDK oficial, ambiente TEST fijo y verificación de monto/orden/sesión |
| clinica/cobros_urls.py | Rutas de cuentas, precios y retorno de Webpay |
| templates/clinica/ | Pantallas de precios, cuentas, detalle y envío al formulario oficial |
| clinica/management/commands/seed_precios_demo.py | Precios ficticios opcionales, sin reemplazar valores existentes |
| clinica/tests/test_cobros.py | Pruebas de pagos, permisos, totales, reintentos y conservación de stock |

Cada cuenta corresponde a una ficha. La dispensación de esa ficha se copia con su cantidad y precio por unidad; NO vuelve a descontar stock. Consulta, exámenes, vacunas y procedimientos se agregan desde el catálogo de servicios. No se cobra automáticamente por agendar o por tener un recordatorio.

Los precios se guardan como pesos chilenos enteros. Una cuenta conserva el precio copiado al agregar cada línea. Para fichas antiguas, se usan los precios configurados al crear su cuenta; no es una reconstrucción de precios históricos.

## 1. Aplicar el parche y subir la rama a GitHub

El ZIP contiene `petcare_webpay_prueba.patch`, este manual y `archivos/` con los archivos modificados para revisión. El parche está generado sobre el commit indicado en BASE_COMMIT.txt. No extraigas `archivos/` directamente sobre tu servidor: usa git apply, que detecta incompatibilidades.

En tu computador, descarga el ZIP y extrae su contenido. Desde una copia limpia del repositorio:

```bash
git clone https://github.com/CodeGorek/petcare_fullstack.git
cd petcare_fullstack
git switch -c feature/cobros-webpay-prueba
```

Si ya tienes una copia, revisa `git status` y guarda tus cambios antes de seguir. No necesitas clonar otra vez si esa copia está limpia y actualizada con main.

Reemplaza `/ruta/al/parche/` por la carpeta donde extrajiste el ZIP:

```bash
git apply --check /ruta/al/parche/petcare_webpay_prueba.patch
git apply --index /ruta/al/parche/petcare_webpay_prueba.patch
git diff --cached --stat
git commit -m "Agrega precios, cuentas y pagos Webpay de prueba"
git push -u origin feature/cobros-webpay-prueba
```

Ejecuta los comandos uno por uno. Si git apply muestra un error, detente y comparte la salida; no fuerces el reemplazo. Si Git solicita identidad, configura tu nombre y correo habituales antes del commit. Para push debes autenticarte con tu cuenta de GitHub.

La actualización queda en una rama revisable. Puedes desplegar esa rama para la demostración. Para incorporarla a main, abre un Pull Request en GitHub, revisa los cambios y fusiónalo. No se ha enviado ningún cambio a GitHub automáticamente desde este chat.

## 2. Respaldar la base de datos en EC2

Antes de ejecutar migraciones, respalda PostgreSQL. El siguiente ejemplo usa `petcare_db`, el nombre predeterminado del proyecto. Comprueba DB_NAME en tu .env y ajusta el nombre si es distinto.

```bash
mkdir -p ~/petcare_backups
chmod 700 ~/petcare_backups
backup_petcare=~/petcare_backups/petcare_$(date +%Y%m%d_%H%M%S).dump
sudo -u postgres pg_dump -Fc petcare_db > "$backup_petcare" && ls -lh "$backup_petcare"
```

Continúa solo si pg_dump terminó correctamente. Esto presupone PostgreSQL local, como en la configuración del proyecto. Si usas otra configuración de base de datos, adapta primero el respaldo.

## 3. Descargar la rama en EC2 conservando las correcciones anteriores

```bash
cd ~/petcare_fullstack
source venv/bin/activate
git status
```

Si el único archivo modificado es clinica/management/commands/seed_petcare.py (correcciones de RUT y decimales), conserva esos cambios temporalmente:

```bash
git stash push -m "Correcciones locales del seed antes de Webpay" -- clinica/management/commands/seed_petcare.py
```

Si aparecen otros archivos modificados, guarda y revisa esos cambios antes de cambiar de rama. No uses reset --hard ni elimines tu .env.

Descarga la rama que acabas de subir:

```bash
git fetch origin
git switch -c feature/cobros-webpay-prueba --track origin/feature/cobros-webpay-prueba
```

Si creaste el stash anterior, comprueba que el primero en `git stash list` sea «Correcciones locales del seed antes de Webpay» y recupéralo:

```bash
git stash pop
```

El parche no modifica seed_petcare.py. Revisa cualquier conflicto antes de continuar. Si ya estás en la rama feature/cobros-webpay-prueba en otra actualización, usa `git pull --ff-only` en lugar de volver a crearla.

Si prefieres desplegar main después de fusionar el Pull Request, selecciona esa rama y actualízala con `git pull --ff-only origin main`, conservando antes tus cambios locales del mismo modo.

## 4. Configurar la URL pública de retorno

Edita `.env` en EC2:

```bash
nano .env
```

Agrega o actualiza estas variables (sin duplicarlas):

```dotenv
WEBPAY_AMBIENTE=INTEGRACION
WEBPAY_BASE_URL=http://32.194.143.180
```

WEBPAY_BASE_URL debe ser la dirección pública exacta que usas para entrar a PetCare, sin barra al final. Si cambia la IP o agregas un dominio, actualiza esta variable y ALLOWED_HOSTS. No necesitas claves de producción: el SDK usa las credenciales oficiales de integración. El código rechaza el modo PRODUCCION.

## 5. Instalar, migrar y reiniciar

Con el entorno virtual activo, Python 3.12 o superior y el respaldo confirmado:

```bash
pip install -r requirements.txt &&
python manage.py migrate &&
python manage.py check &&
python manage.py collectstatic --noinput &&
sudo systemctl restart petcare &&
sudo systemctl status petcare --no-pager
```

No ejecutes nuevamente seed_petcare para instalar esta función. La nueva migración es 0004; no uses makemigrations en el servidor para recrearla.

Opcional, solo para poblar precios ficticios de una demostración:

```bash
python manage.py seed_precios_demo
```

Este comando crea servicios de ejemplo y asigna $2.000 por unidad a TODOS los lotes que todavía no tienen precio. Es un valor ficticio común para facilitar pruebas, NO un precio de mercado. No reemplaza precios ya configurados. Puedes omitir el comando y registrar todos los precios manualmente desde la aplicación.

## 6. Probar desde la página

1. Entra con el administrador y abre **Precios** en el menú lateral.
2. Registra los valores de consulta, procedimientos, exámenes y vacunas que utilizarás. Ajusta el precio de cada lote de medicamento según su unidad de stock.
3. Abre **Fichas Clínicas** y selecciona **Crear / ver cuenta** en una ficha.
4. El medicamento dispensado se agrega automáticamente. Si falta su precio, primero debes configurarlo. Agrega la consulta y otros servicios realizados, indicando cantidades.
5. Revisa el total y selecciona **Pagar con Webpay — Prueba**.
6. Pulsa **Continuar al formulario oficial de prueba** para abrir la página de Transbank.
7. Para un pago de prueba aprobado usa la tarjeta VISA `4051885600446623`, CVV `123`, y una fecha de vencimiento futura. En la simulación del banco usa RUT `11.111.111-1` y clave `123`.
8. Vuelve a PetCare y revisa que figure **Aprobado (prueba)**. Puedes imprimir un comprobante de prueba. No es una boleta tributaria.
9. Prueba también cancelar y rechazar el pago en el simulador.

Usa exclusivamente datos de prueba en el formulario de integración. Las instrucciones oficiales de tarjetas pueden cambiar; revisa los enlaces al final si los datos dejan de funcionar.

La consulta de cuentas requiere una sesión de usuario. El retorno externo acepta GET/POST sin depender de la sesión del navegador y confirma el resultado con Transbank antes de marcar la cuenta como pagada. Puede pedirte volver a iniciar sesión después del retorno.

## Reintentos y resultado pendiente

Una cuenta con un pago iniciado o aprobado no permite cambiar líneas ni iniciar otro cobro. Si falla la red al confirmar, la cuenta permanece por verificar; el botón **Verificar resultado en Webpay** intenta confirmar/consultar el mismo token. Un error de red nunca se interpreta como pago aprobado ni autoriza un segundo intento de cobro.

Un rechazo o una cancelación verificados dejan disponible un nuevo intento. Si se abandona el formulario, vence el token o el retorno llega sin identificador, vuelve a la cuenta y usa Verificar resultado. Si Webpay sigue sin dar un estado definitivo, la cuenta permanece bloqueada: revisa el registro del servicio en vez de forzar un pago nuevo o modificar estados en la base de datos.

```bash
sudo journalctl -u petcare -n 50 --no-pager
```

## Validación realizada

- 19 pruebas automáticas de Django con SQLite: aprobadas. Cubren aprobación, rechazo, cancelación, retorno GET/POST sin sesión, callbacks repetidos, datos alterados, errores de red, permisos, CSRF, total calculado en servidor, precios históricos y conservación de stock.
- Migraciones y check de Django: correctos; sin migraciones pendientes por generar.
- SDK oficial 6.1.0: se creó una transacción en el ambiente real de integración y se consultó su estado INITIALIZED. Esto no completó un pago.
- No se ha probado aún el recorrido completo del navegador con banco simulado, ni los bloqueos concurrentes bajo PostgreSQL. Completa la prueba manual anterior en EC2 antes de considerar terminada la instalación.
- El repositorio y EC2 no se modificaron remotamente. Este paquete contiene cambios preparados y comprobados localmente.

## Referencias oficiales

- SDK Python: https://github.com/TransbankDevelopers/transbank-sdk-python
- Flujo Webpay Plus y tarjetas de prueba: https://transbankdevelopers.com/documentacion/webpay-plus
- Ejemplo Python: https://proyecto-ejemplo-python.transbankdevelopers.cl/webpay-plus/
