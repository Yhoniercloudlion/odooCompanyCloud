from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para asignar automáticamente todas las compañías a usuarios nuevos"""
        users = super().create(vals_list)
        
        for user in users:
            # Solo aplicar para usuarios portal (del website) y usuarios internos nuevos
            if user.share or not user.share:  # Aplicar a todos los usuarios nuevos
                self._assign_all_companies_to_user(user)
                
        return users

    def _assign_all_companies_to_user(self, user):
        """Asignar todas las compañías activas al usuario"""
        try:
            # Obtener todas las compañías activas
            all_companies = self.env['res.company'].sudo().search([('active', '=', True)])
            
            if all_companies:
                # Asignar todas las compañías al usuario
                user.sudo().write({
                    'company_ids': [(6, 0, all_companies.ids)],
                    'company_id': all_companies[0].id  # Compañía principal (primera)
                })
                
                _logger.info(f"=== Usuario '{user.name}' ({user.login}) asignado a {len(all_companies)} compañías: {', '.join(all_companies.mapped('name'))}")
                
                # También asignar todas las compañías al partner relacionado
                if user.partner_id:
                    # Para el partner, usar False para que no tenga restricción de compañía
                    user.partner_id.sudo().write({
                        'company_id': False  # Sin restricción de compañía específica
                    })
                    _logger.info(f"=== Partner '{user.partner_id.name}' configurado sin restricción de compañía")
                    
        except Exception as e:
            _logger.error(f"=== Error asignando compañías al usuario {user.name}: {e}")

    def assign_all_companies(self):
        """Método manual para asignar todas las compañías a un usuario existente"""
        self.ensure_one()
        self._assign_all_companies_to_user(self)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Usuario {self.name} asignado a todas las compañías disponibles',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def fix_all_existing_users(self):
        """Método para corregir usuarios existentes que solo tienen My Company"""
        users_to_fix = self.search([
            ('active', '=', True),
            ('share', '=', False)  # Solo usuarios internos
        ])
        
        fixed_count = 0
        for user in users_to_fix:
            # Verificar si el usuario solo tiene una compañía
            if len(user.company_ids) <= 1:
                self._assign_all_companies_to_user(user)
                fixed_count += 1
        
        _logger.info(f"=== Corregidos {fixed_count} usuarios existentes")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Se corrigieron {fixed_count} usuarios para tener acceso a todas las compañías',
                'type': 'success',
                'sticky': True,
            }
        } 