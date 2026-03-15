# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HorarioActividad(models.Model):
    _name = 'creditos.horario.actividad'
    _description = 'Horario de Actividad Complementaria'

    actividad_id = fields.Many2one(
        'creditos.actividad.complementaria',
        string='Actividad',
        required=True,
        ondelete='cascade',
    )
    dia_semana = fields.Selection(
        selection=[
            ('lunes', 'Lunes'),
            ('martes', 'Martes'),
            ('miercoles', 'Miércoles'),
            ('jueves', 'Jueves'),
            ('viernes', 'Viernes'),
            ('sabado', 'Sábado'),
            ('domingo', 'Domingo'),
        ],
        string='Día de la Semana',
        required=True,
    )
    hora_inicio = fields.Float(string='Hora de Inicio', required=True)
    hora_fin = fields.Float(string='Hora de Fin', required=True)

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for rec in self:
            if rec.hora_fin <= rec.hora_inicio:
                raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
