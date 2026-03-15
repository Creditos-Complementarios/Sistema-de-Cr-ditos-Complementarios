# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FechaPorPeriodo(models.Model):
    _name = 'creditos.fecha.por.periodo'
    _description = 'Fechas de Inscripción por Periodo'

    periodo_id = fields.Many2one(
        'creditos.periodo',
        string='Periodo',
        required=True,
        ondelete='cascade',
    )
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de Fin', required=True)

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_fin <= rec.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
