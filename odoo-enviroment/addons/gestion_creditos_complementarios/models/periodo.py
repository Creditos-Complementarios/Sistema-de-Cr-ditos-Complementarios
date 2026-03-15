# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Periodo(models.Model):
    _name = 'creditos.periodo'
    _description = 'Periodo Escolar'
    _rec_name = 'clave_periodo'
    _order = 'fecha_inicio desc'

    clave_periodo = fields.Char(
        string='Clave de Periodo',
        required=True,
    )
    descripcion = fields.Char(string='Descripción')
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de Fin', required=True)
    active = fields.Boolean(default=True)

    fecha_por_periodo_ids = fields.One2many(
        'creditos.fecha.por.periodo',
        'periodo_id',
        string='Fechas por Periodo',
    )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_fin <= rec.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
