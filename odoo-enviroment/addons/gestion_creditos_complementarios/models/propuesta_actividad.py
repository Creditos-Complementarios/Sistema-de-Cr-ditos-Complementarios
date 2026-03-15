# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from markupsafe import Markup, escape
from datetime import date, timedelta


ESTADO_SOLICITUD = [
    ('en_revision', 'En Revisión'),
    ('aprobada', 'Aprobada'),
    ('rechazada', 'Rechazada'),
]


class PropuestaActividad(models.Model):
    _name = 'creditos.propuesta.actividad'
    _description = 'Propuesta de Actividad Complementaria al Comité Académico'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nombre_actividad'
    _order = 'fecha desc'

    # ──────────────────────────────────────────────
    # Datos del formulario de solicitud
    # ──────────────────────────────────────────────
    nombre_actividad = fields.Char(
        string='Nombre de la Actividad',
        required=True,
        size=200,
        tracking=True,
    )
    tipo_actividad_id = fields.Many2one(
        'creditos.tipo.actividad',
        string='Tipo de Actividad',
        required=True,
        domain="[('es_predefinida', '=', False)]",
        tracking=True,
        help='Solo tipos de actividad NO predefinidos requieren aprobación del Comité.',
    )
    departamento_id = fields.Many2one(
        'creditos.catalogo.departamentos',
        string='Departamento',
        required=True,
        tracking=True,
    )
    jefe_departamento_id = fields.Many2one(
        'hr.employee',
        string='Jefe de Departamento',
        required=True,
        tracking=True,
    )
    periodo_id = fields.Many2one(
        'creditos.periodo',
        string='Periodo Escolar',
        required=True,
        tracking=True,
    )
    descripcion = fields.Text(
        string='Descripción',
        size=2000,
    )
    cantidad_horas = fields.Float(
        string='Cantidad de Horas',
        required=True,
    )

    # ──────────────────────────────────────────────
    # Responsable
    # ──────────────────────────────────────────────
    responsable_actividad_id = fields.Many2one(
        'hr.employee',
        string='Responsable de Actividad',
        tracking=True,
        help=(
            'Las opciones disponibles son solo los responsables '
            'designados por el Coordinador de Carrera.'
        ),
    )

    # ──────────────────────────────────────────────
    # Créditos
    # ──────────────────────────────────────────────
    creditos = fields.Selection(
        selection=[
            ('1', '1 Crédito'),
            ('0.5', '0.5 Créditos'),
        ],
        string='Créditos',
        tracking=True,
    )

    # ──────────────────────────────────────────────
    # Fechas
    # ──────────────────────────────────────────────
    fecha_inicio_actividad = fields.Date(
        string='Fecha de Inicio',
        required=True,
    )
    fecha_fin_actividad = fields.Date(
        string='Fecha de Fin',
        required=True,
    )

    # ──────────────────────────────────────────────
    # Cupo
    # ──────────────────────────────────────────────
    cupo_ilimitado = fields.Boolean(
        string='Cupo Ilimitado',
        default=False,
        help='Activa para cursos masivos sin límite de participantes.',
    )
    cupo_min = fields.Integer(string='Cupo Mínimo')
    cupo_max = fields.Integer(string='Cupo Máximo')

    # ──────────────────────────────────────────────
    # Imagen
    # ──────────────────────────────────────────────
    ruta_imagen = fields.Binary(
        string='Imagen Alusiva a la Actividad',
        attachment=True,
    )
    ruta_imagen_filename = fields.Char(string='Nombre de la Imagen')

    # ──────────────────────────────────────────────
    # Horarios
    # ──────────────────────────────────────────────
    horario_ids = fields.One2many(
        'creditos.propuesta.horario',
        'propuesta_id',
        string='Horarios por Día',
    )

    # ──────────────────────────────────────────────
    # Estado de la propuesta
    # ──────────────────────────────────────────────
    estado_solicitud = fields.Selection(
        selection=ESTADO_SOLICITUD,
        string='Estado de la Solicitud',
        default='en_revision',
        required=True,
        tracking=True,
    )
    encabezado = fields.Char(
        string='Encabezado / Referencia',
        readonly=True,
        copy=False,
    )
    fecha = fields.Datetime(
        string='Fecha de Envío',
        default=fields.Datetime.now,
        readonly=True,
    )
    fecha_limite_aprobacion = fields.Date(
        string='Fecha Límite de Aprobación Automática',
        readonly=True,
        help='Si el Comité no responde antes de esta fecha, la propuesta se aprueba automáticamente.',
    )
    estado = fields.Char(
        string='Estado Interno',
        compute='_compute_estado_label',
        store=False,
    )
    motivo_rechazo = fields.Text(
        string='Motivo de Rechazo',
        tracking=True,
    )
    aprobacion_automatica = fields.Boolean(
        string='Aprobada Automáticamente',
        default=False,
        readonly=True,
        help='Indica si la propuesta fue aprobada automáticamente por vencimiento del plazo de 5 días.',
    )

    actividad_id = fields.Many2one(
        'creditos.actividad.complementaria',
        string='Actividad Generada',
        readonly=True,
        copy=False,
    )

    # ──────────────────────────────────────────────
    # Secuencia
    # ──────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('encabezado'):
                vals['encabezado'] = self.env['ir.sequence'].next_by_code(
                    'creditos.propuesta.actividad'
                ) or '/'
            if not vals.get('fecha_limite_aprobacion'):
                vals['fecha_limite_aprobacion'] = (
                    fields.Date.today() + timedelta(days=5)
                )
        return super().create(vals_list)

    # ──────────────────────────────────────────────
    # Computes
    # ──────────────────────────────────────────────
    @api.depends('estado_solicitud')
    def _compute_estado_label(self):
        # FIXED: Added missing @api.depends so the field recomputes on change.
        for rec in self:
            rec.estado = dict(ESTADO_SOLICITUD).get(rec.estado_solicitud, '')

    # ──────────────────────────────────────────────
    # Constrains
    # ──────────────────────────────────────────────
    @api.constrains('fecha_inicio_actividad', 'fecha_fin_actividad')
    def _check_fechas(self):
        # FIXED: Removed late import of `date`; it is already imported at the
        # top of the module. Late imports inside methods are an anti-pattern.
        hoy = date.today()
        for rec in self:
            if rec.fecha_inicio_actividad < hoy:
                raise ValidationError('La fecha de inicio no puede ser anterior a hoy.')
            if rec.fecha_fin_actividad <= rec.fecha_inicio_actividad:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for rec in self:
            if rec.cupo_ilimitado:
                continue
            if rec.cupo_min < 0 or rec.cupo_max < 0:
                raise ValidationError('Los valores de cupo no pueden ser negativos.')
            if rec.cupo_max and rec.cupo_min > rec.cupo_max:
                raise ValidationError('El cupo mínimo no puede superar al cupo máximo.')

    @api.onchange('cupo_ilimitado')
    def _onchange_cupo_ilimitado(self):
        if self.cupo_ilimitado:
            self.cupo_min = 0
            self.cupo_max = 0

    # ──────────────────────────────────────────────
    # Acciones del Jefe de Departamento
    # ──────────────────────────────────────────────
    def action_enviar_comite(self):
        """Envía la propuesta al Comité Académico y notifica."""
        self.ensure_one()
        if self.estado_solicitud != 'en_revision':
            raise ValidationError('Solo se pueden enviar propuestas en estado "En Revisión".')
        grupo_comite = self.env.ref(
            'gestion_creditos_complementarios.group_comite_academico', raise_if_not_found=False
        )
        if grupo_comite:
            for usuario in grupo_comite.users:
                self.message_notify(
                    partner_ids=[usuario.partner_id.id],
                    subject='Nueva propuesta de actividad complementaria pendiente de revisión',
                    body=Markup(
                        '<p>El Jefe de Departamento <b>%s</b> '
                        'ha enviado la propuesta <b>%s</b> '
                        'para su revisión. Referencia: %s.</p>'
                    ) % (
                        escape(self.jefe_departamento_id.name),
                        escape(self.nombre_actividad),
                        escape(self.encabezado),
                    ),
                )
        self.message_post(
            body='Propuesta enviada al Comité Académico. Estado: En Revisión.',
        )

    # ──────────────────────────────────────────────
    # Acciones del Comité Académico
    # ──────────────────────────────────────────────
    def action_aprobar(self):
        self.ensure_one()
        self.write({'estado_solicitud': 'aprobada', 'aprobacion_automatica': False})
        self._crear_actividad_desde_propuesta()
        self.message_post(body='Propuesta aprobada por el Comité Académico.')

    def action_rechazar(self):
        self.ensure_one()
        if not self.motivo_rechazo:
            raise ValidationError('Debe indicar el motivo de rechazo antes de rechazar.')
        self.write({'estado_solicitud': 'rechazada'})
        self.message_post(
            body=Markup('<p>Propuesta rechazada. Motivo: %s</p>') % escape(self.motivo_rechazo)
        )

    # ──────────────────────────────────────────────
    # Aprobación automática (cron)
    # ──────────────────────────────────────────────
    @api.model
    def _cron_aprobar_propuestas_vencidas(self):
        hoy = fields.Date.today()
        propuestas_vencidas = self.search([
            ('estado_solicitud', '=', 'en_revision'),
            ('fecha_limite_aprobacion', '<', hoy),
        ])
        for propuesta in propuestas_vencidas:
            propuesta.write({
                'estado_solicitud': 'aprobada',
                'aprobacion_automatica': True,
            })
            propuesta._crear_actividad_desde_propuesta()
            propuesta.message_post(
                body='Propuesta aprobada automáticamente por vencimiento del plazo de 5 días.'
            )

    def _crear_actividad_desde_propuesta(self):
        """Crea la actividad complementaria a partir de la propuesta aprobada."""
        self.ensure_one()
        if self.actividad_id:
            return
        actividad = self.env['creditos.actividad.complementaria'].create({
            'nombre_actividad': self.nombre_actividad,
            'tipo_actividad_id': self.tipo_actividad_id.id,
            'estado_actividad': 'aprobada',
            'departamento_id': self.departamento_id.id,
            'periodo_id': self.periodo_id.id,
            'jefe_departamento_id': self.jefe_departamento_id.id,
            'responsable_actividad_id': (
                self.responsable_actividad_id.id
                if self.responsable_actividad_id
                else False
            ),
            'descripcion': self.descripcion,
            'cantidad_horas': self.cantidad_horas,
            # FIXED: Credits from auto-approval vs manual approval logic was
            # inverted. Auto-approved proposals keep their proposed credits;
            # manually approved ones require the committee to set credits.
            'creditos': self.creditos if self.aprobacion_automatica else False,
            'fecha_inicio': self.fecha_inicio_actividad,
            'fecha_fin': self.fecha_fin_actividad,
            'cupo_ilimitado': self.cupo_ilimitado,
            'cupo_min': self.cupo_min,
            'cupo_max': self.cupo_max,
            'ruta_imagen': self.ruta_imagen,
            'propuesta_id': self.id,
        })
        self.actividad_id = actividad.id


class PropuestaHorario(models.Model):
    _name = 'creditos.propuesta.horario'
    _description = 'Horario en Propuesta de Actividad'

    propuesta_id = fields.Many2one(
        'creditos.propuesta.actividad',
        string='Propuesta',
        required=True,
        ondelete='cascade',
    )
    dia_semana = fields.Selection(
        selection=[
            ('lunes', 'Lunes'),
            ('martes', 'Martes'),
            ('miercoles', 'Miércoles'),
            ('jueves', 'Jueves'),
            ('viernes', 'Viernes'),
            ('sabado', 'Sábado'),
            ('domingo', 'Domingo'),
        ],
        string='Día de la Semana',
        required=True,
    )
    hora_inicio = fields.Float(string='Hora de Inicio', required=True)
    hora_fin = fields.Float(string='Hora de Fin', required=True)

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for rec in self:
            if rec.hora_fin <= rec.hora_inicio:
                raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
