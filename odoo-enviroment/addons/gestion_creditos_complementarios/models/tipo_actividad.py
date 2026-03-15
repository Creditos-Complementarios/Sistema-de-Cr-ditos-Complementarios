# -*- coding: utf-8 -*-
from odoo import models, fields


class TipoActividad(models.Model):
    _name = 'creditos.tipo.actividad'
    _description = 'Tipo de Actividad Complementaria'
    _rec_name = 'nombre'

    nombre = fields.Char(
        string='Nombre',
        required=True,
    )
    es_predefinida = fields.Boolean(
        string='Es Predefinida',
        default=False,
        help='Si es predefinida, no requiere aprobación del Comité Académico.',
    )
    active = fields.Boolean(default=True)
