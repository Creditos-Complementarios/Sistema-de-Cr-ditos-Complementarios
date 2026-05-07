# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardNuevaSesion(models.TransientModel):
    """Wizard: genera una sesión de pase de lista para una fecha dada,
    pre-llenando automáticamente todos los estudiantes inscritos."""

    _name = 'actividad.wizard.nueva.sesion'
    _description = 'Wizard: Nueva Sesión de Pase de Lista'

    actividad_id = fields.Many2one(
        'actividad.complementaria',
        required=True,
        ondelete='cascade',
    )
    fecha = fields.Date(
        string='Fecha de la Sesión',
        required=True,
        default=fields.Date.today,
    )

    @api.constrains('fecha', 'actividad_id')
    def _check_fecha_rango(self):
        for rec in self:
            a = rec.actividad_id
            if a.fecha_inicio and rec.fecha < a.fecha_inicio:
                raise ValidationError(
                    _('La fecha de la sesión no puede ser anterior a la fecha de inicio '
                      'de la actividad (%s).') % a.fecha_inicio
                )
            if a.fecha_fin and rec.fecha > a.fecha_fin:
                raise ValidationError(
                    _('La fecha de la sesión no puede ser posterior a la fecha de fin '
                      'de la actividad (%s).') % a.fecha_fin
                )

    def action_generar(self):
        """Crea registros de asistencia para todos los inscritos en la fecha dada.
        Ignora duplicados (mismo alumno, misma fecha)."""
        self.ensure_one()
        Asistencia = self.env['actividad.asistencia']
        creados = 0
        for inscripcion in self.actividad_id.inscripcion_ids:
            existe = Asistencia.search_count([
                ('actividad_id', '=', self.actividad_id.id),
                ('inscripcion_id', '=', inscripcion.id),
                ('fecha', '=', self.fecha),
            ])
            if not existe:
                Asistencia.create({
                    'actividad_id': self.actividad_id.id,
                    'inscripcion_id': inscripcion.id,
                    'fecha': self.fecha,
                    'presente': False,
                })
                creados += 1

        # Abrir la vista de pase de lista filtrada por esta actividad
        return self.actividad_id.action_abrir_pase_lista()
