# Créditos Complementarios — Módulo Odoo 19.0

## Descripción

Módulo para la gestión integral del sistema de **Créditos Complementarios** institucional.
Permite registrar, aprobar, gestionar y acreditar actividades complementarias para estudiantes.

---

## Casos de uso implementados

### JD-01SC · Solicitud de nuevo tipo de actividad complementaria

- El **Jefe de Departamento** llena el formulario completo de una nueva actividad.
- Si el tipo es **predefinido**, la actividad se envía directamente al catálogo.
- Si el tipo es **nuevo**, se genera una propuesta que se envía al **Comité Académico**.
- El Comité puede **aprobar** o **rechazar** la propuesta con motivo.
- Si el Comité no responde en **5 días hábiles**, la propuesta se aprueba automáticamente (cron diario).
- Los créditos solo pueden ser **1** o **0.5**.
- El cupo puede ser numérico (mínimo/máximo) o marcarse como **ilimitado**.

### JD-02SC · Gestión de actividades complementarias

- Visualización de actividades por estado: **aprobada → pendiente de inicio → en curso → finalizada**.
- Asignación de **Responsable de Actividad** (solo entre los designados por el Coordinador de Carrera).
- Asignación de **estudiantes** a la actividad o envío al catálogo.
- **Difusión** selectiva de la actividad a estudiantes filtrados por carrera, semestre y grupo.
- Registro de **nivel de desempeño** por el Responsable.
- Generación automática de **constancias** al finalizar la actividad.
- **Firma digital** masiva de constancias por el Jefe de Departamento.

---

## Grupos de seguridad

| Grupo | Permisos principales |
|---|---|
| **Jefe de Departamento** | Crear propuestas, gestionar actividades, firmar constancias |
| **Comité Académico** | Aprobar/rechazar propuestas |
| **Coordinador de Carrera** | Designar responsables de actividad |
| **Responsable de Actividad** | Gestionar actividad asignada, registrar desempeño |
| **Administrador** | Acceso total |

---

## Modelos principales

| Modelo | Descripción |
|---|---|
| `creditos.propuesta.actividad` | Formulario JD-01SC — solicitud al Comité |
| `creditos.actividad.complementaria` | Gestión JD-02SC — ciclo de vida completo |
| `creditos.tipo.actividad` | Catálogo de tipos (predefinidos y nuevos) |
| `creditos.periodo` | Periodos escolares |
| `creditos.estudiante` | Registro de estudiantes |
| `creditos.expediente.estudiante` | Créditos acumulados y constancias |
| `creditos.constancia` | Constancias digitales con firma electrónica |
| `creditos.lista.estudiante.actividad` | Inscritos por actividad con nivel de desempeño |

---

## Instalación

1. Copiar la carpeta `creditos_complementarios` a `addons/` del servidor Odoo.
2. Actualizar la lista de módulos en **Ajustes → Activar modo desarrollador → Actualizar lista de aplicaciones**.
3. Buscar **Créditos Complementarios** e instalar.
4. Asignar los grupos de seguridad a los usuarios correspondientes.

---

## Dependencias

- `base`
- `mail`
- `portal`
- `hr`

---

## Versión

`19.0.1.0.0` — Compatible con Odoo Community 19.0
