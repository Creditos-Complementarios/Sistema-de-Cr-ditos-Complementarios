# Sistema de Créditos Complementarios

> Una línea que describa el propósito del sistema. Ejemplo: _Sistema de gestión comercial y contable sobre Odoo 19 Community para [Nombre del Cliente]._

[![CI](https://github.com/<org>/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<org>/<repo>/actions/workflows/ci.yml)
[![Odoo](https://img.shields.io/badge/Odoo-19.0_Community-714B67)](https://github.com/odoo/odoo/tree/19.0)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

---

## ¿Qué hace este proyecto?

_Describir en 3–5 oraciones el problema de negocio que resuelve y los módulos o procesos principales que cubre. No es necesario ser técnico aquí — este párrafo es para cualquier persona que llegue al repositorio por primera vez._

**Áreas funcionales cubiertas:**

- Ventas y CRM
- Facturación y contabilidad
- Inventario y logística
- _(ajustar según el proyecto)_

---

## Estructura del repositorio

```
.
├── infra/          Configuración Docker, Compose y entorno de servidor
├── odoo/           Módulos Odoo personalizados (addons propios)
├── docs/           Documentación técnica, diagramas y decisiones de arquitectura
└── .github/        Pipelines de CI/CD (GitHub Actions)
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

### Levantar el entorno en 3 pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/<org>/<repo>.git && cd <repo>

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores locales

# 3. Levantar los servicios
docker compose -f infra/docker-compose.yml up -d
```

Odoo estará disponible en **http://localhost:8069**.

Para instrucciones detalladas de infraestructura, ver [`infra/README.md`](infra/README.md).  
Para instalar y desarrollar módulos, ver [`odoo/README.md`](odoo/README.md).

---

## Equipo

| Rol | Responsabilidad principal |
|---|---|
| Líder técnico | Arquitectura, revisión de PRs, merge a `develop` y `main` |
| Back-end (×2) | Modelos, lógica de negocio, reportes, controladores |
| Front-end (×2) | Vistas XML, QWeb, assets JS/CSS, portal web |
| Base de datos (×2) | Migraciones, índices, rendimiento de consultas, scripts de datos |

---

## Flujo de trabajo Git

Este proyecto sigue un Git Flow adaptado con cuatro tipos de ramas:

| Rama | Propósito |
|---|---|
| `main` | Código en producción. Solo recibe merges desde `develop` o `hotfix/*`. |
| `develop` | Integración continua. Refleja el servidor de staging. |
| `feature/*` / `fix/*` / `refactor/*`/ `docs/*`/ `test/*`| Trabajo individual. Nace y muere en cada tarea. |
| `hotfix/*` | Correcciones urgentes sobre producción. |

Ningún desarrollador hace push directo a `main` o `develop`. Todo cambio entra por Pull Request con CI en verde y aprobación del líder.

Para la guía completa de Git, convenciones de nombres y proceso de PR, ver [`docs/README.md`](docs/README.md).

---

## Convenciones de commits

Se usa el estándar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(ventas): añadir campo de margen en líneas de pedido
fix(facturación): corregir cálculo de impuesto en nota de crédito
chore(ci): añadir job de linting a pipeline
docs(adr): registrar decisión sobre estructura de módulos
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

Este proyecto está bajo la licencia [LGPL-3.0](LICENSE). Los módulos personalizados desarrollados para este proyecto son propiedad de [Nombre del Cliente / Empresa].

---

_Última actualización: 2026-03-19 · Odoo 19.0 Community_
