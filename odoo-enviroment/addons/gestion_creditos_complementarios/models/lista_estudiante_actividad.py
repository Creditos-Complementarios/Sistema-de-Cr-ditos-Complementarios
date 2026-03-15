# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ListaEstudianteActividad(models.Model):
    _name = 'creditos.lista.estudiante.actividad'
    _description = 'Lista de Estudiantes por Actividad Complementaria'

    actividad_id = fields.Many2one(
        'creditos.actividad.complementaria',
        string='Actividad',
        required=True,
        ondelete='cascade',
    )
    estudiante_id = fields.Many2one(
        'creditos.estudiante',
        string='Estudiante',
        required=True,
    )
    nivel_desempeno = fields.Selection(
        selection=[
            ('excelente', 'Excelente'),
            ('bueno', 'Bueno'),
            ('regular', 'Regular'),
            ('deficiente', 'Deficiente'),
        ],
        string='Nivel de Desempeño',
        tracking=True,
    )
    constancia_id = fields.Many2one(
        'creditos.constancia',
        string='Constancia Generada',
        readonly=True,
    )
    periodo_id = fields.Many2one(
        related='actividad_id.periodo_id',
        string='Periodo',
        store=True,
    )

    _sql_constraints = [
        (
            'estudiante_actividad_uniq',
            'UNIQUE(actividad_id, estudiante_id)',
            'El estudiante ya está registrado en esta actividad.',
        )
    ]
