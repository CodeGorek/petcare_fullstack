# Comparativa de Precios Amazon S3 y S3 Glacier (`us-east-1` Norte de Virginia)

Referencia oficial para justificar la estrategia de almacenamiento de **PetCare** (`fotos/` en acceso frecuente y `respaldos/` en archivo frío con regla de ciclo de vida).

| Clase de almacenamiento | Precio por GB / mes (`us-east-1`) | Duración mínima | Uso recomendado en PetCare |
| :--- | :--- | :--- | :--- |
| **S3 Standard** | **\$0.023** por GB (primeros 50 TB) | Sin mínimo | Estáticos e imágenes activas (`fotos/` de pacientes y logo servido por CDN). |
| **S3 Glacier Instant Retrieval** | **\$0.004** por GB | 90 días *(mín. facturable 128 KB por objeto)* | Respaldos recientes que podrían consultarse al instante (ahorro ~82% vs Standard). |
| **S3 Glacier Flexible Retrieval** *(antes S3 Glacier)* | **\$0.0036** por GB | 90 días *(+40 KB metadatos/objeto)* | Respaldos diarios tras 30 días mediante regla de ciclo de vida `respaldos-a-glacier`. |
| **S3 Glacier Deep Archive** | **\$0.00099** por GB | 180 días *(+40 KB metadatos/objeto)* | Archivo histórico legal o anual de fichas clínicas de muy largo plazo. |

### Notas clave para la defensa
1. **Regla de ciclo de vida en `respaldos/`:** los respaldos `.json.gz` generados por `lambda/backup_rds_s3.py` entran en `respaldos/` y transicionan automáticamente a **S3 Glacier Flexible Retrieval** después de 30 días, reduciendo el costo mensual por GB de **\$0.023** a **\$0.0036**.
2. **Consideraciones de facturación:** eliminar o sobreescribir objetos antes de cumplir la duración mínima (90 o 180 días) genera cobro prorrateado por los días restantes, además de los cargos por solicitudes PUT/GET y recuperación según velocidad elegida.
