# -*- coding: utf-8 -*-
from odoo import models, fields


class InicioSesion(models.Model):
    _name = 'creditos.inicio.sesion'
    _description = 'Control de Acceso al Sistema'

    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        required=True,
        ondelete='cascade',
    )
    tipo_usuario_id = fields.Many2one(
        'creditos.tipo.usuario',
        string='Tipo de Usuario',
        required=True,
    )
    nip = fields.Char(string='NIP', required=True)
    activo = fields.Boolean(string='Activo', default=True)


class TipoUsuario(models.Model):
    _name = 'creditos.tipo.usuario'
    _description = 'Tipo de Usuario del Sistema'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
