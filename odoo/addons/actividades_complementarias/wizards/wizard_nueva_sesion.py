# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import pytz


class WizardNuevaSesion(models.TransientModel):
    """Wizard: genera una sesión de pase de lista para una fecha dada,
    pre-llenando automáticamente todos los estudiantes inscritos."""

    _name = 'actividad.wizard.nueva.sesion'
    _description = 'Wizard: Nueva Sesión de Pase de Lista'

    actividad_id = fields.Many2one(
        'actividad.complementaria',
        required=True,
        ondelete='cascade',
    )
    fecha = fields.Date(
        string='Fecha de la Sesión',
        required=True,
        default=fields.Date.today,
    )

    def _hoy_local(self):
        """Devuelve la fecha de HOY en la zona horaria del usuario (no UTC).
        Esto evita que a las 6 pm en México (UTC-6) el servidor ya cuente
        como 'mañana' porque su reloj interno está en UTC."""
        tz_name = self.env.user.tz or 'America/Mexico_City'
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone('America/Mexico_City')
        return fields.Datetime.now().astimezone(tz).date()

    @api.constrains('fecha', 'actividad_id')
    def _check_fecha_rango(self):
        for rec in self:
            a = rec.actividad_id
            if a.fecha_inicio and rec.fecha < a.fecha_inicio:
                raise ValidationError(
                    _('La fecha de la sesión no puede ser anterior a la fecha de inicio '
                      'de la actividad (%s).') % a.fecha_inicio
                )
            if a.fecha_fin and rec.fecha > a.fecha_fin:
                raise ValidationError(
                    _('La fecha de la sesión no puede ser posterior a la fecha de fin '
                      'de la actividad (%s).') % a.fecha_fin
                )

    @api.constrains('fecha')
    def _check_fecha_no_anterior_a_hoy(self):
        """No se puede crear una sesión con fecha anterior a hoy (hora local del usuario).
        Esto corrige el desfase UTC: México es UTC-6, por lo que fields.Date.today()
        en el servidor puede devolver 'mañana' si son más de las 6 pm locales."""
        for rec in self:
            hoy_local = rec._hoy_local()
            if rec.fecha < hoy_local:
                raise ValidationError(
                    _('No se puede crear una sesión para una fecha pasada (%s). '
                      'Solo se permiten sesiones para hoy (%s) o fechas futuras.')
                    % (rec.fecha, hoy_local)
                )

    @api.constrains('fecha', 'actividad_id')
    def _check_no_sesion_duplicada(self):
        """No se puede crear una sesión si ya existe una con la misma fecha en la actividad."""
        Asistencia = self.env['actividad.asistencia']
        for rec in self:
            existe = Asistencia.search_count([
                ('actividad_id', '=', rec.actividad_id.id),
                ('fecha', '=', rec.fecha),
            ])
            if existe:
                raise ValidationError(
                    _('Ya existe una sesión registrada para el %s en esta actividad. '
                      'No se pueden crear sesiones duplicadas.')
                    % rec.fecha
                )

    def action_generar(self):
        """Crea registros de asistencia para todos los inscritos en la fecha dada.
        Ignora duplicados (mismo alumno, misma fecha)."""
        self.ensure_one()
        Asistencia = self.env['actividad.asistencia']
        creados = 0
        for inscripcion in self.actividad_id.inscripcion_ids:
            existe = Asistencia.search_count([
                ('actividad_id', '=', self.actividad_id.id),
                ('inscripcion_id', '=', inscripcion.id),
                ('fecha', '=', self.fecha),
            ])
            if not existe:
                Asistencia.create({
                    'actividad_id': self.actividad_id.id,
                    'inscripcion_id': inscripcion.id,
                    'fecha': self.fecha,
                    'presente': False,
                })
                creados += 1

        # Abrir la vista de pase de lista filtrada por esta actividad
        return self.actividad_id.action_abrir_pase_lista()
