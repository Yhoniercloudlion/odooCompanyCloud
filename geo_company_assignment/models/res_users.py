from odoo import models, fields, api
from odoo.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        """
        Sobrescribir el método signup para asignar automáticamente la compañía
        basada en la ubicación geográfica del usuario y asignar grupo portal
        """
        # Asignar grupo portal por defecto
        values['groups_id'] = [(6, 0, [self.env.ref('base.group_portal').id])]
        
        # Ejecutar el signup original
        result = super(ResUsers, self).signup(values, token)
        
        # Obtener el usuario recién creado
        if result:
            user = self.browse(result)
            
            # Extraer información de ubicación de los valores
            country_id = values.get('country_id')
            state_id = values.get('state_id')
            city = values.get('city')
            
            if country_id:
                # Buscar la compañía más adecuada
                company = self.env['res.company'].find_company_by_location(
                    country_id=country_id,
                    state_id=state_id,
                    city=city
                )
                
                if company and company != user.company_id:
                    # Asignar la nueva compañía al usuario
                    user.write({
                        'company_id': company.id,
                        'company_ids': [(4, company.id)]
                    })
                    
                    # También actualizar el partner asociado
                    if user.partner_id:
                        user.partner_id.write({
                            'company_id': company.id
                        })
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescribir create para asignación automática durante creación programática
        """
        # Asignar grupo portal por defecto a todos los usuarios nuevos
        for vals in vals_list:
            if request and request.httprequest.path.startswith('/web/signup'):
                vals['groups_id'] = [(6, 0, [self.env.ref('base.group_portal').id])]
            
        users = super(ResUsers, self).create(vals_list)
        
        for user, vals in zip(users, vals_list):
            country_id = vals.get('country_id')
            state_id = vals.get('state_id') 
            city = vals.get('city')
            
            # Solo asignar si viene del website
            if country_id and request and request.httprequest.path.startswith('/web/signup'):
                company = self.env['res.company'].find_company_by_location(
                    country_id=country_id,
                    state_id=state_id,
                    city=city
                )
                
                if company and company != user.company_id:
                    user.write({
                        'company_id': company.id,
                        'company_ids': [(4, company.id)]
                    })
                    
                    if user.partner_id:
                        user.partner_id.write({
                            'company_id': company.id
                        })
        
        return users 