# -*- coding: utf-8 -*-
from odoo import models, fields


class EvidenciaActividad(models.Model):
    _name = 'creditos.evidencia.actividad'
    _description = 'Evidencias por Actividad Complementaria'

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
    ruta_archivo = fields.Binary(
        string='Archivo de Evidencia',
        attachment=True,
        required=True,
    )
    ruta_archivo_filename = fields.Char(string='Nombre del Archivo')
    fecha_carga = fields.Datetime(
        string='Fecha de Carga',
        default=fields.Datetime.now,
        readonly=True,
    )
