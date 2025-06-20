from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def assign_geographic_company(self):
        """
        Método para asignar geográficamente una compañía basada en la ubicación del contacto
        """
        for partner in self:
            if not partner.country_id:
                continue
                
            try:
                # Buscar la compañía más adecuada
                company = self.env['res.company'].sudo().find_company_by_location(
                    country_id=partner.country_id.id,
                    state_id=partner.state_id.id if partner.state_id else None,
                    city=partner.city
                )
                
                if company and company != partner.company_id:
                    # Si tiene usuario asociado, actualizar sus compañías primero
                    if partner.user_ids:
                        user = partner.user_ids[0]
                        current_companies = list(user.company_ids.ids)
                        
                        # Agregar la nueva compañía si no está
                        if company.id not in current_companies:
                            current_companies.append(company.id)
                        
                        # Actualizar usuario con sudo
                        user.sudo().write({
                            'company_ids': [(6, 0, current_companies)],
                            'company_id': company.id
                        })
                        
                        self.env['ir.logging'].sudo().create({
                            'name': 'geo_company_assignment',
                            'type': 'server',
                            'level': 'INFO',
                            'message': f'Usuario {user.name} actualizado: compañías {current_companies}, principal {company.id}',
                            'path': 'geo_company_assignment',
                            'line': '1',
                            'func': 'assign_geographic_company'
                        })
                    
                    # Actualizar el partner
                    partner.sudo().write({'company_id': company.id})
                    
                    self.env['ir.logging'].sudo().create({
                        'name': 'geo_company_assignment',
                        'type': 'server',
                        'level': 'INFO',
                        'message': f'✅ {partner.name} reasignado a {company.name} basado en {partner.country_id.name}, {partner.state_id.name if partner.state_id else ""}, {partner.city or ""}',
                        'path': 'geo_company_assignment',
                        'line': '1',
                        'func': 'assign_geographic_company'
                    })
                
            except Exception as e:
                self.env['ir.logging'].sudo().create({
                    'name': 'geo_company_assignment',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': f'❌ Error asignando geográficamente {partner.name}: {str(e)}',
                    'path': 'geo_company_assignment',
                    'line': '1',
                    'func': 'assign_geographic_company'
                })

    def write(self, vals):
        """
        Sobrescribir write para detectar cambios en ubicación y reasignar compañía
        """
        result = super(ResPartner, self).write(vals)
        
        # Verificar si se actualizaron campos de ubicación
        location_fields = ['country_id', 'state_id', 'city']
        location_updated = any(field in vals for field in location_fields)
        
        if location_updated:
            # Para cada partner que se actualizó
            for partner in self:
                # Solo procesar si tiene información de país
                if partner.country_id:
                    try:
                        # Buscar la compañía más adecuada
                        company = self.env['res.company'].find_company_by_location(
                            country_id=partner.country_id.id,
                            state_id=partner.state_id.id if partner.state_id else None,
                            city=partner.city
                        )
                        
                        # Si encontramos una compañía diferente, reasignar
                        if company and company != partner.company_id:
                            # PRIMERO: Si tiene usuario asociado, agregar la empresa a sus compañías permitidas
                            if partner.user_ids:
                                user = partner.user_ids[0]
                                current_companies = list(user.company_ids.ids)
                                if company.id not in current_companies:
                                    current_companies.append(company.id)
                                    # Actualizar las compañías del usuario ANTES de cambiar el partner
                                    user.sudo().write({
                                        'company_ids': [(6, 0, current_companies)]
                                    })
                                    
                                # Luego cambiar la compañía principal del usuario
                                user.sudo().write({
                                    'company_id': company.id
                                })
                                log_message = f'Usuario {user.name} reasignado a {company.name}'
                            else:
                                log_message = f'Contacto {partner.name} asignado a {company.name}'
                            
                            # SEGUNDO: Asignar compañía al contacto/partner
                            partner.sudo().write({
                                'company_id': company.id
                            })
                            
                            # Log del cambio
                            self.env['ir.logging'].sudo().create({
                                'name': 'geo_company_assignment',
                                'type': 'server',
                                'level': 'INFO',
                                'message': f'{log_message} y contacto {partner.name} basado en ubicación: {partner.country_id.name}, {partner.state_id.name if partner.state_id else ""}, {partner.city or ""}',
                                'path': 'geo_company_assignment',
                                'line': '1',
                                'func': 'write'
                            })
                            
                    except Exception as e:
                        # Log del error pero continuar
                        self.env['ir.logging'].sudo().create({
                            'name': 'geo_company_assignment',
                            'type': 'server',
                            'level': 'ERROR',
                            'message': f'Error reasignando compañía geográfica para {partner.name}: {str(e)}',
                            'path': 'geo_company_assignment',
                            'line': '1',
                            'func': 'write'
                        })
        
        return result 