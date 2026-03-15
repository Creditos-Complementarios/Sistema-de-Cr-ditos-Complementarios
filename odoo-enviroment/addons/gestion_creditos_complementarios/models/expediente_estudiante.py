# -*- coding: utf-8 -*-
from odoo import models, fields


class ExpedienteEstudiante(models.Model):
    _name = 'creditos.expediente.estudiante'
    _description = 'Expediente del Estudiante'
    _rec_name = 'estudiante_id'

    estudiante_id = fields.Many2one(
        'creditos.estudiante',
        string='Estudiante',
        required=True,
        ondelete='cascade',
    )
    creditos_acumulados = fields.Float(
        string='Créditos Acumulados',
        default=0.0,
        readonly=True,
    )
    nivel_desempeno_promedio = fields.Float(
        string='Nivel de Desempeño Promedio',
        default=0.0,
        readonly=True,
    )
    constancia_ids = fields.One2many(
        'creditos.constancia',
        'expediente_id',
        string='Constancias',
    )
