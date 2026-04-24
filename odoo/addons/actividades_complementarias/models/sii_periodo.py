# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SiiPeriodo(models.Model):
    _name = 'sii.periodo'
    _description = 'SII — Periodo'
    _rec_name = 'clave_periodo'
    _order = 'fecha_inicio desc'

    clave_periodo = fields.Char(
        string='ClavePeriodo',
        required=True,
        size=10
    )
    fecha_inicio = fields.Date(
        string='FechaInicio',
        required=True
    )
    fecha_fin = fields.Date(
        string='FechaFin',
        required=True
    )

    @api.constrains('clave_periodo')
    def _check_clave_periodo_unica(self):
        for rec in self:
            duplicado = self.search_count([
                ('clave_periodo', '=', rec.clave_periodo),
                ('id', '!=', rec.id),
            ])
            if duplicado:
                raise ValidationError(
                    f'El periodo "{rec.clave_periodo}" ya existe. '
                    f'ClavePeriodo debe ser única.'
                )
