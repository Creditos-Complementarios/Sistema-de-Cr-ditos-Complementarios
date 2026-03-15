# -*- coding: utf-8 -*-
from odoo import models, fields


class CatalogoDepartamentos(models.Model):
    _name = 'creditos.catalogo.departamentos'
    _description = 'Catálogo de Departamentos'
    _rec_name = 'nombre_departamento'

    nombre_departamento = fields.Char(
        string='Nombre del Departamento',
        required=True,
    )
    active = fields.Boolean(default=True)

    # FIXED: hr.employee.department_id is a Many2one pointing to hr.department,
    # NOT to this custom model. Linking One2many here would crash at install.
    # Removed the invalid empleado_ids field.
    actividad_ids = fields.One2many(
        'creditos.actividad.complementaria',
        'departamento_id',
        string='Actividades Complementarias',
    )
