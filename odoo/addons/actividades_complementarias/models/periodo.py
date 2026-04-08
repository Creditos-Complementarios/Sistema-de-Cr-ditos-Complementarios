# -*- coding: utf-8 -*-
from odoo import models, fields


class PeriodoEscolar(models.Model):
    _name = 'actividad.periodo'
    _description = 'Periodo Escolar'
    _order = 'name desc'

    name = fields.Char(string='Periodo', required=True, help='Ej: 2025-2026, 2025-A, 2026-B')
