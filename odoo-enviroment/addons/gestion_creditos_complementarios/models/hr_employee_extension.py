# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployeeExtension(models.Model):
    """Extiende hr.employee con campos requeridos por el módulo."""
    _inherit = 'hr.employee'

    creditos_es_jefe_depto = fields.Boolean(
        string='Es Jefe de Departamento',
        default=False,
        help='Marca si este empleado puede actuar como Jefe de Departamento en el módulo.',
    )
    creditos_es_responsable_designado = fields.Boolean(
        string='Es Responsable Designado (por Coordinador)',
        default=False,
        help=(
            'Marcado por el Coordinador de Carrera. '
            'Solo estos empleados aparecen como opciones de Responsable de Actividad.'
        ),
    )
    creditos_es_coordinador_carrera = fields.Boolean(
        string='Es Coordinador de Carrera',
        default=False,
    )
