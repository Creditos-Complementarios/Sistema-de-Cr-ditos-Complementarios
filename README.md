# Sistema de Créditos Complementarios — ITCH

> Plataforma de gestión del proceso de créditos complementarios del Instituto Tecnológico de Chetumal, construida sobre Odoo 19 Community.

[![CI](https://github.com/itch-dev/sistema-creditos-complementarios/actions/workflows/ci.yml/badge.svg)](https://github.com/itch-dev/sistema-creditos-complementarios/actions/workflows/ci.yml)
[![Odoo](https://img.shields.io/badge/Odoo-19.0_Community-714B67)](https://github.com/odoo/odoo/tree/19.0)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

## ¿Qué hace este proyecto?

Los estudiantes del ITCH deben acumular créditos complementarios (deportivos, culturales, académicos, etc.) para poder titularse. Este sistema gestiona el ciclo completo: los Jefes de Departamento proponen actividades, el Comité Académico las aprueba o rechaza, los estudiantes se inscriben a través del catálogo, el Responsable de Actividad toma asistencia y asigna niveles de desempeño, se generan constancias con firma dual (JD + Responsable), y finalmente Servicios Escolares valida la liberación de créditos del estudiante.

**Actores del sistema:**

| Actor | Función principal |
|---|---|
| Jefe de Departamento | Crea actividades, gestiona el ciclo de vida, delega permisos, firma constancias |
| Departamento Extraescolares | Crea actividades de tipo extraescolar/selectivo, gestiona personal |
| Comité Académico | Aprueba o rechaza propuestas de nuevos tipos de actividad |
| Responsable de Actividad | Toma asistencia, habilita evidencias, asigna desempeño, firma constancias |
| Estudiante | Consulta catálogo, se inscribe, sube evidencias, solicita liberación |
| División de Estudios / Coordinador | Difunde actividades, consulta expedientes de estudiantes |
| Servicios Escolares | Gestiona periodos de solicitud, aprueba/rechaza liberaciones, genera reportes |

---

## Estructura del repositorio

```
.
├── infrastructure/   Configuración Docker, Compose y entorno de servidor
├── odoo/             Módulos Odoo personalizados (addons propios)
├── docs/             Documentación técnica, diagramas y decisiones de arquitectura
└── .github/          Pipelines de CI/CD (GitHub Actions)
```

Cada subdirectorio tiene su propio `README.md` con instrucciones específicas para el área.

---

## Inicio rápido

### Requisitos

| Herramienta | Versión mínima |
|---|---|
| Docker Desktop | 24.x |
| Docker Compose | 2.x |
| Git | 2.40+ |

### Levantar el entorno

```bash
# 1. Clonar el repositorio
git clone https://github.com/itch-dev/sistema-creditos-complementarios.git
cd sistema-creditos-complementarios

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores locales

# 3. Entrar a infrastructure/ — TODOS los comandos docker se ejecutan desde aquí
cd infrastructure

# 4. Configurar Odoo
cp config/odoo.conf.example config/odoo.conf

# 5. Levantar los servicios
docker compose up -d
```

Odoo estará disponible en **http://localhost:8069**.

Para instrucciones detalladas de infraestructura, ver [`infrastructure/README.md`](infrastructure/README.md).
Para instalar y desarrollar módulos, ver [`odoo/README.md`](odoo/README.md).

---

## Estado del desarrollo

| Fase | Casos de uso | Estado |
|---|---|---|
| Fase 1 — Esqueleto y seguridad | Grupos, modelos base, catálogos, crons | ✅ Completo |
| Fase 2 — Creación y aprobación | JD-01SC, JD-02SC, JD-03SC, CA-01SC, CA-02SC, DE-01SC, DE-02SC, DE-03SC | ✅ JD + CA completos · DE en progreso |
| Fase 3 — Inscripción y ejecución | E-01SC, E-02SC, RA-01SC, RA-02SC, RAE-01SC | 🔄 En desarrollo |
| Fase 4 — Certificación y liberación | E-03SC, SE-01SC, SE-02SC, SE-03SC, SE-04SC, DEP-C-01SC, DEP-C-02SC | ⏳ Pendiente |

---

## Equipo

| Rol | Responsabilidad principal |
|---|---|
| Líder técnico | Arquitectura, revisión de PRs, merge a `develop` y `main` |
| Back-end (×2) | Modelos, lógica de negocio, crons, wizards |
| Front-end (×2) | Vistas XML, QWeb, assets JS/CSS |
| Base de datos (×2) | Migraciones, índices, rendimiento, scripts de datos |

---

## Flujo de trabajo Git

Este proyecto sigue un Git Flow adaptado:

| Rama | Propósito |
|---|---|
| `main` | Código en producción. Solo recibe merges desde `develop` o `hotfix/*`. |
| `develop` | Integración continua. Refleja el servidor de staging. |
| `feature/<rol>-<descripcion>` | Trabajo individual. Nace y muere en cada tarea. |
| `fix/<rol>-<descripcion>` | Corrección de bugs. |
| `hotfix/*` | Correcciones urgentes sobre producción. |
| `docs/*` | Cambios exclusivos de documentación. |

**Infijos de rol en nombres de rama:** `back-`, `front-`, `db-`

```
feature/back-estudiante-inscripcion
feature/front-catalogo-actividades
fix/back-cron-auto-aprobacion
docs/adr-expediente-model
```

Ningún desarrollador hace push directo a `main` o `develop`. Todo cambio entra por Pull Request con CI en verde y aprobación del líder.

Para la guía completa de Git, convenciones y proceso de PR, ver [`docs/README.md`](docs/README.md).

---

## Convenciones de commits

Se usa [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(jd): añadir wizard de generación de actividad complementaria
fix(comite): corregir cálculo de fecha límite de revisión en propuesta
fix(security): acotar acceso de base.group_user a modelos del módulo
chore(ci): añadir job de linting a pipeline
docs(adr): registrar decisión sobre módulo único vs. por actor
test(actividad): cubrir flujo dual de firma de constancias
```

---

## Variables de entorno

Copiar `.env.example` a `.env` y completar los valores. El archivo `.env` está en `.gitignore` y **nunca debe subirse al repositorio**.

| Variable | Descripción | Ejemplo |
|---|---|---|
| `ODOO_MASTER_PASSWORD` | Contraseña maestra de Odoo | `changeme_local` |
| `POSTGRES_DB` | Nombre de la base de datos | `odoo_dev` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `odoo` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `odoo` |
| `ODOO_PORT` | Puerto expuesto de Odoo | `8069` |

---

## Licencia

Este proyecto está bajo la licencia [LGPL-3.0](LICENSE). Desarrollado como proyecto académico para el Instituto Tecnológico de Chetumal.

---

_Última actualización: 2026-03-23 · Odoo 19.0 Community_
