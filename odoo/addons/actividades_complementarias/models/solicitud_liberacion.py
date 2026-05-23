# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

CREDITOS_MINIMOS = 5.0

_NIVEL_LABELS = {
    0: 'Insuficiente',
    1: 'Suficiente',
    2: 'Bueno',
    3: 'Notable',
    4: 'Excelente',
}


class SolicitudLiberacion(models.Model):
    """E-03SC: Expediente y solicitud de liberación de créditos complementarios."""

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
        ('borrador',    'Borrador'),
        ('en_revision', 'En Revisión'),
        ('aprobada',    'Aprobada'),
        ('rechazada',   'Rechazada'),
    ], string='Estado', default='borrador', tracking=True, readonly=True)

    # ── Resumen computado ────────────────────────────────────────────────────
    creditos_validos = fields.Float(
        string='Créditos Válidos',
        compute='_compute_resumen',
        store=True,
        digits=(4, 1),
        help='Máximo 2 créditos contabilizados por tipo de actividad (RN1).',
    )
    promedio_desempenio = fields.Float(
        string='Promedio de Desempeño',
        compute='_compute_resumen',
        store=True,
        digits=(4, 2),
        help='Media aritmética de los niveles de desempeño, redondeada al entero más próximo.',
    )
    promedio_label = fields.Char(
        string='Nivel de Desempeño',
        compute='_compute_resumen',
        store=True,
    )
    puede_solicitar = fields.Boolean(
        compute='_compute_puede_solicitar',
        store=False,
        help='True cuando cumple RN2 (≥5 créditos) y RN3 (sin solicitud activa).',
    )
    razon_bloqueado = fields.Char(
        compute='_compute_puede_solicitar',
        store=False,
    )
    # ── Revisión por Servicios Escolares (SE-02SC) ───────────────────────────
    ventana_id = fields.Many2one(
        'actividad.ventana.liberacion',
        string='Ventana de Evaluación',
        readonly=True,
        ondelete='restrict',
    )
    aprobado_por = fields.Many2one(
        'res.users', string='Aprobado/Rechazado por', readonly=True,
    )
    observaciones_se = fields.Text(
        string='Observaciones de Servicios Escolares',
        help='Obligatorio en caso de rechazo (RN3).',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    @api.depends('estudiante_id')
    def _compute_resumen(self):
        """
        RN1: máx 2 créditos por tipo de actividad.
        Promedio: media de performance_level en actividad.inscripcion,
        redondeada al entero más próximo (paso 5 del flujo).
        """
        for rec in self:
            if not rec.estudiante_id:
                rec.creditos_validos = 0.0
                rec.promedio_desempenio = 0.0
                rec.promedio_label = ''
                continue

            acreditadas = self.env['actividad.complementaria'].sudo().search([
                ('alumno_ids', 'in', [rec.estudiante_id.id]),
                ('constancias_firmadas', '=', True),
            ])

            # RN1 ─ cap de 2 créditos por tipo
            creditos_por_tipo = {}
            for act in acreditadas:
                tipo = act.tipo_actividad_id.id
                cr = float(act.creditos or 0.0)
                creditos_por_tipo[tipo] = creditos_por_tipo.get(tipo, 0.0) + cr
            rec.creditos_validos = sum(
                min(v, 2.0) for v in creditos_por_tipo.values()
            )

            # Promedio ─ desde actividad.inscripcion
            partner = rec.estudiante_id.partner_id
            inscripciones = self.env['actividad.inscripcion'].sudo().search([
                ('actividad_id', 'in', acreditadas.ids),
                ('partner_id', '=', partner.id),
                ('performance_level', '!=', False),
                ('performance_level', '!=', '0'),   # insuficiente no promedia
            ])
            if inscripciones:
                niveles = [int(i.performance_level) for i in inscripciones]
                promedio_redondeado = round(sum(niveles) / len(niveles))
                rec.promedio_desempenio = promedio_redondeado
                rec.promedio_label = _NIVEL_LABELS.get(promedio_redondeado, '')
            else:
                rec.promedio_desempenio = 0.0
                rec.promedio_label = 'Sin evaluación registrada'

    @api.depends('creditos_validos', 'estudiante_id')
    def _compute_puede_solicitar(self):
        """
        RN2: necesita ≥ 5 créditos válidos.
        RN3: sin solicitud en_revision activa; si ya fue aprobada → bloqueado permanente.
        """
        for rec in self:
            uid = rec.estudiante_id.id
            rid = rec._origin.id or 0

            # RN3 permanente: ya liberado
            liberado = self.search([
                ('estudiante_id', '=', uid),
                ('estado', '=', 'aprobada'),
            ], limit=1)
            if liberado:
                rec.puede_solicitar = False
                rec.razon_bloqueado = 'Tus actividades complementarias ya fueron liberadas.'
                continue

            hoy = date.today()
            ventana_activa = self.env['actividad.ventana.liberacion'].sudo().search([
                ('fecha_inicio', '<=', hoy),
                ('fecha_fin', '>=', hoy),
            ], limit=1)
            if not ventana_activa:
                rec.puede_solicitar = False
                rec.razon_bloqueado = (
                    'No hay un período habilitado para enviar solicitudes. '
                    'Consulte a Servicios Escolares.'
                )
                continue

            # RN2
            if rec.creditos_validos < CREDITOS_MINIMOS:
                rec.puede_solicitar = False
                rec.razon_bloqueado = (
                    f'Necesitas {int(CREDITOS_MINIMOS)} créditos válidos. '
                    f'Actualmente tienes {rec.creditos_validos:.1f}.'
                )
                continue

            # RN3: solicitud en revisión existente
            en_revision = self.search([
                ('estudiante_id', '=', uid),
                ('estado', '=', 'en_revision'),
                ('id', '!=', rid),
            ], limit=1)
            if en_revision:
                rec.puede_solicitar = False
                rec.razon_bloqueado = 'Ya tienes una solicitud en revisión.'
                continue

            rec.puede_solicitar = True
            rec.razon_bloqueado = ''

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────

    @api.constrains('estudiante_id', 'estado')
    def _check_solicitud_unica(self):
        """RN3: solo una solicitud en_revision o aprobada por estudiante."""
        for rec in self:
            if rec.estado not in ('en_revision', 'aprobada'):
                continue
            duplicado = self.search([
                ('estudiante_id', '=', rec.estudiante_id.id),
                ('estado', 'in', ['en_revision', 'aprobada']),
                ('id', '!=', rec.id),
            ], limit=1)
            if duplicado:
                raise ValidationError(
                    'Ya existe una solicitud activa (En Revisión o Aprobada) '
                    'para este estudiante. Solo puede haber una a la vez.'
                )

    @api.constrains('estudiante_id')
    def _check_estudiante_es_usuario(self):
        """E-03SC: el estudiante de la solicitud debe ser el usuario autenticado."""
        for rec in self:
            if (
                not self.env.user.has_group('actividades_complementarias.group_admin_actividades')
                and not self.env.user.has_group('actividades_complementarias.group_servicios_escolares')
                and rec.estudiante_id.id != self.env.user.id
            ):
                raise ValidationError(
                    'Solo puedes crear solicitudes de liberación a tu propio nombre.'
                )

    # ────────────────────────────────────────────────────────────────────────
    # Business logic
    # ────────────────────────────────────────────────────────────────────────

    def action_solicitar_liberacion(self):
        """
        Flujo principal paso 7: registra la solicitud en estado En Revisión.
        Valida RN2 y RN3 antes de transicionar.
        """
        self.ensure_one()
        if self.creditos_validos < CREDITOS_MINIMOS:
            raise ValidationError(
                f'Necesitas al menos {int(CREDITOS_MINIMOS)} créditos válidos. '
                f'Actualmente tienes {self.creditos_validos:.1f}.'
            )
        liberado = self.search([
            ('estudiante_id', '=', self.estudiante_id.id),
            ('estado', '=', 'aprobada'),
        ], limit=1)
        if liberado:
            raise ValidationError(
                'Tus actividades complementarias ya fueron liberadas. '
                'No puedes realizar una nueva solicitud.'
            )
        en_revision = self.search([
            ('estudiante_id', '=', self.estudiante_id.id),
            ('estado', '=', 'en_revision'),
            ('id', '!=', self.id),
        ], limit=1)
        if en_revision:
            raise ValidationError(
                'Ya tienes una solicitud en revisión. '
                'Espera a que sea resuelta antes de enviar otra.'
            )
        # Asignar la ventana activa al momento de enviar
        hoy = date.today()
        ventana_activa = self.env['actividad.ventana.liberacion'].sudo().search([
            ('fecha_inicio', '<=', hoy),
            ('fecha_fin', '>=', hoy),
        ], limit=1)
        if not ventana_activa:
            raise ValidationError(
                'No hay un período habilitado para enviar solicitudes de liberación. '
                'Consulte a Servicios Escolares.'
            )
        self.write({'estado': 'en_revision', 'ventana_id': ventana_activa.id})
        self.message_post(
            body=(
                f'Solicitud enviada por <b>{self.estudiante_id.name}</b>.<br/>'
                f'Créditos válidos: <b>{self.creditos_validos:.1f}</b>.<br/>'
                f'Nivel de desempeño: <b>{self.promedio_label}</b>.'
            ),
            subtype_xmlid='mail.mt_comment',
        )

    def action_aprobar_se(self):
        """SE-02SC: Servicios Escolares aprueba la solicitud."""
        self.ensure_one()
        if self.estado != 'en_revision':
            raise ValidationError('Solo se pueden aprobar solicitudes en revisión (RN1).')
        self.write({'estado': 'aprobada', 'aprobado_por': self.env.user.id})
        self._notificar_estudiante_se(aprobada=True)

    def action_rechazar_se(self):
        """SE-02SC flujo alterno: Servicios Escolares rechaza la solicitud."""
        self.ensure_one()
        if self.estado != 'en_revision':
            raise ValidationError('Solo se pueden rechazar solicitudes en revisión (RN1).')
        if not self.observaciones_se or not self.observaciones_se.strip():
            raise ValidationError(
                'Las observaciones son obligatorias para rechazar una solicitud (RN3).'
            )
        self.write({'estado': 'rechazada', 'aprobado_por': self.env.user.id})
        self._notificar_estudiante_se(aprobada=False)

    def action_ver_expediente_alumno(self):
        """Abre el expediente (sii.estudiante) del alumno en esta solicitud."""
        self.ensure_one()
        estudiante = self.env['sii.estudiante'].sudo().search(
            [('no_control', '=', self.estudiante_id.login)], limit=1
        )
        if not estudiante:
            raise ValidationError(
                f'No se encontró un expediente en el SII para el usuario '
                f'"{self.estudiante_id.name}" (login: {self.estudiante_id.login}).'
            )
        return {
            'type': 'ir.actions.act_window',
            'name': f'Expediente — {self.estudiante_id.name}',
            'res_model': 'sii.estudiante',
            'res_id': estudiante.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(False, 'form')],
        }

    def _notificar_estudiante_se(self, aprobada):
        """Publica mensaje en el chatter y notifica al estudiante."""
        partner = self.estudiante_id.partner_id
        if aprobada:
            body = (
                f'<p>✅ Tu solicitud de liberación ha sido <strong>aprobada</strong> '
                f'por {self.aprobado_por.name}.</p>'
            )
        else:
            body = (
                f'<p>❌ Tu solicitud de liberación ha sido <strong>rechazada</strong>.</p>'
                f'<p><strong>Observaciones:</strong> {self.observaciones_se}</p>'
            )
        self.message_post(
            body=body,
            partner_ids=partner.ids if partner else [],
            subtype_xmlid='mail.mt_comment',
        )
