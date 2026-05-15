# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizardGuardarPermisosSE(models.TransientModel):
    """Wizard de confirmación de cambios de permisos para personal de SE."""

    _name = 'actividad.wizard.guardar.permisos.se'
    _description = 'Confirmación de cambios de permisos SE'

    permiso_id = fields.Many2one(
        'actividad.empleado.permiso.se', required=True, readonly=True,
    )
    perm_aprobar_solicitudes = fields.Boolean(string='Aprobar o Rechazar Solicitudes')
    perm_establecer_fechas = fields.Boolean(string='Establecer Fechas de Ventana')
    perm_generar_reporte = fields.Boolean(string='Generar Reporte de Liberados')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        pid = self.env.context.get('default_permiso_id')
        if pid:
            p = self.env['actividad.empleado.permiso.se'].browse(pid)
            res.update({
                'permiso_id': p.id,
                'perm_aprobar_solicitudes': p.perm_aprobar_solicitudes,
                'perm_establecer_fechas': p.perm_establecer_fechas,
                'perm_generar_reporte': p.perm_generar_reporte,
            })
        return res

    def action_confirmar(self):
        self.ensure_one()
        self.permiso_id.write({
            'perm_aprobar_solicitudes': self.perm_aprobar_solicitudes,
            'perm_establecer_fechas': self.perm_establecer_fechas,
            'perm_generar_reporte': self.perm_generar_reporte,
            'orig_perm_aprobar_solicitudes': self.perm_aprobar_solicitudes,
            'orig_perm_establecer_fechas': self.perm_establecer_fechas,
            'orig_perm_generar_reporte': self.perm_generar_reporte,
        })
        self.permiso_id.message_post(
            body=(
                f'Permisos actualizados por <b>{self.env.user.name}</b>:<br/>'
                f'• Aprobar/Rechazar solicitudes: '
                f'<b>{"Sí" if self.perm_aprobar_solicitudes else "No"}</b><br/>'
                f'• Establecer fechas de ventana: '
                f'<b>{"Sí" if self.perm_establecer_fechas else "No"}</b><br/>'
                f'• Generar reporte: '
                f'<b>{"Sí" if self.perm_generar_reporte else "No"}</b>'
            ),
            subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestión de Personal SE',
            'res_model': 'actividad.empleado.permiso.se',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_cancelar(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestión de Personal SE',
            'res_model': 'actividad.empleado.permiso.se',
            'view_mode': 'list,form',
            'target': 'current',
        }
