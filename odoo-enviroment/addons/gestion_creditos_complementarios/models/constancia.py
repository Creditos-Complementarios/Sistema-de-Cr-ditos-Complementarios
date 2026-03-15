# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Constancia(models.Model):
    _name = 'creditos.constancia'
    _description = 'Constancia de Actividad Complementaria'
    _inherit = ['mail.thread']
    _rec_name = 'nombre_constancia'

    expediente_id = fields.Many2one(
        'creditos.expediente.estudiante',
        string='Expediente del Estudiante',
        required=True,
        ondelete='cascade',
    )
    actividad_id = fields.Many2one(
        'creditos.actividad.complementaria',
        string='Actividad Complementaria',
        required=True,
    )
    estudiante_id = fields.Many2one(
        'creditos.estudiante',
        string='Estudiante',
        required=True,
    )
    ruta_constancia = fields.Binary(
        string='Archivo de Constancia (PDF)',
        attachment=True,
    )
    ruta_constancia_filename = fields.Char(string='Nombre del Archivo')
    estado_constancia = fields.Selection(
        selection=[
            ('pendiente', 'Pendiente de Firmas'),
            ('firmada_responsable', 'Firmada por Responsable'),
            ('firmada_jefe', 'Firmada por Jefe de Departamento'),
            ('completa', 'Completa'),
        ],
        string='Estado',
        default='pendiente',
        tracking=True,
    )
    firma_jefe_depto = fields.Binary(
        string='Firma del Jefe de Departamento',
        attachment=True,
    )
    firma_responsable = fields.Binary(
        string='Firma del Responsable de Actividad',
        attachment=True,
    )
    fecha_generacion = fields.Datetime(
        string='Fecha de Generación',
        default=fields.Datetime.now,
        readonly=True,
    )
    nombre_constancia = fields.Char(
        string='Nombre',
        compute='_compute_nombre_constancia',
        store=True,
    )

    @api.depends('estudiante_id', 'actividad_id')
    def _compute_nombre_constancia(self):
        for rec in self:
            rec.nombre_constancia = (
                f'{rec.estudiante_id.nombre_completo or ""} - '
                f'{rec.actividad_id.nombre_actividad or ""}'
            )

    @api.constrains('firma_jefe_depto', 'firma_responsable')
    def _check_constancia_completa(self):
        # FIXED: A @constrains method must raise ValidationError on failure,
        # not perform writes. Writes inside constrains cause recursion and
        # bypass the ORM write pipeline. Use a separate method or override
        # write() for state transitions triggered by field changes.
        pass

    def _actualizar_estado_constancia(self):
        """Call after saving firma fields to transition state correctly."""
        for rec in self:
            if rec.firma_jefe_depto and rec.firma_responsable:
                if rec.estado_constancia != 'completa':
                    rec.estado_constancia = 'completa'
            elif rec.firma_jefe_depto:
                if rec.estado_constancia not in ('firmada_jefe', 'completa'):
                    rec.estado_constancia = 'firmada_jefe'
            elif rec.firma_responsable:
                if rec.estado_constancia not in ('firmada_responsable', 'completa'):
                    rec.estado_constancia = 'firmada_responsable'

    def write(self, vals):
        res = super().write(vals)
        if 'firma_jefe_depto' in vals or 'firma_responsable' in vals:
            self._actualizar_estado_constancia()
        return res


class FirmaElectronica(models.Model):
    _name = 'creditos.firma.electronica'
    _description = 'Firmas Electrónicas de Empleados'

    empleado_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
    )
    firma_electronica = fields.Binary(
        string='Firma Electrónica',
        attachment=True,
        required=True,
    )
    firma_filename = fields.Char(string='Nombre del Archivo')
    activo = fields.Boolean(default=True)

    _sql_constraints = [
        ('empleado_firma_uniq', 'UNIQUE(empleado_id)', 'El empleado ya tiene una firma registrada.')
    ]
