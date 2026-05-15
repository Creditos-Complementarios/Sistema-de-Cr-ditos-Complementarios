# -*- coding: utf-8 -*-
# E-02SC: Subida de evidencia de participación por el alumno.
#
# Validaciones (documento Estudiante-Cumplimiento.pdf, pp. 5-6):
#   1. Formato permitido: PDF, JPG, PNG, DOCX.
#   2. Tamaño máximo: 5 MB.
#   3. Plazo abierto: evidence_enabled = True y estado en {en_curso, finalizada}.
#   4. El alumno debe estar inscrito en la actividad.

import base64
import mimetypes

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_EXTENSIONES_PERMITIDAS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
_TAMANO_MAX_BYTES = 5 * 1024 * 1024                      # 5 MB
_ESTADOS_PERMITIDOS = {'en_curso', 'finalizada'}


class WizardEvidencia(models.TransientModel):
    """E-02SC: Wizard para que el alumno suba evidencia de participación."""

    _name = 'actividad.wizard.evidencia'
    _description = 'Subir Evidencia de Participación'

    # ------------------------------------------------------------------
    # Campos
    # ------------------------------------------------------------------

    actividad_id = fields.Many2one(
        'actividad.complementaria', required=True, readonly=True,
    )
    descripcion = fields.Char(string='Descripción breve', required=True,
                              help='Indique brevemente qué demuestra esta evidencia.')
    archivo = fields.Binary(string='Archivo de Evidencia', required=True, attachment=True,
                            help='Formatos: PDF, JPG, PNG, DOCX. Máximo 5 MB.')
    archivo_nombre = fields.Char(string='Nombre del archivo')

    # Solo lectura — usados en la vista
    actividad_nombre = fields.Char(related='actividad_id.name', readonly=True)
    evidence_enabled = fields.Boolean(related='actividad_id.evidence_enabled', readonly=True)
    estado_code = fields.Selection(related='actividad_id.estado_code', readonly=True)

    # ------------------------------------------------------------------
    # Validaciones privadas
    # ------------------------------------------------------------------

    def _validar_plazo(self):
        """Plazo abierto: evidence_enabled=True y estado en {en_curso, finalizada}."""
        self.ensure_one()
        actividad = self.actividad_id
        if not actividad.evidence_enabled:
            raise ValidationError(
                _('El plazo para subir evidencias de «%s» está cerrado. '
                  'El responsable no ha habilitado la carga de evidencias.')
                % actividad.name
            )
        if actividad.estado_code not in _ESTADOS_PERMITIDOS:
            raise ValidationError(
                _('No se pueden subir evidencias: la actividad «%s» '
                  'se encuentra en estado «%s».')
                % (actividad.name, actividad.estado_code)
            )

    def _validar_inscripcion(self):
        """El alumno debe estar inscrito en la actividad."""
        self.ensure_one()
        if self.env.user.id not in self.actividad_id.alumno_ids.ids:
            raise ValidationError(
                _('No puede subir evidencias porque no está inscrito en «%s».')
                % self.actividad_id.name
            )

    def _validar_formato(self):
        """Extensión del archivo debe ser PDF, JPG, PNG o DOCX."""
        self.ensure_one()
        nombre = (self.archivo_nombre or '').strip()
        if not nombre:
            raise ValidationError(
                _('No se pudo determinar el nombre del archivo. '
                  'Por favor vuelva a seleccionarlo.')
            )
        partes = nombre.rsplit('.', 1)
        if len(partes) < 2 or partes[-1].lower() not in _EXTENSIONES_PERMITIDAS:
            extension = partes[-1] if len(partes) > 1 else '(sin extensión)'
            raise ValidationError(
                _('El formato «.%s» no está permitido.\n'
                  'Solo se aceptan: PDF, JPG, PNG, DOCX.')
                % extension
            )

    def _validar_tamano(self):
        """El archivo no debe superar los 5 MB."""
        self.ensure_one()
        try:
            contenido = base64.b64decode(self.archivo)
        except Exception:
            raise ValidationError(
                _('No se pudo leer el archivo. Por favor vuelva a seleccionarlo.')
            )
        tamano = len(contenido)
        if tamano > _TAMANO_MAX_BYTES:
            raise ValidationError(
                _('El archivo supera el tamaño máximo de 5 MB '
                  '(tamaño detectado: %.2f MB). '
                  'Reduzca el tamaño e inténtelo de nuevo.')
                % (tamano / (1024 * 1024))
            )

    # ------------------------------------------------------------------
    # Acción principal
    # ------------------------------------------------------------------

    def action_subir(self):
        """Valida y guarda la evidencia como adjunto de la actividad."""
        self.ensure_one()

        self._validar_plazo()
        self._validar_inscripcion()
        self._validar_formato()
        self._validar_tamano()

        nombre_archivo = self.archivo_nombre or 'evidencia.bin'
        attachment = self.env['ir.attachment'].sudo().create({
            'name': nombre_archivo,
            'datas': self.archivo,
            'res_model': 'actividad.complementaria',
            'res_id': self.actividad_id.id,
            'mimetype': mimetypes.guess_type(nombre_archivo)[0] or 'application/octet-stream',
            'description': self.descripcion,
        })

        self.actividad_id.sudo().message_post(
            body=(
                '<b>📎 Evidencia subida</b><br/>'
                '<b>Descripción:</b> %s<br/>'
                '<b>Archivo:</b> %s<br/>'
                '<b>Alumno:</b> %s'
            ) % (self.descripcion, nombre_archivo, self.env.user.name),
            attachment_ids=[attachment.id],
            subtype_xmlid='mail.mt_note',
        )

        return {'type': 'ir.actions.act_window_close'}
