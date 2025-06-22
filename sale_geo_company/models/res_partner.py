from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para manejar partners creados desde el website"""
        partners = super().create(vals_list)
        
        for partner in partners:
            # Verificar si el partner fue creado desde el website
            if self._is_website_partner(partner):
                self._configure_partner_for_multicompany(partner)
                
        return partners

    def write(self, vals):
        """Override write para detectar cambios de ubicación y reasignar compañía en órdenes"""
        result = super().write(vals)
        
        # Verificar si se actualizaron datos de ubicación
        location_fields = ['country_id', 'state_id', 'city']
        if any(field in vals for field in location_fields):
            self._check_geographic_reassignment()
                
        return result

    def _check_geographic_reassignment(self):
        """Verificar si hay órdenes de venta que necesiten reasignación geográfica"""
        
        for partner in self:
            # Buscar órdenes de venta activas de este partner
            orders = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['draft', 'sent'])  # Solo órdenes no confirmadas
            ])
            
            for order in orders:
                try:
                    # Intentar reasignar compañía basada en nueva ubicación
                    company = order._get_geographic_company()
                    if company and company != order.company_id:
                        _logger.info(f"=== Reasignando orden {order.name} de {order.company_id.name} a {company.name} por cambio en partner {partner.name}")
                        
                        order.sudo().write({'company_id': company.id})
                        order._ensure_partner_company_compatibility(company)
                        
                        order.message_post(
                            body=f"Compañía reasignada automáticamente a {company.name} por actualización de ubicación del cliente"
                        )
                        
                except Exception as e:
                    _logger.error(f"=== Error reasignando orden {order.name}: {e}")

    def _is_website_partner(self, partner):
        """Determinar si un partner fue creado desde el website"""
        # Indicadores de que es un partner del website:
        # 1. Es un contacto (no es una compañía)
        # 2. Tiene email
        # 3. No tiene usuario asociado inicialmente
        # 4. Viene del contexto web
        
        is_website_context = 'website_id' in self.env.context or \
                           'from_website' in self.env.context or \
                           self.env.context.get('website_sale_order')
        
        is_contact = not partner.is_company and partner.email
        
        _logger.info(f"=== Evaluando partner '{partner.name}': website_context={is_website_context}, is_contact={is_contact}")
        
        return is_website_context and is_contact

    def _configure_partner_for_multicompany(self, partner):
        """Configurar partner para compatibilidad multicompañía"""
        try:
            # Configurar partner sin restricción de compañía específica
            partner.sudo().write({
                'company_id': False  # Sin restricción de compañía
            })
            
            _logger.info(f"=== Partner '{partner.name}' configurado para multicompañía (sin restricción de compañía)")
            
            # Si más tarde se crea un usuario para este partner, también lo configuramos
            self._setup_future_user_for_partner(partner)
            
        except Exception as e:
            _logger.error(f"=== Error configurando partner multicompañía {partner.name}: {e}")

    def _setup_future_user_for_partner(self, partner):
        """Configurar para que cuando se cree un usuario para este partner, tenga acceso a todas las compañías"""
        # Esto se manejará en el modelo res.users cuando se cree el usuario
        # Pero podemos marcar el partner de alguna manera
        pass

    def ensure_multicompany_compatibility(self):
        """Método manual para asegurar compatibilidad multicompañía de partners existentes"""
        self.ensure_one()
        
        if not self.is_company:  # Solo para contactos, no para compañías
            self.sudo().write({'company_id': False})
            
            # Si tiene usuario asociado, también configurarlo
            if self.user_ids:
                for user in self.user_ids:
                    user_model = self.env['res.users'].browse(user.id)
                    user_model._assign_all_companies_to_user(user)
            
            _logger.info(f"=== Partner '{self.name}' configurado para multicompañía")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Partner {self.name} configurado para multicompañía',
                    'type': 'success',
                    'sticky': False,
                }
            }

    @api.model
    def fix_all_website_partners(self):
        """Método para corregir todos los partners del website"""
        # Buscar partners que parecen ser del website
        website_partners = self.search([
            ('is_company', '=', False),  # Solo contactos
            ('email', '!=', False),      # Que tengan email
            ('customer_rank', '>', 0),   # Que sean clientes
        ])
        
        fixed_count = 0
        for partner in website_partners:
            if partner.company_id:  # Solo si tienen restricción de compañía
                partner.sudo().write({'company_id': False})
                fixed_count += 1
                
                # También corregir usuarios asociados si existen
                for user in partner.user_ids:
                    user_model = self.env['res.users'].browse(user.id)
                    user_model._assign_all_companies_to_user(user)
        
        _logger.info(f"=== Corregidos {fixed_count} partners del website para multicompañía")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Se corrigieron {fixed_count} partners del website para multicompañía',
                'type': 'success',
                'sticky': True,
            }
        } 