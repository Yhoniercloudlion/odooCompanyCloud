{
    'name': 'Asignación Geográfica de Compañías',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Asigna automáticamente compañías a usuarios basado en su ubicación geográfica',
    'description': """
        Este módulo permite:
        - Configurar compañías con sus ubicaciones geográficas
        - Asignar automáticamente la compañía más cercana al usuario
        - Sistema de prioridades para múltiples coincidencias
        - Reasignación automática al completar perfil en "Mi Cuenta"
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'depends': ['base', 'website'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'data/company_locations_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 