# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError


class WizardEvidencia(models.TransientModel):
    """E-02SC: subida de evidencia de participación por el alumno."""

    _name = 'actividad.wizard.evidencia'
    _description = 'Subir Evidencia de Participación'

    actividad_id = fields.Many2one(
        'actividad.complementaria', required=True, readonly=True,
    )
    descripcion = fields.Char(string='Descripción breve', required=True)
    archivo = fields.Binary(string='Archivo', required=True, attachment=True)
    archivo_nombre = fields.Char(string='Nombre del archivo')

    def action_subir(self):
        self.ensure_one()
        if not self.archivo:
            raise ValidationError('Debe seleccionar un archivo.')
        attachment = self.env['ir.attachment'].sudo().create({
            'name': self.archivo_nombre or 'evidencia',
            'datas': self.archivo,
            'res_model': 'actividad.complementaria',
            'res_id': self.actividad_id.id,
        })
        self.actividad_id.sudo().message_post(
            body=(
                f'<b>Evidencia:</b> {self.descripcion}<br/>'
                f'Subida por {self.env.user.name}.'
            ),
            attachment_ids=[attachment.id],
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
