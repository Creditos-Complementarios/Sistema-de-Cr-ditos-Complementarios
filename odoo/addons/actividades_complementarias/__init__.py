# -*- coding: utf-8 -*-
from . import models
from . import wizards


def post_init_hook(env):
    actividades = env['actividad.complementaria'].search([('alumno_ids', '!=', False)])
    for a in actividades:
        a._sincronizar_inscripciones()
        
