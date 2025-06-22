{
    'name': 'Asignación Geográfica de Compañías',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Asigna automáticamente compañías a usuarios y ventas basado en ubicación geográfica',
    'description': """
        Este módulo permite:
        - Asignar automáticamente la compañía más adecuada a las órdenes de venta basado en la ubicación del cliente
        - Sistema de prioridades para múltiples coincidencias geográficas
        - Configuración de áreas de servicio por compañía (países, estados, ciudades)
        - Asignación automática usando datos de envío del checkout del website
        
        Flujo de trabajo:
        1. Usuario se registra en website → se asigna a compañía del website (permanente)
        2. Usuario actualiza su dirección → mantiene la misma compañía
        3. Orden de venta se crea → se asigna automáticamente la compañía más cercana al cliente
        4. En checkout del website → asigna compañía basado en dirección de envío existente
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'website',
        'website_sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/res_users_views.xml',
        'data/manual_data_load.xml',
        'data/user_access.xml',
    ],
    'demo': [
        'data/demo_companies.xml',
        'data/demo_partners.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 