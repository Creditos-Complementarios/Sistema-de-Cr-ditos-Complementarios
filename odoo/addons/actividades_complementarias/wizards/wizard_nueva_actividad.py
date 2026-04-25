# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def _n_dias_habiles(n, desde=None):
    """Avanza *n* días hábiles (lunes a viernes) desde *desde* (default: hoy)."""
    base = desde if desde is not None else date.today()
    contados = 0
    candidato = base
    while contados < n:
        candidato += timedelta(days=1)
        if candidato.weekday() < 5:   # 0=lun … 4=vie
            contados += 1
    return candidato


class WizardNuevaActividad(models.TransientModel):
    """
    Wizard JD-01SC: Solicitud de nuevo tipo de actividad complementaria.
    Guía al JD para registrar una actividad y decide automáticamente
    si se envía al catálogo (predefinida) o al Comité Académico (nueva).
    """
    _name = 'actividad.wizard.nueva'
    _description = 'Wizard: Generar Actividad Complementaria'

    # ── Datos obligatorios ────────────────────────────────────────────────
    name = fields.Char(
        string='Nombre de la Actividad',
        required=True,
        size=200,
    )
    descripcion = fields.Text(
        string='Descripción',
        size=2000,
    )
    tipo_actividad_id = fields.Many2one(
        comodel_name='actividad.tipo',
        string='Tipo de Actividad',
        required=True,
    )
    periodo = fields.Many2one(
        comodel_name='sii.periodo',
        string='Periodo Escolar',
        required=True,
    )
    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        required=True,
    )
    fecha_fin = fields.Date(
        string='Fecha de Finalización',
        required=True,
    )
    cantidad_horas = fields.Float(
        string='Cantidad de Horas',
        required=True,
    )
    horario = fields.Text(
        string='Horario por Día (si aplica)',
    )
    cupo_ilimitado = fields.Boolean(
        string='Cupo Ilimitado',
        default=False,
    )
    cupo_min = fields.Integer(
        string='Cupo Mínimo',
        default=1,
    )
    cupo_max = fields.Integer(
        string='Cupo Máximo',
        default=30,
    )
    ruta_imagen = fields.Image(
        string='Imagen Alusiva',
        max_width=1024,
        max_height=1024,
    )

    # ── Datos condicionales (solo si predefinida) ─────────────────────────
    es_predefinida = fields.Boolean(
        string='Tipo Predefinido',
        compute='_compute_es_predefinida',
        store=False,
    )
    actividad_predefinida = fields.Many2one(
        comodel_name='actividad.tipo.predefinida',
        string='Actividades Predefinidas',
        ondelete='set null',
        help=(
            'Seleccione si la actividad corresponde a un tipo predefinido '
            '(incluyendo las aprobadas por el Comité Académico). Al '
            'seleccionarla, el Tipo de Actividad se completará automáticamente.'
        ),
    )
    responsable_actividad_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsable de Actividad',
    )
    creditos = fields.Selection(
        selection=[
            ('0.5', '0.5 créditos'),
            ('1.0', '1 crédito'),
            ('1.5', '1.5 créditos'),
            ('2.0', '2 créditos'),
        ],
        string='Cantidad de Créditos',
    )

    # ────────────────────────────────────────────────────────────────────────
    # API Methods
    # ────────────────────────────────────────────────────────────────────────
    @api.depends('tipo_actividad_id', 'actividad_predefinida')
    def _compute_es_predefinida(self):
        for wizard in self:
            wizard.es_predefinida = (
                bool(wizard.actividad_predefinida) or
                (wizard.tipo_actividad_id.es_predefinida if wizard.tipo_actividad_id else False)
            )

    @api.onchange('actividad_predefinida')
    def _onchange_actividad_predefinida(self):
        """Al seleccionar un predefinido, autocompleta el Tipo de Actividad.
        Si el predefinido fue aprobado por Comité, también rellena el nombre."""
        if self.actividad_predefinida:
            if self.actividad_predefinida.tipo_actividad_id:
                self.tipo_actividad_id = self.actividad_predefinida.tipo_actividad_id
            if self.actividad_predefinida.is_comite:
                self.name = self.actividad_predefinida.name

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────
    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for wizard in self:
            if not self.env.context.get('install_demo') and not self.env.context.get('skip_fecha_check'):
                if wizard.fecha_inicio:
                    min_fecha = _n_dias_habiles(5)
                    if wizard.fecha_inicio < min_fecha:
                        raise ValidationError(
                            f'La fecha de inicio debe ser al menos 5 días hábiles '
                            f'a partir de hoy. La fecha mínima válida es '
                            f'{min_fecha.strftime("%d/%m/%Y")}.'
                        )
                if wizard.fecha_inicio and wizard.fecha_inicio < date.today():
                    raise ValidationError(
                        'La fecha de inicio no puede ser anterior a hoy.'
                    )
            if wizard.fecha_fin and wizard.fecha_inicio and wizard.fecha_fin <= wizard.fecha_inicio:
                raise ValidationError(
                    'La fecha de fin debe ser posterior a la fecha de inicio.'
                )

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for wizard in self:
            if not wizard.cupo_ilimitado:
                if wizard.cupo_min < 1:
                    raise ValidationError('El cupo mínimo debe ser al menos 1.')
                if wizard.cupo_max < wizard.cupo_min:
                    raise ValidationError(
                        'El cupo máximo debe ser mayor o igual al cupo mínimo.'
                    )

    # ────────────────────────────────────────────────────────────────────────
    # Business Actions
    # ────────────────────────────────────────────────────────────────────────
    def action_confirmar(self):
        """
        Valida todos los campos, luego crea la actividad y la enruta:
        - Predefinida -> estado 'pendiente_inicio' (sin comite).
        - Nueva -> estado 'en_revision', se crea propuesta al Comite.
        """
        self.ensure_one()
        self._validate_all_fields()
        es_predefinida = self._is_predefinida()
        estado = self._get_estado_inicial(es_predefinida)
        vals = self._prepare_activity_vals(estado, es_predefinida)
        actividad = self._create_activity(vals)
        
        if not es_predefinida:
            self._create_propuesta(actividad)
        
        self._post_activity_message(actividad, es_predefinida)
        return self._get_action_response(actividad, es_predefinida)

    def action_cancelar(self):
        return {'type': 'ir.actions.act_window_close'}

    # ────────────────────────────────────────────────────────────────────────
    # Helper Methods (privadas)
    # ────────────────────────────────────────────────────────────────────────
    def _validate_all_fields(self):
        """Valida todos los campos comunes y específicos según el tipo."""
        errores = []

        # Validaciones comunes
        self._validate_common_fields(errores)
        
        # Validaciones específicas
        if self._is_predefinida():
            self._validate_predefinida_fields(errores)
        else:
            self._validate_comite_fields(errores)

        if errores:
            raise ValidationError(
                'Por favor corrija los siguientes campos antes de continuar:\n\n' +
                '\n'.join(errores)
            )

    def _validate_common_fields(self, errores):
        """Valida campos comunes a todos los tipos de actividad."""
        if not self.name or not self.name.strip():
            errores.append('• Nombre de la Actividad es obligatorio.')
        if not self.tipo_actividad_id:
            errores.append('• Tipo de Actividad es obligatorio.')
        if not self.periodo:
            errores.append('• Periodo Escolar es obligatorio.')
        if not self.fecha_inicio:
            errores.append('• Fecha de Inicio es obligatoria.')
        if not self.fecha_fin:
            errores.append('• Fecha de Finalización es obligatoria.')
        
        self._validate_fechas_y_horas(errores)
        
        if not self.cantidad_horas or self.cantidad_horas <= 0:
            errores.append('• La Cantidad de Horas debe ser mayor a 0.')
        
        if not self.cupo_ilimitado:
            if self.cupo_min < 1:
                errores.append('• El Cupo Mínimo debe ser al menos 1.')
            if self.cupo_max < self.cupo_min:
                errores.append('• El Cupo Máximo debe ser mayor o igual al Cupo Mínimo.')

    def _validate_fechas_y_horas(self, errores):
        """Valida relaciones entre fechas y horas."""
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                errores.append(
                    '• La Fecha de Finalización debe ser posterior a la Fecha de Inicio.'
                )
            if not self.env.context.get('install_demo') and self.fecha_inicio < date.today():
                errores.append('• La Fecha de Inicio no puede ser anterior a hoy.')
            
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            horas_max = dias * 12
            if self.cantidad_horas and self.cantidad_horas > horas_max:
                errores.append(
                    f'• La Cantidad de Horas ({self.cantidad_horas} h) supera el máximo '
                    f'para el periodo seleccionado ({dias} día(s) x 12 h = {horas_max} h máximos).'
                )

    def _validate_predefinida_fields(self, errores):
        """Valida campos específicos para actividades predefinidas."""
        if not self.creditos:
            errores.append('• Cantidad de Créditos es obligatoria para enviar al Catálogo.')
        if not self.responsable_actividad_id:
            errores.append('• Responsable de Actividad es obligatorio para enviar al Catálogo.')

    def _validate_comite_fields(self, errores):
        """Valida campos específicos para envío al Comité."""
        if not self.creditos:
            errores.append(
                '• Cantidad de Créditos es obligatoria para enviar al Comité Académico.'
            )

    def _is_predefinida(self):
        """Determina si la actividad es de tipo predefinida."""
        return (
            bool(self.actividad_predefinida) or
            (self.tipo_actividad_id.es_predefinida if self.tipo_actividad_id else False)
        )

    def _get_estado_inicial(self, es_predefinida):
        """Obtiene el estado inicial según el tipo de actividad."""
        if es_predefinida:
            return self.env.ref('actividades_complementarias.estado_pendiente_inicio')
        return self.env.ref('actividades_complementarias.estado_en_revision')

    def _prepare_activity_vals(self, estado, es_predefinida):
        """Prepara el diccionario de valores para crear la actividad."""
        vals = {
            'name': self.name,
            'descripcion': self.descripcion,
            'tipo_actividad_id': self.tipo_actividad_id.id,
            'periodo': self.periodo.id,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'cantidad_horas': self.cantidad_horas,
            'horario': self.horario,
            'cupo_ilimitado': self.cupo_ilimitado,
            'cupo_min': self.cupo_min,
            'cupo_max': self.cupo_max,
            'ruta_imagen': self.ruta_imagen,
            'jefe_departamento_id': self.env.user.id,
            'estado_id': estado.id,
            'responsable_actividad_id': (
                self.responsable_actividad_id.id if self.responsable_actividad_id else False
            ),
            'creditos': self.creditos,
        }

        if es_predefinida:
            vals['en_catalogo'] = False

        return vals

    def _create_activity(self, vals):
        """Crea la actividad complementaria con contexto especial."""
        return self.env['actividad.complementaria'].with_context(
            skip_fecha_check=True,
            skip_horas_check=True,
            bypass_edit_protection=True,
        ).create(vals)

    def _create_propuesta(self, actividad):
        """Crea una propuesta para el Comité Académico."""
        estado_revision = self.env.ref('actividades_complementarias.estado_solicitud_en_revision')
        self.env['actividad.propuesta'].sudo().create({
            'actividad_id': actividad.id,
            'estado_solicitud_id': estado_revision.id,
        })

    def _post_activity_message(self, actividad, es_predefinida):
        """Publica mensaje en el chatter según el tipo de actividad."""
        if not es_predefinida:
            actividad.message_post(
                body=(
                    'Propuesta enviada al Comité Académico para su revisión. '
                    'Se aprobará automáticamente si no hay respuesta en 5 días.'
                )
            )
        else:
            tipo_label = (
                self.actividad_predefinida.name if self.actividad_predefinida
                else self.tipo_actividad_id.name
            )
            actividad.message_post(
                body=(
                    f'Actividad predefinida ({tipo_label}) registrada y aprobada '
                    f'automáticamente. Lista para enviar al catálogo.'
                )
            )

    def _get_action_response(self, actividad, es_predefinida):
        """Retorna la acción de redirección apropiada."""
        if not es_predefinida:
            action = self.env.ref(
                'actividades_complementarias.action_propuesta',
                raise_if_not_found=False,
            )
            if action:
                result = action.sudo().read()[0]
                result['target'] = 'current'
                return result
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'actividad.complementaria',
            'res_id': actividad.id,
            'view_mode': 'form',
            'target': 'current',
        }