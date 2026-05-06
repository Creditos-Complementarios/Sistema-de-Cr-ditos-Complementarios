# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizardGuardarPermisos(models.TransientModel):
    """Wizard que muestra el diff de permisos antes de confirmar el guardado."""
    _name = 'actividad.wizard.guardar.permisos'
    _description = 'Confirmación de cambios de permisos de personal'

    permiso_id = fields.Many2one(
        'actividad.empleado.permiso',
        required=True,
        readonly=True,
    )
    perm_modificar_actividades = fields.Boolean(string='Modificar Actividades Complementarias')
    perm_difundir_actividades = fields.Boolean(string='Difundir Actividades')
    perm_asignar_alumnos = fields.Boolean(string='Asignar Alumnos a Actividad')
    perm_enviar_catalogo = fields.Boolean(string='Enviar al Catálogo')
    resumen_html = fields.Html(
        compute='_compute_resumen_html',
        store=False,
        sanitize=False,
    )

    # ── Computes ─────────────────────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        permiso_id = self.env.context.get('default_permiso_id')
        if permiso_id:
            p = self.env['actividad.empleado.permiso'].browse(permiso_id)
            res.update({
                'permiso_id': p.id,
                'perm_modificar_actividades': p.perm_modificar_actividades,
                'perm_difundir_actividades': p.perm_difundir_actividades,
                'perm_asignar_alumnos': p.perm_asignar_alumnos,
                'perm_enviar_catalogo': p.perm_enviar_catalogo,
            })
        return res

    @api.depends('permiso_id', 'perm_modificar_actividades', 'perm_difundir_actividades',
                 'perm_asignar_alumnos', 'perm_enviar_catalogo')
    def _compute_resumen_html(self):
        for rec in self:
            p = rec.permiso_id
            if not p:
                rec.resumen_html = ''
                continue

            empleado = p.user_id.name or '—'
            depto = p.departamento_id.name if p.departamento_id else '—'

            permisos = [
                ('Modificar Actividades Complementarias',
                 p.perm_modificar_actividades,
                 rec.perm_modificar_actividades),
                ('Difundir Actividades',
                 p.perm_difundir_actividades,
                 rec.perm_difundir_actividades),
                ('Asignar Alumnos a Actividad',
                 p.perm_asignar_alumnos,
                 rec.perm_asignar_alumnos),
                ('Enviar al Catálogo',
                 p.perm_enviar_catalogo,
                 rec.perm_enviar_catalogo),
            ]

            def badge(val):
                color, text = ('#17a589', 'Activo') if val else ('#c0392b', 'Inactivo')
                return (
                    f'<span style="background:{color};color:#fff;'
                    f'padding:2px 9px;border-radius:3px;font-size:11px;">'
                    f'{text}</span>'
                )

            hay_cambios = any(a != d for _, a, d in permisos)
            filas = ''
            for nombre, antes, despues in permisos:
                cambio = antes != despues
                bg = '#fef9e7' if cambio else ''
                if cambio:
                    celda = f'{badge(antes)}&nbsp;→&nbsp;{badge(despues)}'
                else:
                    celda = f'<span style="color:#aaa;">{badge(antes)}</span>'
                filas += (
                    f'<tr style="background:{bg};">'
                    f'<td style="padding:7px 12px;font-weight:{"600" if cambio else "400"};">'
                    f'{nombre}</td>'
                    f'<td style="padding:7px 12px;text-align:center;">{celda}</td>'
                    f'</tr>'
                )

            if not hay_cambios:
                aviso = (
                    '<div style="background:#fef9e7;border-left:4px solid #f39c12;'
                    'padding:8px 14px;margin-bottom:10px;border-radius:4px;">'
                    '<strong>⚠ No hay cambios de permisos para confirmar.</strong>'
                    '</div>'
                )
            else:
                aviso = ''

            rec.resumen_html = f'''
<div style="font-family:sans-serif;font-size:13px;">
  <p style="margin:0 0 10px;">
    Empleado: <strong>{empleado}</strong>
    &nbsp;|&nbsp; Departamento: <strong>{depto}</strong>
  </p>
  {aviso}
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="background:#2c3e50;color:#fff;">
        <th style="padding:7px 12px;text-align:left;font-weight:600;">Permiso</th>
        <th style="padding:7px 12px;text-align:center;font-weight:600;width:200px;">
          Estado
        </th>
      </tr>
    </thead>
    <tbody>{filas}</tbody>
  </table>
</div>'''

    # ── Business logic ────────────────────────────────────────────────────────

    def action_confirmar(self):
        """Persiste los permisos editados y regresa a la lista."""
        self.ensure_one()
        p = self.permiso_id
        p.write({
            'perm_modificar_actividades': self.perm_modificar_actividades,
            'perm_difundir_actividades': self.perm_difundir_actividades,
            'perm_asignar_alumnos': self.perm_asignar_alumnos,
            'perm_enviar_catalogo': self.perm_enviar_catalogo,
            'orig_perm_modificar_actividades': self.perm_modificar_actividades,
            'orig_perm_difundir_actividades': self.perm_difundir_actividades,
            'orig_perm_asignar_alumnos': self.perm_asignar_alumnos,
            'orig_perm_enviar_catalogo': self.perm_enviar_catalogo,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestión de Personal',
            'res_model': 'actividad.empleado.permiso',
            'view_mode': 'list,kanban,form',
            'target': 'current',
        }

    def action_cancelar(self):
        """Cancela sin guardar y regresa a la lista."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestión de Personal',
            'res_model': 'actividad.empleado.permiso',
            'view_mode': 'list,kanban,form',
            'target': 'current',
        }
