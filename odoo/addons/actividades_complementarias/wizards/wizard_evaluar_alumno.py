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
                # [#201] Eliminado el fallback 'or \"0\"'.
                # Precargar Insuficiente cuando la inscripción no tiene nivel
                # asignado provocaba que cerrar el wizard sin elegir nada
                # guardara '0' de forma involuntaria, bloqueando la inscripción
                # permanentemente y contaminando el promedio del estudiante.
                # El campo queda vacío y el RA debe elegir explícitamente.
                'performance_level': insc.performance_level or False,
                'observations': insc.observations or '',
            })
        return res

    def action_confirmar(self):
        self.ensure_one()
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
