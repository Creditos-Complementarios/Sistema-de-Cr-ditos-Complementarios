# -*- coding: utf-8 -*-
# Copyright 2025 Your Organization
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

"""
actividad_pase_lista_pivot.py
==============================
Modelo transitorio que genera la representación matricial del pase de lista:
    filas    → estudiantes inscritos
    columnas → fechas de sesión (dinámicas)

Usado por el template QWeb ``pase_lista_pivot_template`` para renderizar
una tabla HTML interactiva que permite marcar asistencia sin recargar la página.
"""

from odoo import fields, models


class ActividadPaseListaPivot(models.TransientModel):
    """Contexto de la vista pivot del pase de lista (transitorio)."""

    _name = "actividad.pase.lista.pivot"
    _description = "Pase de Lista – Vista Pivote"

    actividad_id = fields.Many2one(
        comodel_name="actividad.complementaria",
        string="Actividad",
        required=True,
        ondelete="cascade",
    )

    # ------------------------------------------------------------------
    # Método principal: devuelve la estructura para el template
    # ------------------------------------------------------------------

    def get_pivot_data(self, actividad_id):
        """
        Devuelve un dict con:
            - fechas  : lista de strings 'YYYY-MM-DD' ordenados ASC
            - filas   : lista de dicts por estudiante
                {
                  'partner_id': int,
                  'nombre':     str,
                  'celdas':     { 'YYYY-MM-DD': {'asistencia_id': int, 'presente': bool} }
                }
            - readonly: bool  (actividad finalizada o constancias generadas)
        """
        actividad = self.env["actividad.complementaria"].browse(actividad_id)
        if not actividad.exists():
            return {"fechas": [], "filas": [], "readonly": True}

        readonly = (
            actividad.estado_code == "finalizada"
            or actividad.certificates_generated
            or self.env.user.has_group(
                "actividades_complementarias.group_jefe_departamento"
            )
        )

        # 1. Todas las fechas únicas de sesión, ordenadas
        asistencias = self.env["actividad.asistencia"].search(
            [("actividad_id", "=", actividad_id)],
            order="fecha asc",
        )
        fechas = sorted({str(a.fecha) for a in asistencias})

        # 2. Agrupar registros por (inscripcion_id, fecha)
        mapa = {}
        for a in asistencias:
            key = (a.inscripcion_id.id, str(a.fecha))
            mapa[key] = {"asistencia_id": a.id, "presente": a.presente}

        # 3. Construir filas por estudiante inscrito (orden alfabético)
        filas = []
        for insc in actividad.inscripcion_ids.sorted(
            key=lambda i: i.partner_id.name or ""
        ):
            celdas = {}
            for f in fechas:
                celdas[f] = mapa.get(
                    (insc.id, f),
                    {"asistencia_id": False, "presente": False},
                )
            filas.append(
                {
                    "partner_id": insc.partner_id.id,
                    "nombre": insc.partner_id.name or "(Sin nombre)",
                    "celdas": celdas,
                }
            )

        return {"fechas": fechas, "filas": filas, "readonly": readonly}
