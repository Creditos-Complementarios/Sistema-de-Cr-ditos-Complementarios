# -*- coding: utf-8 -*-
{
    'name': 'Sistema de Créditos Complementarios',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Gestión de actividades complementarias para créditos estudiantiles',
    'description': """
        Módulo para la gestión integral de actividades complementarias:
        - Solicitud y registro de nuevas actividades complementarias (JD-01SC)
        - Gestión del ciclo de vida de actividades complementarias (JD-02SC)
        - Control de propuestas al Comité Académico
        - Asignación de responsables y estudiantes
        - Generación y firma de constancias digitales
    """,
    'author': 'Desarrollo Institucional',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'portal',
        'hr',
    ],
    'data': [
        # Security
        'security/gestion_creditos_complementarios_groups.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        # Data
        'data/gestion_creditos_complementarios_data.xml',
        # Views
        'views/catalogo_departamentos_views.xml',
        'views/tipo_actividad_views.xml',
        'views/periodo_views.xml',
        'views/actividad_form_views.xml',
        'views/actividad_list_views.xml',
        'views/actividad_search_views.xml',
        'views/propuesta_actividad_views.xml',
        'views/expediente_estudiante_views.xml',
        'views/constancia_views.xml',
        'wizard/wizard_difusion_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
