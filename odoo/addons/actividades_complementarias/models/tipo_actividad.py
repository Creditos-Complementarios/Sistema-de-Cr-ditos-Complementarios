# -*- coding: utf-8 -*-
from odoo import models, fields


class TipoActividad(models.Model):
    _name = 'actividad.tipo'
    _description = 'Tipo de Actividad Complementaria'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        size=200,
    )
    es_predefinida = fields.Boolean(
        string='Actividad Predefinida',
        default=False,
        help='Las actividades no predefinidas crean una propuesta y requieren aprobación del Comité Académico.',
    )
    active = fields.Boolean(default=True)
