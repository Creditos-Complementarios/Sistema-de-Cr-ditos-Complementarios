# -*- coding: utf-8 -*-
from odoo import models, fields


class Carrera(models.Model):
    _name = 'creditos.carrera'
    _description = 'Carrera Académica'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)

    estudiante_ids = fields.One2many(
        'creditos.estudiante',
        'carrera_id',
        string='Estudiantes',
    )
