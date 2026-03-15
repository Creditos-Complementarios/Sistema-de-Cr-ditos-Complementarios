# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Estudiante(models.Model):
    _name = 'creditos.estudiante'
    _description = 'Estudiante'
    _rec_name = 'nombre_completo'

    no_control = fields.Char(
        string='Número de Control',
        required=True,
        copy=False,
    )
    carrera_id = fields.Many2one(
        'creditos.carrera',
        string='Carrera',
        required=True,
    )
    nombre = fields.Char(string='Nombre', required=True)
    apellido1 = fields.Char(string='Primer Apellido', required=True)
    apellido2 = fields.Char(string='Segundo Apellido')
    semestre = fields.Integer(string='Semestre', required=True)
    grupo = fields.Char(string='Grupo')
    estado_liberacion = fields.Boolean(
        string='Liberación Cumplida',
        default=False,
    )
    estado_estudiante = fields.Selection(
        selection=[
            ('activo', 'Activo'),
            ('inactivo', 'Inactivo'),
            ('egresado', 'Egresado'),
        ],
        string='Estado',
        default='activo',
        required=True,
    )
    correo = fields.Char(string='Correo Electrónico')
    telefono = fields.Char(string='Teléfono')
    nombre_completo = fields.Char(
        string='Nombre Completo',
        compute='_compute_nombre_completo',
        store=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Usuario del Sistema',
    )

    expediente_id = fields.One2many(
        'creditos.expediente.estudiante',
        'estudiante_id',
        string='Expediente',
    )

    # FIXED: Missing @api.depends decorator — without it the compute method
    # is never triggered automatically when nombre/apellido fields change.
    @api.depends('nombre', 'apellido1', 'apellido2')
    def _compute_nombre_completo(self):
        for rec in self:
            partes = [rec.nombre, rec.apellido1]
            if rec.apellido2:
                partes.append(rec.apellido2)
            rec.nombre_completo = ' '.join(filter(None, partes))

    _sql_constraints = [
        ('no_control_uniq', 'UNIQUE(no_control)', 'El número de control debe ser único.'),
    ]
