# -*- coding: utf-8 -*-
"""
DEP-C-02SC: Enviar aviso al estudiante desde su expediente.

Permite a la División de Estudios Profesionales y al Coordinador
enviar una notificación interna de Odoo a un estudiante específico
después de consultar su expediente de actividades complementarias.

Reglas de negocio:
    - El estudiante debe tener una cuenta activa en el sistema.
    - No se puede enviar aviso si el estudiante ya liberó sus créditos
      (estado_liberacion = 'liberado').
    - No se puede modificar el expediente del estudiante.
"""
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardAvisoEstudiante(models.TransientModel):
    _name = 'actividad.wizard.aviso.estudiante'
    _description = 'Enviar Aviso al Estudiante — DEP-C-02SC'

    # ── Estudiante destinatario ─────────────────────────────────────────────
    estudiante_id = fields.Many2one(
        'sii.estudiante',
        string='Estudiante',
        required=True,
        readonly=True,
    )

    # ── Información resumida del estudiante ─────────────────────────────────
    info_html = fields.Html(
        string='Datos del estudiante',
        compute='_compute_info_html',
        store=False,
        sanitize=False,
    )

    # ── Contenido del aviso ─────────────────────────────────────────────────
    asunto = fields.Char(
        string='Asunto',
        required=True,
        default='Aviso sobre tus Actividades Complementarias',
        help='Asunto del mensaje que recibirá el estudiante.',
    )
    mensaje = fields.Text(
        string='Mensaje',
        required=True,
        default=(
            'Estimado alumno,\n\n'
            'Te informamos que debes atender tus actividades complementarias. '
            'Por favor, accede al sistema para revisar tu expediente.\n\n'
            'Atentamente,\n'
            'División de Estudios Profesionales'
        ),
        help='Cuerpo del aviso que recibirá el estudiante.',
    )

    # ───────────────────────────────────────────────────────────────────────
    # Defaults
    # ───────────────────────────────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        ctx = self.env.context
        estudiante_id = ctx.get('default_estudiante_id') or ctx.get('active_id')
        if estudiante_id:
            vals['estudiante_id'] = estudiante_id
        return vals

    # ───────────────────────────────────────────────────────────────────────
    # Computed
    # ───────────────────────────────────────────────────────────────────────

    @api.depends('estudiante_id')
    def _compute_info_html(self):
        for rec in self:
            e = rec.estudiante_id
            if not e:
                rec.info_html = ''
                continue

            def row(label, value):
                return (
                    f'<tr>'
                    f'<td style="padding:4px 12px;font-weight:600;color:#555;'
                    f'white-space:nowrap;width:180px;">{label}</td>'
                    f'<td style="padding:4px 12px;color:#222;">{value or "—"}</td>'
                    f'</tr>'
                )

            nombre_completo = (
                f'{e.nombre} {e.apellido_paterno}'
                + (f' {e.apellido_materno}' if e.apellido_materno else '')
            )
            rows = ''.join([
                row('No. Control', e.no_control),
                row('Nombre', nombre_completo),
                row('Carrera', e.id_carrera.clave_carrera if e.id_carrera else ''),
                row('Semestre', e.semestre),
                row('Grupo', e.grupo),
                row('Estado', e.estado_estudiante),
                row('Estado Liberación', e.estado_liberacion),
                row('Correo', e.correo),
            ])

            # Advertencia si ya tiene créditos completos
            liberado = (e.estado_liberacion or '').lower() in [
                'liberado', 'creditos completos', 'completado'
            ]
            if liberado:
                advertencia = (
                    '<div style="background:#fdecea;border-left:4px solid #c0392b;'
                    'padding:8px 14px;margin-bottom:8px;border-radius:4px;">'
                    '<strong style="color:#c0392b;">⚠ Atención:</strong> '
                    'Este estudiante ya tiene sus créditos completos. '
                    'No se puede enviar un aviso.'
                    '</div>'
                )
            else:
                advertencia = ''

            rec.info_html = Markup(
                '<div style="font-family:sans-serif;">'
                '{advertencia}'
                '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
                '<tbody>{rows}</tbody>'
                '</table>'
                '</div>'
            ).format(advertencia=Markup(advertencia), rows=Markup(rows))

    # ───────────────────────────────────────────────────────────────────────
    # Acción principal
    # ───────────────────────────────────────────────────────────────────────

    def action_enviar_aviso(self):
        """DEP-C-02SC paso 1.4: enviar aviso al estudiante seleccionado.

        Validaciones:
            - El estudiante debe tener una cuenta activa en el sistema.
            - No se puede enviar si el estudiante ya liberó sus créditos.
        """
        self.ensure_one()
        e = self.estudiante_id

        # Validación 3: créditos completos
        liberado = (e.estado_liberacion or '').lower() in [
            'liberado', 'creditos completos', 'completado'
        ]
        if liberado:
            raise ValidationError(
                f'El estudiante "{e.nombre} {e.apellido_paterno}" ya tiene sus '
                'créditos completos. No se puede enviar un aviso.'
            )

        # Buscar cuenta del estudiante en Odoo
        usuario = self.env['res.users'].sudo().search(
            [('login', '=', e.correo)], limit=1
        )
        if not usuario:
            raise ValidationError(
                f'El estudiante "{e.nombre} {e.apellido_paterno}" '
                f'(correo: {e.correo or "sin correo registrado"}) '
                'no tiene una cuenta activa en el sistema.'
            )

        # Construir el cuerpo del mensaje con Markup
        cuerpo = Markup(
            '<p><strong>{asunto}</strong></p>'
            '<p>{mensaje}</p>'
            '<p style="color:#888;font-size:11px;">'
            'Enviado por {remitente} — División de Estudios Profesionales'
            '</p>'
        ).format(
            asunto=self.asunto,
            mensaje=self.mensaje.replace('\n', '<br/>'),
            remitente=self.env.user.name,
        )

        # Enviar como DM en Conversaciones para que la notificación
        # llegue a la bandeja de entrada del estudiante
        try:
            channel = self.env['discuss.channel'].sudo().with_context(
                mail_create_nosubscribe=True,
            )._get_or_create_direct_message_channel(usuario.id)
            channel.sudo().message_post(
                body=cuerpo,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=self.env.user.partner_id.id,
                notify_by_email=False,
            )
        except Exception:
            # Fallback: mensaje directo al partner del estudiante
            self.env['mail.thread'].sudo().message_notify(
                partner_ids=usuario.partner_id.ids,
                body=cuerpo,
                subject=self.asunto,
                author_id=self.env.user.partner_id.id,
            )

        return {'type': 'ir.actions.act_window_close'}
