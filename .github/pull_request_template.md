## Descripción

_¿Qué cambia y por qué? Referencia el caso de uso (ej: implementa E-01SC — inscripción de estudiante)._

## Tipo de cambio

- [ ] `feat` — Nueva funcionalidad
- [ ] `fix` — Corrección de bug
- [ ] `refactor` — Sin cambio funcional
- [ ] `docs` — Solo documentación
- [ ] `test` — Solo tests
- [ ] `chore` — CI, dependencias, configuración

## Checklist

- [ ] `__manifest__.py` tiene versión correcta y dependencias mínimas
- [ ] Modelos nuevos tienen entradas en `security/ir.model.access.csv`
- [ ] Grupos nuevos están declarados en `security/actividades_security.xml`
- [ ] Si se añade un departamento, se actualizó `DEPT_MAP` en `empleado_permiso.py`
- [ ] Tests pasan localmente (`--test-tags actividades_complementarias`)
- [ ] Linting sin errores (`flake8 --max-line-length=120`)
- [ ] No hay `print()`, TODOs ni código comentado en el diff
- [ ] Si hay cambios de esquema, existe el script de migración en `migrations/`
- [ ] Si se añade dependencia Python, está en `requirements.txt`
