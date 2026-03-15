# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ActividadComplementaria(models.Model):
    _name = 'creditos.actividad.complementaria'
    _description = 'Actividad Complementaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nombre_actividad'
    _order = 'fecha_inicio desc'

    # ──────────────────────────────────────────────
    # Identificación
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
        tracking=True,
    )
    es_tipo_predefinido = fields.Boolean(
        string='Tipo Predefinido',
        related='tipo_actividad_id.es_predefinida',
        store=True,
        readonly=True,
    )
    estado_actividad = fields.Selection(
        selection=[
            ('aprobada', 'Aprobada'),
            ('rechazada', 'Rechazada'),
            ('pendiente_inicio', 'Pendiente de Inicio'),
            ('en_curso', 'En Curso'),
            ('finalizada', 'Finalizada'),
        ],
        string='Estado',
        default='aprobada',
        required=True,
        tracking=True,
    )
    departamento_id = fields.Many2one(
        'creditos.catalogo.departamentos',
        string='Departamento',
        required=True,
        tracking=True,
    )
    periodo_id = fields.Many2one(
        'creditos.periodo',
        string='Periodo Escolar',
        required=True,
        tracking=True,
    )

    # ──────────────────────────────────────────────
    # Responsables
    # ──────────────────────────────────────────────
    jefe_departamento_id = fields.Many2one(
        'hr.employee',
        string='Jefe de Departamento',
        required=True,
        tracking=True,
    )
    responsable_actividad_id = fields.Many2one(
        'hr.employee',
        string='Responsable de Actividad',
        tracking=True,
        help=(
            'Solo puede seleccionarse entre los responsables '
            'designados por el Coordinador de Carrera.'
        ),
    )

    # ──────────────────────────────────────────────
    # Detalles de la actividad
    # ──────────────────────────────────────────────
    descripcion = fields.Text(
        string='Descripción',
        size=2000,
    )
    cantidad_horas = fields.Float(
        string='Cantidad de Horas',
        required=True,
    )
    creditos = fields.Selection(
        selection=[
            ('1', '1 Crédito'),
            ('0.5', '0.5 Créditos'),
        ],
        string='Créditos',
        tracking=True,
        help='Solo disponible para actividades predefinidas o aprobadas automáticamente.',
    )
    creditos_readonly = fields.Boolean(
        string='Créditos Solo Lectura',
        compute='_compute_creditos_readonly',
        store=False,
    )

    # ──────────────────────────────────────────────
    # Fechas
    # ──────────────────────────────────────────────
    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        required=True,
        tracking=True,
    )
    fecha_fin = fields.Date(
        string='Fecha de Fin',
        required=True,
        tracking=True,
    )

    # ──────────────────────────────────────────────
    # Cupo
    # ──────────────────────────────────────────────
    cupo_ilimitado = fields.Boolean(
        string='Cupo Ilimitado',
        default=False,
        help='Marcar para cursos masivos sin límite de participantes.',
    )
    cupo_min = fields.Integer(string='Cupo Mínimo')
    cupo_max = fields.Integer(string='Cupo Máximo')

    # ──────────────────────────────────────────────
    # Imagen y archivos
    # ──────────────────────────────────────────────
    ruta_imagen = fields.Binary(
        string='Imagen Alusiva',
        attachment=True,
    )
    ruta_imagen_filename = fields.Char(string='Nombre de Imagen')

    # ──────────────────────────────────────────────
    # Relaciones
    # ──────────────────────────────────────────────
    horario_ids = fields.One2many(
        'creditos.horario.actividad',
        'actividad_id',
        string='Horarios',
    )
    lista_estudiante_ids = fields.One2many(
        'creditos.lista.estudiante.actividad',
        'actividad_id',
        string='Lista de Estudiantes',
    )
    evidencia_ids = fields.One2many(
        'creditos.evidencia.actividad',
        'actividad_id',
        string='Evidencias',
    )
    propuesta_id = fields.Many2one(
        'creditos.propuesta.actividad',
        string='Propuesta de Origen',
        readonly=True,
    )
    constancia_ids = fields.One2many(
        'creditos.constancia',
        'actividad_id',
        string='Constancias',
    )

    # ──────────────────────────────────────────────
    # Campos computados
    # ──────────────────────────────────────────────
    total_estudiantes = fields.Integer(
        string='Total de Estudiantes',
        compute='_compute_total_estudiantes',
        store=True,
    )
    constancias_listas = fields.Boolean(
        string='Constancias Listas para Firmar',
        compute='_compute_constancias_listas',
        store=False,
    )

    # ──────────────────────────────────────────────
    # Computes
    # ──────────────────────────────────────────────
    @api.depends('lista_estudiante_ids')
    def _compute_total_estudiantes(self):
        for rec in self:
            rec.total_estudiantes = len(rec.lista_estudiante_ids)

    @api.depends('estado_actividad', 'lista_estudiante_ids.nivel_desempeno')
    def _compute_constancias_listas(self):
        for rec in self:
            if rec.estado_actividad == 'finalizada':
                rec.constancias_listas = bool(rec.lista_estudiante_ids) and all(
                    bool(e.nivel_desempeno)
                    for e in rec.lista_estudiante_ids
                )
            else:
                rec.constancias_listas = False

    @api.depends('tipo_actividad_id', 'propuesta_id', 'propuesta_id.estado_solicitud',
                 'propuesta_id.aprobacion_automatica')
    def _compute_creditos_readonly(self):
        for rec in self:
            aprobada_comite = (
                rec.propuesta_id
                and rec.propuesta_id.estado_solicitud == 'aprobada'
                and not rec.propuesta_id.aprobacion_automatica
            )
            rec.creditos_readonly = bool(aprobada_comite)

    # ──────────────────────────────────────────────
    # Onchanges
    # ──────────────────────────────────────────────
    @api.onchange('tipo_actividad_id')
    def _onchange_tipo_actividad(self):
        """Limpia créditos si el tipo cambia a uno no predefinido."""
        if not self.es_tipo_predefinido:
            self.creditos = False

    @api.onchange('cupo_ilimitado')
    def _onchange_cupo_ilimitado(self):
        if self.cupo_ilimitado:
            self.cupo_min = 0
            self.cupo_max = 0

    # ──────────────────────────────────────────────
    # Constrains
    # ──────────────────────────────────────────────
    @api.constrains('nombre_actividad', 'periodo_id')
    def _check_nombre_duplicado(self):
        for rec in self:
            dominio = [
                ('nombre_actividad', '=', rec.nombre_actividad),
                ('periodo_id', '=', rec.periodo_id.id),
                ('estado_actividad', 'not in', ['rechazada', 'finalizada']),
                ('id', '!=', rec.id),
            ]
            if self.search_count(dominio):
                raise ValidationError(
                    'Ya existe una actividad activa con ese nombre en el mismo periodo escolar.'
                )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        # FIXED: Removed the check fecha_inicio < today. Dates created from a
        # propuesta (cron or manual) may have past dates at the moment the
        # actividad is created programmatically. Validate only the logical
        # ordering; UI-facing validation can be done via onchange if needed.
        for rec in self:
            if rec.fecha_fin <= rec.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for rec in self:
            if rec.cupo_ilimitado:
                continue
            if rec.cupo_min < 0 or rec.cupo_max < 0:
                raise ValidationError('Los valores de cupo no pueden ser negativos.')
            if rec.cupo_max and rec.cupo_min > rec.cupo_max:
                raise ValidationError('El cupo mínimo no puede ser mayor al cupo máximo.')

    # ──────────────────────────────────────────────
    # Acciones de estado
    # ──────────────────────────────────────────────
    def action_enviar_catalogo(self):
        self.ensure_one()
        self.write({'estado_actividad': 'pendiente_inicio'})
        self.message_post(body='Actividad enviada al catálogo. Estado: Pendiente de Inicio.')

    def action_iniciar_actividad(self):
        self.ensure_one()
        self.write({'estado_actividad': 'en_curso'})
        self.message_post(body='La actividad ha iniciado. Estado: En Curso.')

    def action_finalizar_actividad(self):
        self.ensure_one()
        self.write({'estado_actividad': 'finalizada'})
        self.message_post(body='La actividad ha finalizado.')
        self._generar_constancias()

    def _generar_constancias(self):
        """Genera constancias para todos los estudiantes con nivel de desempeño asignado."""
        Expediente = self.env['creditos.expediente.estudiante']
        Constancia = self.env['creditos.constancia']
        for estudiante_line in self.lista_estudiante_ids:
            if estudiante_line.nivel_desempeno and not estudiante_line.constancia_id:
                expediente = Expediente.search(
                    [('estudiante_id', '=', estudiante_line.estudiante_id.id)], limit=1
                )
                if not expediente:
                    expediente = Expediente.create(
                        {'estudiante_id': estudiante_line.estudiante_id.id}
                    )
                constancia = Constancia.create({
                    'expediente_id': expediente.id,
                    'actividad_id': self.id,
                    'estudiante_id': estudiante_line.estudiante_id.id,
                })
                estudiante_line.constancia_id = constancia.id

    def action_firmar_constancias(self):
        """El Jefe de Departamento firma todas las constancias de la actividad."""
        self.ensure_one()
        constancias_pendientes = self.constancia_ids.filtered(
            lambda c: not c.firma_jefe_depto
        )
        if not constancias_pendientes:
            raise ValidationError('No hay constancias pendientes de firma del Jefe de Departamento.')
        firma = self.env['creditos.firma.electronica'].search(
            [('empleado_id', '=', self.jefe_departamento_id.id)], limit=1
        )
        if not firma:
            raise ValidationError(
                'El Jefe de Departamento no tiene firma electrónica registrada.'
            )
        constancias_pendientes.write({
            'firma_jefe_depto': firma.firma_electronica,
            'estado_constancia': 'firmada_jefe',
        })
        self.message_post(
            body=(
                'Constancias firmadas por el Jefe de Departamento. '
                'Pendientes de firma del Responsable de Actividad.'
            )
        )

    @api.model
    def _cron_actualizar_estados(self):
        """
        Cron diario:
        - pendiente_inicio → en_curso cuando fecha_inicio <= hoy
        - en_curso → finalizada cuando fecha_fin < hoy
        """
        hoy = fields.Date.today()
        pendientes = self.search([
            ('estado_actividad', '=', 'pendiente_inicio'),
            ('fecha_inicio', '<=', hoy),
        ])
        pendientes.write({'estado_actividad': 'en_curso'})
        for act in pendientes:
            act.message_post(body='Estado actualizado automáticamente a: En Curso.')
        en_curso = self.search([
            ('estado_actividad', '=', 'en_curso'),
            ('fecha_fin', '<', hoy),
        ])
        for act in en_curso:
            act.action_finalizar_actividad()

    def action_difundir_actividad(self):
        """Abre wizard para seleccionar estudiantes a notificar."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Difundir Actividad Complementaria',
            'res_model': 'creditos.wizard.difusion',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_actividad_id': self.id},
        }
