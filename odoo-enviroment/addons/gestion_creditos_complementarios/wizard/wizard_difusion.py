# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from markupsafe import Markup, escape


class WizardDifusion(models.TransientModel):
    _name = 'creditos.wizard.difusion'
    _description = 'Asistente para Difusión de Actividad Complementaria'

    actividad_id = fields.Many2one(
        'creditos.actividad.complementaria',
        string='Actividad',
        required=True,
        readonly=True,
    )
    carrera_id = fields.Many2one(
        'creditos.carrera',
        string='Filtrar por Carrera',
    )
    semestre = fields.Integer(string='Filtrar por Semestre')
    grupo = fields.Char(string='Filtrar por Grupo')
    estudiante_ids = fields.Many2many(
        'creditos.estudiante',
        'wizard_difusion_estudiante_rel',
        'wizard_id',
        'estudiante_id',
        string='Estudiantes Seleccionados',
    )

    @api.onchange('carrera_id', 'semestre', 'grupo')
    def _onchange_filtros(self):
        dominio = [('estado_estudiante', '=', 'activo')]
        if self.carrera_id:
            dominio.append(('carrera_id', '=', self.carrera_id.id))
        if self.semestre:
            dominio.append(('semestre', '=', self.semestre))
        if self.grupo:
            dominio.append(('grupo', 'ilike', self.grupo))
        return {'domain': {'estudiante_ids': dominio}}

    def action_difundir(self):
        self.ensure_one()
        if not self.estudiante_ids:
            raise ValidationError('Debe seleccionar al menos un estudiante para difundir.')
        actividad = self.actividad_id
        for estudiante in self.estudiante_ids:
            if estudiante.user_id:
                actividad.message_notify(
                    partner_ids=[estudiante.user_id.partner_id.id],
                    subject=f'Invitación: {actividad.nombre_actividad}',
                    body=Markup(
                        '<p>Has sido invitado a participar en la actividad complementaria '
                        '<b>%s</b>.<br/>'
                        'Periodo: %s<br/>'
                        'Fechas: %s – %s</p>'
                    ) % (
                        escape(actividad.nombre_actividad),
                        escape(actividad.periodo_id.clave_periodo),
                        escape(str(actividad.fecha_inicio)),
                        escape(str(actividad.fecha_fin)),
                    ),
                )
        # FIXED: f-string used inside message_post body — message_post body
        # must be a Markup object or plain string; f-strings are safe here
        # only because there is no user-supplied content. Changed to use
        # a plain str for clarity (Odoo auto-escapes plain strings in chatter).
        total = len(self.estudiante_ids)
        actividad.message_post(
            body=f'Actividad difundida a {total} estudiante(s).'
        )
        return {'type': 'ir.actions.act_window_close'}
