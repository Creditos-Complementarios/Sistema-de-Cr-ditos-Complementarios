# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizardConfirmarEnvio(models.TransientModel):
    _name = 'actividad.wizard.confirmar.envio'
    _description = 'Confirmación de envío de actividad'

    actividad_id = fields.Many2one('actividad.complementaria', required=True)
    tipo_envio = fields.Selection([
        ('comite', 'Comité Académico'),
        ('catalogo', 'Catálogo'),
    ], required=True)
    resumen_html = fields.Html(compute='_compute_resumen_html', store=False, sanitize=False)

    @api.depends('actividad_id', 'tipo_envio')
    def _compute_resumen_html(self):
        creditos_labels = dict(self.env['actividad.complementaria']._fields['creditos'].selection)
        for rec in self:
            a = rec.actividad_id
            if not a:
                rec.resumen_html = ''
                continue

            # MODIFICADO RA-01SC Regla 5: si la actividad es de asignación directa,
            # el destino mostrado en el resumen es "Asignación Directa" en lugar de
            # "Catálogo", para que el usuario entienda que la actividad no se publicará
            # en el catálogo sino que quedará disponible para los alumnos asignados.
            if rec.tipo_envio == 'comite':
                destino = '<span style="color:#e67e22;font-weight:600;">Comité Académico</span>'
            elif a.tipo_inscripcion == 'asignacion':
                destino = '<span style="color:#8e44ad;font-weight:600;">Asignación Directa (sin catálogo)</span>'
            else:
                destino = '<span style="color:#17a589;font-weight:600;">Catálogo</span>'

            def row(label, value):
                return (
                    f'<tr>'
                    f'<td style="padding:5px 14px;font-weight:600;'
                    f'color:#555;white-space:nowrap;width:220px;">{label}</td>'
                    f'<td style="padding:5px 14px;color:#222;">'
                    f'{value or "—"}</td>'
                    f'</tr>'
                )

            cupo = 'Ilimitado' if a.cupo_ilimitado else f'Mínimo: {a.cupo_min} | Máximo: {a.cupo_max}'

            rows = ''.join([
                row('Nombre', a.name),
                row('Tipo de Actividad', a.tipo_actividad_id.name if a.tipo_actividad_id else ''),
                row('Periodo Escolar', a.periodo.clave_periodo if a.periodo else ''),
                row('Jefe de Departamento', a.jefe_departamento_id.name if a.jefe_departamento_id else ''),
                row('Responsable', a.responsable_actividad_id.name if a.responsable_actividad_id else ''),
                row('Créditos', creditos_labels.get(a.creditos, '') if a.creditos else ''),
                row('Fecha de Inicio', a.fecha_inicio.strftime('%d/%m/%Y') if a.fecha_inicio else ''),
                row('Fecha de Finalización', a.fecha_fin.strftime('%d/%m/%Y') if a.fecha_fin else ''),
                row('Cantidad de Horas', f'{a.cantidad_horas:g} h' if a.cantidad_horas else ''),
                row('Cupos', cupo),
                row('Descripción', a.descripcion),
                # NUEVO RA-01SC Regla 5: mostrar el tipo de inscripción en el resumen
                # para que el usuario confirme conscientemente el canal de inscripción.
                row('Tipo de Inscripción', 'Asignación Directa' if a.tipo_inscripcion == 'asignacion' else 'Inscripción Abierta (Catálogo)'),
            ])

            div_style = (
                'background:#eaf4fb;border-left:4px solid #2980b9;'
                'padding:10px 16px;margin-bottom:12px;border-radius:4px;'
            )

            rec.resumen_html = f'''
<div style="font-family:sans-serif;">
    <div style="{div_style}">
        <strong>Destino:</strong> {destino}
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:13.5px;">
        <tbody>{rows}</tbody>
    </table>
</div>'''

    def action_confirmar(self):
        self.ensure_one()
        if self.tipo_envio == 'comite':
            return self.actividad_id.action_enviar_comite()

        # MODIFICADO RA-01SC Regla 5: si la actividad es de asignación directa,
        # se llama a action_confirmar_actividad() en lugar de action_enviar_catalogo().
        # Esto permite que el flujo de confirmación del wizard funcione correctamente
        # para ambos tipos de inscripción sin lanzar el error de validación.
        #
        # - 'asignacion': confirma la actividad (Pendiente de Inicio) sin publicarla.
        # - 'catalogo':   envía la actividad al catálogo público como antes.
        if self.actividad_id.tipo_inscripcion == 'asignacion':
            return self.actividad_id.action_confirmar_actividad()
        return self.actividad_id.action_enviar_catalogo()
