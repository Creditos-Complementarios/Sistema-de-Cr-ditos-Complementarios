# -*- coding: utf-8 -*-
from odoo import models, fields


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

    _constraints = [
        models.Constraint(
            'UNIQUE(clave_carrera)',
            'sii_carrera_clave_carrera_unique',
            'ClaveCarrera debe ser única.'
        )
    ]
