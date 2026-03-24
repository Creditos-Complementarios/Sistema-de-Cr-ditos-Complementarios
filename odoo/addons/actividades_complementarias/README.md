# actividades_complementarias

Módulo Odoo 19 Community para la gestión integral del ciclo de créditos complementarios del Instituto Tecnológico de Chetumal.

---

## Casos de uso implementados

| ID | Módulo | Actor | Prioridad | Estado |
|---|---|---|---|---|
| JD-01SC | Solicitud de nuevo tipo de actividad complementaria | Jefe de Departamento | Alta | ✅ |
| JD-02SC | Gestión de actividades complementarias | Jefe de Departamento | Alta | ✅ |
| JD-03SC | Gestión de personal para asignación de permisos | Jefe de Departamento | Alta | ✅ |
| CA-01SC | Gestión de propuestas de actividad complementaria | Comité Académico | Alta | ✅ |
| CA-02SC | Consulta de historial de propuestas | Comité Académico | Media | ✅ |

---

## Modelos

| Modelo | Descripción |
|---|---|
| `actividad.complementaria` | Entidad central — recorre todos los estados del ciclo de vida |
| `actividad.propuesta` | Propuesta al Comité Académico para nuevos tipos de actividad |
| `actividad.tipo` | Catálogo de tipos (predefinidos / nuevos) |
| `actividad.estado` | Estados del ciclo de vida de la actividad |
| `actividad.estado.solicitud` | Estados de propuesta (en revisión / aprobada / rechazada) |
| `actividad.periodo` | Catálogo de periodos escolares |
| `actividad.empleado.permiso` | Permisos delegados por el JD / Depto. Extraescolares a su personal |
| `actividad.departamento` | Catálogo de departamentos con su Jefe asignado |

---

## Ciclo de vida de `actividad.complementaria`

```
[borrador] → en_revision → aprobada ──→ pendiente_inicio → en_curso → finalizada
                        ↘ rechazada         ↑
                                       (predefinida: salto directo)
```

Las transiciones `pendiente_inicio → en_curso` y `en_curso → finalizada` ocurren automáticamente vía cron al llegar la fecha correspondiente.

Las propuestas al Comité se aprueban automáticamente si no hay respuesta en 5 días hábiles (cron diario).

---

## Firma dual de constancias

Las constancias requieren la firma de **dos personas** antes de liberarse a los expedientes de estudiantes:

- `jd_firmo` — establece el JD mediante `action_firmar_constancias()`
- `responsable_firmo` — establece el Responsable de Actividad (implementado en RA-02SC)
- `constancias_firmadas` — campo computado `store=True`; es `True` solo cuando ambas firmas están presentes

No modificar esta lógica sin considerar el impacto en el flujo de liberación de Servicios Escolares.

---

## Grupos de seguridad

| XML ID | Nombre | Puede crear actividades | Puede aprobar | Firma constancias |
|---|---|---|---|---|
| `group_admin_actividades` | Administrador | ✅ | ✅ | ✅ |
| `group_jefe_departamento` | Jefe de Departamento | ✅ | — | ✅ (JD) |
| `group_comite_academico` | Comité Académico | — | ✅ | — |
| `group_personal_departamento_*` | Personal de Depto. | Delegado | — | — |
| `group_personal_departamento_extraescolar` | Personal Extraescolar | Delegado | — | — |
| `group_responsable_actividad` | Responsable de Actividad | ✅ | — | ✅ (RA) |
| `group_alumno` | Alumno | — | — | — |
| `group_servicios_escolares` | Servicios Escolares | — | Liberación | — |
| `group_division_estudios` | División / Coordinador | — | — | — |

Los grupos marcados como "stub" (`group_personal_departamento_extraescolar`, `group_servicios_escolares`, `group_division_estudios`) ya están declarados en `actividades_security.xml` para que las ramas que los implementen no generen conflictos al agregar sus rows en `ir.model.access.csv`.

---

## Automatizaciones (Cron)

| ID | Frecuencia | Regla de negocio |
|---|---|---|
| `cron_actualizar_estados_actividad` | Diario | `pendiente_inicio → en_curso` al llegar fecha_inicio; `en_curso → finalizada` al llegar fecha_fin |
| `cron_auto_aprobar_propuestas` | Diario | Aprueba propuestas sin respuesta del Comité tras 5 días |
| `cron_remover_permisos_inactivos` | Diario | Revoca todos los permisos delegados a personal sin uso en 30 días |

---

## Añadir un nuevo departamento

El mapeo de departamentos a grupos de seguridad vive en una sola constante al inicio de `models/empleado_permiso.py`:

```python
DEPT_MAP = [
    ('sistem',   'sistemas',    'actividades_complementarias.group_personal_departamento_sistemas'),
    ('electr',   'electrica',   'actividades_complementarias.group_personal_departamento_electrica'),
    ('biol',     'biologia',    'actividades_complementarias.group_personal_departamento_biologia'),
    ('extraesc', 'extraescolar','actividades_complementarias.group_personal_departamento_extraescolar'),
]
```

Para añadir un nuevo departamento: (1) declarar el grupo en `actividades_security.xml`, (2) añadir sus rows en `ir.model.access.csv`, (3) añadir una tupla en `DEPT_MAP`. No hay más lugares que editar.

---

## Dependencias

- `base`
- `mail` (chatter y seguimiento de cambios)
- `hr` (referencia a empleados para validar Responsable de Actividad)

---

## Instalación

```bash
# Instalar
docker compose exec odoo odoo-bin -d odoo_dev \
  -i actividades_complementarias --stop-after-init

# Actualizar tras cambios
docker compose exec odoo odoo-bin -d odoo_dev \
  -u actividades_complementarias --stop-after-init

# Ejecutar tests
docker compose exec odoo odoo-bin -d odoo_dev \
  --test-tags actividades_complementarias --stop-after-init --log-level=test
```

_Ejecutar todos los comandos desde dentro de `infrastructure/`._

---

_Última actualización: 2026-03-23 · Odoo 19.0 Community_
