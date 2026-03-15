# -*- coding: utf-8 -*-
from odoo import models, fields


class Notificacion(models.Model):
    _name = 'creditos.notificacion'
    _description = 'Notificaciones del Sistema de Créditos Complementarios'
    _order = 'fecha_envio desc'

    mensaje = fields.Text(string='Mensaje', required=True)
    fecha_envio = fields.Datetime(
        string='Fecha de Envío',
        default=fields.Datetime.now,
        readonly=True,
    )
    encabezado = fields.Char(string='Encabezado / Asunto', required=True)
    estado = fields.Selection(
        selection=[
            ('no_leida', 'No Leída'),
            ('leida', 'Leída'),
        ],
        string='Estado',
        default='no_leida',
    )
    usuario_ids = fields.Many2many(
        'res.users',
        'creditos_notificacion_usuario_rel',
        'notificacion_id',
        'usuario_id',
        string='Destinatarios',
    )


class UsuarioEnNotificacion(models.Model):
    _name = 'creditos.usuario.notificacion'
    _description = 'Relación Usuario-Notificación'

    usuario_id = fields.Many2one('res.users', string='Usuario', required=True, ondelete='cascade')
    notificacion_id = fields.Many2one(
        'creditos.notificacion',
        string='Notificación',
        required=True,
        ondelete='cascade',
    )
    leida = fields.Boolean(string='Leída', default=False)
