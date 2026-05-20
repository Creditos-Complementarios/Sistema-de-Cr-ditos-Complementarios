# -*- coding: utf-8 -*-
from . import models  # noqa: F401
from . import wizards  # noqa: F401
from . import controllers  # noqa: F401


def post_init_hook(env):
    actividades = env['actividad.complementaria'].search([('alumno_ids', '!=', False)])
    for a in actividades:
        a._sincronizar_inscripciones()
