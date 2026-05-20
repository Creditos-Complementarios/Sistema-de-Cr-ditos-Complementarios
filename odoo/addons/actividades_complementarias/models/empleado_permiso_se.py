# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class EmpleadoPermisoSE(models.Model):
    """SE-01SC: Permisos delegados por el jefe de Servicios Escolares a su personal."""

    _name = 'actividad.empleado.permiso.se'
    _description = 'Permisos de Personal de Servicios Escolares'
    _inherit = ['mail.thread']
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users', string='Empleado', required=True, ondelete='cascade',
    )
    no_empleado = fields.Char(string='No. Empleado')

    # ── Permisos delegables (SE-01SC RN) ─────────────────────────────────────
    perm_aprobar_solicitudes = fields.Boolean(
        string='Aprobar o Rechazar Solicitudes', default=False, tracking=True,
    )
    perm_establecer_fechas = fields.Boolean(
        string='Establecer Fechas de Ventana', default=False, tracking=True,
    )
    perm_generar_reporte = fields.Boolean(
        string='Generar Reporte de Estudiantes Liberados', default=False, tracking=True,
    )

    # Valores originales para el wizard de diff (mismo patrón que empleado_permiso)
    orig_perm_aprobar_solicitudes = fields.Boolean(default=False)
    orig_perm_establecer_fechas = fields.Boolean(default=False)
    orig_perm_generar_reporte = fields.Boolean(default=False)

    fecha_ultimo_uso = fields.Date(string='Último Uso', default=fields.Date.today)

    # ── Constraints ───────────────────────────────────────────────────────────

    _sql_constraints = [
        ('unique_user', 'UNIQUE(user_id)', 'Este usuario ya tiene un registro de permisos SE.'),
    ]

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = [
                '|',
                ('user_id.name', 'ilike', name),
                ('no_empleado', 'ilike', name),
            ] + domain
        return super()._name_search(
            name='', domain=domain, operator=operator, limit=limit, order=order
        )

    @api.constrains('user_id')
    def _check_no_es_jefe(self):
        """RN2: el jefe de SE no debe aparecer en la lista de personal."""
        grupo_se = self.env.ref(
            'actividades_complementarias.group_servicios_escolares',
            raise_if_not_found=False,
        )
        if not grupo_se:
            return
        # Identificar si el usuario es el "jefe" buscando en demo/SII
        # Usamos la misma heurística: si es el único con acceso pleno (admin o primer SE)
        # Para MVP: simplemente verificar que no sea el usuario en sesión si es admin
        for rec in self:
            if rec.user_id == self.env.user and self.env.user.has_group(
                'actividades_complementarias.group_admin_actividades'
            ):
                raise ValidationError(
                    'El administrador no debe estar en la lista de personal de SE.'
                )

    # ── ORM ───────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            for f in ('aprobar_solicitudes', 'establecer_fechas', 'generar_reporte'):
                orig = f'orig_perm_{f}'
                if orig not in vals:
                    vals[orig] = vals.get(f'perm_{f}', False)
        return super().create(vals_list)

    # ── Business logic ────────────────────────────────────────────────────────

    def action_guardar_permisos(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Modificar Permisos',
            'res_model': 'actividad.wizard.guardar.permisos.se',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_permiso_id': self.id},
        }

    def _remover_permisos_inactivos(self):
        """Cron: remueve permisos sin uso en los últimos 30 días (RN4 SE-01SC)."""
        limite = date.today() - timedelta(days=30)
        inactivos = self.search([('fecha_ultimo_uso', '<', limite)])
        inactivos.write({
            'perm_aprobar_solicitudes': False,
            'perm_establecer_fechas': False,
            'perm_generar_reporte': False,
        })
        for emp in inactivos:
            emp.message_post(
                body='Permisos removidos automáticamente por 30 días de inactividad.'
            )
