# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SiiCarrera(models.Model):
    _name = 'sii.carrera'
    _description = 'SII — Carrera'
    _rec_name = 'nombre'

    clave_carrera = fields.Char(
        string='ClaveCarrera',
        required=True,
        size=10
    )
    nombre = fields.Char(
        string='Nombre',
        required=True
    )
    reticula = fields.Char(
        string='Reticula',
        required=True
    )

    @api.constrains('clave_carrera')
    def _check_clave_carrera_unica(self):
        for rec in self:
            duplicado = self.search_count([
                ('clave_carrera', '=', rec.clave_carrera),
                ('id', '!=', rec.id),
            ])
            if duplicado:
                raise ValidationError(
                    f'La clave de carrera "{rec.clave_carrera}" ya existe. '
                    f'ClaveCarrera debe ser única.'
                )
