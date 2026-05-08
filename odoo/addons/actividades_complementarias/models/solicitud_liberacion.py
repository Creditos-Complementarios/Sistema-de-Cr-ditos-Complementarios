# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SolicitudLiberacion(models.Model):
    """E-03SC: Solicitud de liberación de créditos complementarios."""

    _name = 'actividad.solicitud.liberacion'
    _description = 'Solicitud de Liberación de Créditos Complementarios'
    _order = 'fecha desc'
    _rec_name = 'estudiante_id'
    _inherit = ['mail.thread']

    estudiante_id = fields.Many2one(
        'res.users', string='Estudiante', required=True,
        default=lambda self: self.env.user, readonly=True,
    )
    fecha = fields.Date(
        string='Fecha de Solicitud', default=fields.Date.today, readonly=True,
    )
    estado = fields.Selection([
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ], string='Estado', default='en_revision', tracking=True, readonly=True)
    creditos_validos = fields.Float(
        string='Créditos Válidos',
        compute='_compute_resumen',
        store=True,
        help='Máximo 2 créditos por tipo de actividad.',
    )
    promedio_desempenio = fields.Float(
        string='Promedio de Desempeño',
        compute='_compute_resumen',
        store=True,
        digits=(4, 2),
    )

    @api.depends('estudiante_id')
    def _compute_resumen(self):
        """MVP: créditos con constancia firmada (máx 2 por tipo)."""
        for rec in self:
            if not rec.estudiante_id:
                rec.creditos_validos = 0.0
                rec.promedio_desempenio = 0.0
                continue
            actividades = self.env['actividad.complementaria'].sudo().search([
                ('alumno_ids', 'in', [rec.estudiante_id.id]),
                ('constancias_firmadas', '=', True),
            ])
            creditos_por_tipo = {}
            for act in actividades:
                tipo = act.tipo_actividad_id.id
                cr = float(act.creditos or 0.0)
                creditos_por_tipo[tipo] = creditos_por_tipo.get(tipo, 0.0) + cr
            rec.creditos_validos = sum(
                min(v, 2.0) for v in creditos_por_tipo.values()
            )
            rec.promedio_desempenio = 0.0   # TODO E-03SC: leer desde inscripciones