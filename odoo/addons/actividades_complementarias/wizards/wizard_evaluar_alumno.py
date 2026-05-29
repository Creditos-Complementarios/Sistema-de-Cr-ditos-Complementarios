# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError

PERFORMANCE_LEVELS = [
    ("0", "Insuficiente"),
    ("1", "Suficiente"),
    ("2", "Bueno"),
    ("3", "Notable"),
    ("4", "Excelente"),
]


class WizardEvaluarAlumno(models.TransientModel):
    _name = 'actividad.wizard.evaluar.alumno'
    _description = 'Asignar Nivel de Desempeño al Estudiante'

    inscripcion_id = fields.Many2one(
        'actividad.inscripcion',
        string='Inscripción',
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        related='inscripcion_id.partner_id',
        string='Estudiante',
        readonly=True,
    )
    actividad_id = fields.Many2one(
        related='inscripcion_id.actividad_id',
        string='Actividad',
        readonly=True,
    )
    performance_level = fields.Selection(
        selection=PERFORMANCE_LEVELS,
        string='Nivel de Desempeño',
        required=True,
    )
    observations = fields.Text(string='Observaciones')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        inscripcion_id = self.env.context.get('default_inscripcion_id')
        if inscripcion_id:
            insc = self.env['actividad.inscripcion'].browse(inscripcion_id)
            res.update({
                'inscripcion_id': insc.id,
                'performance_level': insc.performance_level or '0',
                'observations': insc.observations or '',
            })
        return res

    def action_confirmar(self):
        self.ensure_one()
        # Verificar que el usuario en sesión es el Responsable de la Actividad
        inscripcion = self.inscripcion_id
        if inscripcion.actividad_id.responsable_actividad_id.id != self.env.user.id:
            raise ValidationError(
                _(
                    "No tiene permiso para evaluar alumnos en esta actividad. "
                    "Solo el Responsable de la Actividad puede asignar el "
                    "nivel de desempeño."
                )
            )
        if self.inscripcion_id.performance_level:
            raise ValidationError(
                _(
                    "El nivel de desempeño de \"%s\" ya fue asignado (%s) "
                    "y no puede modificarse."
                )
                % (
                    self.inscripcion_id.partner_id.name,
                    self.inscripcion_id.performance_label,
                )
            )
        self.inscripcion_id.write({
            'performance_level': self.performance_level,
            'observations': self.observations,
        })
        return {'type': 'ir.actions.act_window_close'}
