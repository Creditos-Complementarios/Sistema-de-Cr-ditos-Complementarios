# Odoo 19 — Docker Desktop Setup
## Sistema de Créditos Complementarios

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado y corriendo
- Git (opcional, para clonar el repositorio)

---

## Estructura de archivos

```
docker_odoo19/
├── docker-compose.yml       ← Orquestación de contenedores
├── config/
│   └── odoo.conf            ← Configuración de Odoo
├── addons/
│   └── gestion_creditos_complementarios/  ← TU MÓDULO VA AQUÍ
└── README.md
```

---

## Paso 1 — Copiar tu módulo

Copia la carpeta del módulo dentro de `addons/`:

```bash
cp -r gestion_creditos_complementarios_fixed/  docker_odoo19/addons/gestion_creditos_complementarios/
```

La estructura final debe quedar:
```
addons/
└── gestion_creditos_complementarios/
    ├── __manifest__.py
    ├── __init__.py
    ├── models/
    ├── views/
    ├── security/
    └── ...
```

---

## Paso 2 — Levantar los contenedores

Desde la carpeta `docker_odoo19/`:

```bash
docker compose up -d
```

Espera ~30 segundos a que Odoo inicie. Puedes ver los logs con:

```bash
docker compose logs -f odoo
```

---

## Paso 3 — Crear la base de datos

1. Abre el navegador en: **http://localhost:8069**
2. Verás el wizard de creación de base de datos.
3. Completa:
   - **Master Password**: `admin`  (o la que quieras)
   - **Database Name**: `odoo19_dev`
   - **Email**: `admin@example.com`
   - **Password**: `admin`
   - **Language**: Español (México)
   - **Demo Data**: True
4. Haz clic en **Create Database**.

**Demo user password:** Admin1234!

---

## Paso 4 — Instalar el módulo

### Opción A — Desde la interfaz

1. Ve a **Ajustes → Aplicaciones** (activa modo desarrollador primero: Ajustes → Modo desarrollador)
2. Busca **"Créditos Complementarios"**
3. Haz clic en **Instalar**

### Opción B — Desde la terminal (más rápido)

```bash
docker compose exec odoo odoo -d odoo19_dev -i gestion_creditos_complementarios --stop-after-init
```

---

## Comandos útiles

### Actualizar el módulo después de cambios en el código

```bash
# Opción A: desde la UI en modo dev — refresca la página con Ctrl+Shift+F5
# Opción B: desde terminal
docker compose exec odoo odoo -d odoo19_dev -u gestion_creditos_complementarios --stop-after-init
```

> Nota: con `dev_mode = all` en odoo.conf, los cambios en vistas XML se
> recargan automáticamente. Los cambios en modelos Python siempre requieren
> `-u` o reiniciar el contenedor.

### Reiniciar solo Odoo (sin tocar la base de datos)

```bash
docker compose restart odoo
```

### Ver logs en tiempo real

```bash
docker compose logs -f odoo
```

### Acceder a la shell de Python de Odoo (para debug)

```bash
docker compose exec odoo odoo shell -d odoo19_dev
```

### Detener todo

```bash
docker compose down
```

### Detener todo Y borrar la base de datos (reset completo)

```bash
docker compose down -v
```

---

## Activar modo desarrollador

1. Ve a **Ajustes**
2. Haz scroll hasta la sección "Herramientas para desarrolladores"
3. Haz clic en **Activar modo desarrollador**

O directamente en la URL: agrega `?debug=1` después del dominio:
`http://localhost:8069/web?debug=1`

---

## Credenciales por defecto

| Campo     | Valor               |
|-----------|---------------------|
| URL       | http://localhost:8069 |
| Email     | admin@example.com   |
| Password  | admin               |
| DB        | odoo19_dev          |

---

## Solución de problemas frecuentes

**El módulo no aparece en la lista de aplicaciones:**
- Verifica que la carpeta esté correctamente ubicada en `addons/`
- Ve a Aplicaciones → Actualizar lista de aplicaciones

**Error "Module not found" al instalar:**
- Revisa que `__manifest__.py` exista y no tenga errores de sintaxis
- Ejecuta: `docker compose exec odoo python3 -c "import ast; ast.parse(open('/mnt/extra-addons/gestion_creditos_complementarios/__manifest__.py').read())"`

**Puerto 8069 en uso:**
- Cambia el mapeo en `docker-compose.yml`: `"8070:8069"`

**Error de permisos en volúmenes (Linux/Mac):**
```bash
sudo chown -R $USER:$USER addons/
```
