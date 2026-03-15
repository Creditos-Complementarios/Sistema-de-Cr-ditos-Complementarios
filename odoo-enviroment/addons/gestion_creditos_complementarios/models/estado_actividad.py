# -*- coding: utf-8 -*-
from odoo import models, fields


class EstadoActividad(models.Model):
    _name = 'creditos.estado.actividad'
    _description = 'Estado de Actividad Complementaria'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
