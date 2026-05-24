# -*- coding: utf-8 -*-
"""
DEP-C-01SC: Difusión de actividad complementaria.

Permite a la División de Estudios Profesionales y al Coordinador
seleccionar alumnos (por carrera, semestre, grupo o búsqueda individual)
y enviarles una notificación/invitación de Odoo a la actividad.

Reglas de negocio:
    - La actividad debe estar en estado 'pendiente_inicio'.
    - El botón de difusión está deshabilitado si el cupo ya está lleno.
    - Los filtros excluyen alumnos que ya tengan créditos completos.
"""
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardDifundirActividad(models.TransientModel):
    _name = 'actividad.wizard.difundir'
    _description = 'Difusión de Actividad — DEP/Coordinador'

    # ── Actividad origen ────────────────────────────────────────────────────────
    actividad_id = fields.Many2one(
        'actividad.complementaria',
        string='Actividad',
        required=True,
        readonly=True,
    )

    # ── Filtros de búsqueda de alumnos ─────────────────────────────────────────
    filtro_carrera_id = fields.Many2one(
        'sii.carrera',
        string='Carrera',
        help='Filtra la lista de alumnos por carrera.',
    )
    filtro_semestre = fields.Integer(
        string='Semestre',
        help='Filtra la lista de alumnos por semestre (0 = todos).',
    )
    filtro_grupo = fields.Char(
        string='Grupo',
        size=10,
        help='Filtra la lista de alumnos por grupo.',
    )
    filtro_busqueda = fields.Char(
        string='Buscar por nombre o N° control',
        help='Búsqueda libre: nombre, apellido o número de control.',
    )

    # ── Lista de alumnos seleccionados ─────────────────────────────────────────
    alumno_ids = fields.Many2many(
        'sii.estudiante',
        'wizard_difundir_alumno_rel',
        'wizard_id',
        'estudiante_id',
        string='Alumnos a invitar',
        help=(
            'Alumnos que recibirán la notificación de invitación. '
            'Aplicar los filtros y pulsar "Actualizar lista" para poblar este campo.'
        ),
    )

    # ── Información resumida ────────────────────────────────────────────────────
    info_html = fields.Html(
        string='Resumen de la actividad',
        compute='_compute_info_html',
        store=False,
        sanitize=False,
    )

    # ───────────────────────────────────────────────────────────────────────────
    # Defaults / onchange
    # ───────────────────────────────────────────────────────────────────────────

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        ctx = self.env.context
        actividad_id = ctx.get('default_actividad_id') or ctx.get('active_id')
        if actividad_id:
            vals['actividad_id'] = actividad_id
        return vals

    # ───────────────────────────────────────────────────────────────────────────
    # Computed
    # ───────────────────────────────────────────────────────────────────────────

    @api.depends('actividad_id')
    def _compute_info_html(self):
        for rec in self:
            a = rec.actividad_id
            if not a:
                rec.info_html = ''
                continue

            def row(label, value):
                return (
                    f'<tr>'
                    f'<td style="padding:4px 12px;font-weight:600;color:#555;'
                    f'white-space:nowrap;width:200px;">{label}</td>'
                    f'<td style="padding:4px 12px;color:#222;">{value or "—"}</td>'
                    f'</tr>'
                )

            cupo = (
                'Ilimitado' if a.cupo_ilimitado
                else f'Máx. {a.cupo_max} | Disponibles: {a.cupos_disponibles}'
            )
            field = a._fields['estado_code']
            estado_label = dict(
                field._description_selection(a.env)
            ).get(a.estado_code, '')
            rows = ''.join([
                row('Actividad', a.name),
                row('Tipo', a.tipo_actividad_id.name if a.tipo_actividad_id else ''),
                row('Estado', estado_label),
                row('Periodo', a.periodo.clave_periodo if a.periodo else ''),
                row('Cupo', cupo),
                row('Fecha inicio', a.fecha_inicio.strftime('%d/%m/%Y') if a.fecha_inicio else ''),
                row('Fecha fin', a.fecha_fin.strftime('%d/%m/%Y') if a.fecha_fin else ''),
            ])

            div_style = (
                'background:#eaf4fb;border-left:4px solid #2980b9;'
                'padding:10px 16px;margin-bottom:10px;border-radius:4px;'
            )
            rec.info_html = f'''
<div style="font-family:sans-serif;">
    <div style="{div_style}">
        <strong>Vista previa de la invitación que recibirán los alumnos.</strong>
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tbody>{rows}</tbody>
    </table>
</div>'''

    # ───────────────────────────────────────────────────────────────────────────
    # Acciones del wizard
    # ───────────────────────────────────────────────────────────────────────────

    def action_actualizar_lista(self):
        """Recalcula alumno_ids aplicando los filtros configurados.

        Se excluyen alumnos cuyo estado_liberacion indique créditos completos,
        tal como exige la regla de negocio DEP-C-01SC §3.
        """
        self.ensure_one()

        domain = []

        if self.filtro_carrera_id:
            domain.append(('id_carrera', '=', self.filtro_carrera_id.id))
        if self.filtro_semestre and self.filtro_semestre > 0:
            domain.append(('semestre', '=', self.filtro_semestre))
        if self.filtro_grupo:
            domain.append(('grupo', 'ilike', self.filtro_grupo.strip()))
        if self.filtro_busqueda:
            q = self.filtro_busqueda.strip()
            domain.append('|')
            domain.append(('no_control', 'ilike', q))
            domain.append('|')
            domain.append(('nombre', 'ilike', q))
            domain.append('|')
            domain.append(('apellido_paterno', 'ilike', q))
            domain.append(('apellido_materno', 'ilike', q))

        # Excluir alumnos con créditos completos (estado_liberacion = 'liberado')
        domain.append(('estado_liberacion', 'not in', ['liberado', 'Liberado', 'LIBERADO']))

        alumnos = self.env['sii.estudiante'].search(domain)
        self.alumno_ids = [(6, 0, alumnos.ids)]

        # Devolver el mismo wizard abierto para que el usuario vea los resultados
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'actividad.wizard.difundir',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_difundir(self):
        """Envía una notificación interna de Odoo a cada alumno seleccionado.

        DEP-C-01SC paso 1.7: invitar a la actividad a los alumnos elegidos.

        Validaciones:
            - La actividad debe estar en 'pendiente_inicio'.
            - Debe haber cupo disponible (o ser ilimitado).
            - Debe haberse seleccionado al menos un alumno.
        """
        self.ensure_one()
        a = self.actividad_id

        # Validación 1: estado
        if a.estado_code != 'pendiente_inicio':
            raise ValidationError(
                'Solo se pueden difundir actividades en estado "Pendiente de Inicio".'
            )

        # Validación 2: cupo
        if not a.cupo_ilimitado and a.cupos_disponibles <= 0:
            raise ValidationError(
                f'La actividad "{a.name}" no tiene cupos disponibles. '
                'No se puede difundir.'
            )

        # Validación 3: alumnos seleccionados
        if not self.alumno_ids:
            raise ValidationError(
                'Seleccione al menos un alumno antes de difundir.'
            )

        # Construir cuerpo del mensaje
        cupo_txt = (
            'Cupo ilimitado' if a.cupo_ilimitado
            else f'{a.cupos_disponibles} lugar(es) disponible(s)'
        )
        fecha_inicio = (
            a.fecha_inicio.strftime('%d/%m/%Y') if a.fecha_inicio else '—'
        )
        cuerpo = (
            f'<p>Estimado alumno,</p>'
            f'<p>Te invitamos a participar en la siguiente actividad complementaria:</p>'
            f'<ul>'
            f'<li><strong>Actividad:</strong> {a.name}</li>'
            f'<li><strong>Tipo:</strong> {a.tipo_actividad_id.name if a.tipo_actividad_id else "—"}</li>'
            f'<li><strong>Fecha de inicio:</strong> {fecha_inicio}</li>'
            f'<li><strong>Cupo:</strong> {cupo_txt}</li>'
            f'</ul>'
            f'<p>Accede al catálogo de actividades complementarias para inscribirte.</p>'
        )

        # Enviar la notificación a cada alumno que tenga cuenta en Odoo
        enviados = 0
        sin_cuenta = []
        for estudiante in self.alumno_ids:
            usuario = self.env['res.users'].sudo().search(
                [('login', '=', estudiante.correo)], limit=1
            )
            if not usuario:
                sin_cuenta.append(
                    f'{estudiante.nombre} {estudiante.apellido_paterno} '
                    f'({estudiante.no_control})'
                )
                continue

            # Mensaje tipo mail.message en el chatter de la actividad
            # con partner_ids del alumno → genera notificación interna
            a.sudo().message_post(
                body=cuerpo,
                subtype_xmlid='mail.mt_comment',
                partner_ids=usuario.partner_id.ids,
                author_id=self.env.user.partner_id.id,
                message_type='comment',
            )
            enviados += 1

        # Registrar la difusión en el chatter de la actividad
        resumen_difusion = (
            f'<p><strong>Difusión registrada por {self.env.user.name}</strong></p>'
            f'<p>Se enviaron invitaciones a <strong>{enviados}</strong> alumno(s).</p>'
        )
        if sin_cuenta:
            lista_sc = ', '.join(sin_cuenta[:10])
            if len(sin_cuenta) > 10:
                lista_sc += f' … y {len(sin_cuenta) - 10} más'
            resumen_difusion += (
                f'<p style="color:#e67e22;">'
                f'Alumnos sin cuenta en el sistema (no notificados): {lista_sc}.'
                f'</p>'
            )

        a.sudo().message_post(
            body=resumen_difusion,
            subtype_xmlid='mail.mt_note',
            author_id=self.env.user.partner_id.id,
        )

        return {'type': 'ir.actions.act_window_close'}
