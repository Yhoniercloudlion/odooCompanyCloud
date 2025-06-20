from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSignupGeoHome(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """
        Extender el controlador de registro para manejar ubicación geográfica
        """
        # Procesar datos de ubicación si existen
        if request.httprequest.method == 'POST':
            # Extraer datos geográficos del request
            country_id = kw.get('country_id')
            state_id = kw.get('state_id') 
            city = kw.get('city')
            
            # Agregar al contexto para uso posterior
            if country_id:
                kw.update({
                    'country_id': int(country_id) if country_id else False,
                    'state_id': int(state_id) if state_id else False,
                    'city': city or False,
                })
        
        # Llamar al método original
        response = super(AuthSignupGeoHome, self).web_auth_signup(*args, **kw)
        
        return response

    def _signup_with_values(self, token, values):
        """
        Sobrescribir para asignar compañía basada en ubicación
        """
        # Extraer datos de ubicación
        country_id = values.get('country_id')
        state_id = values.get('state_id')
        city = values.get('city')
        
        # Llamar al método original para crear el usuario
        result = super(AuthSignupGeoHome, self)._signup_with_values(token, values)
        
        # Si se creó el usuario y hay datos de ubicación, asignar compañía
        if result and country_id:
            try:
                # Buscar la compañía más adecuada
                company = request.env['res.company'].sudo().find_company_by_location(
                    country_id=country_id,
                    state_id=state_id,
                    city=city
                )
                
                if company:
                    # Obtener el usuario recién creado
                    user = request.env['res.users'].sudo().browse(result)
                    if user and company != user.company_id:
                        # Asignar la nueva compañía
                        user.write({
                            'company_id': company.id,
                            'company_ids': [(4, company.id)]
                        })
                        
                        # Actualizar el partner
                        if user.partner_id:
                            user.partner_id.write({
                                'company_id': company.id
                            })
            except Exception as e:
                # Log del error pero continuar con el registro
                request.env['ir.logging'].sudo().create({
                    'name': 'geo_company_assignment',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': f'Error asignando compañía geográfica: {str(e)}',
                    'path': 'geo_company_assignment',
                    'line': '1',
                    'func': '_signup_with_values'
                })
        
        return result 