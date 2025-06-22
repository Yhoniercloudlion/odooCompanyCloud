from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Campos para capturar datos de envío del website (solo para información)
    delivery_country_id = fields.Many2one(
        'res.country',
        string='País de Envío',
        help='País de envío capturado del checkout del website'
    )
    delivery_state_id = fields.Many2one(
        'res.country.state',
        string='Provincia/Estado de Envío',
        help='Provincia o estado de envío capturado del website'
    )
    delivery_city = fields.Char(
        string='Ciudad de Envío',
        help='Ciudad de envío capturada del website'
    )

    def _get_geographic_company(self):
        """Obtener la compañía más adecuada según la ubicación del cliente"""
        self.ensure_one()
        
        # Prioridad 1: Usar datos de envío del website si existen
        if self.delivery_country_id:
            _logger.info(f"=== Buscando compañía para envío: {self.delivery_city}, {self.delivery_state_id.name if self.delivery_state_id else ''}, {self.delivery_country_id.name}")
            company = self.env['res.company'].sudo().find_company_by_location(
                country_id=self.delivery_country_id.id,
                state_id=self.delivery_state_id.id if self.delivery_state_id else None,
                city=self.delivery_city
            )
            if company:
                _logger.info(f"=== Compañía encontrada por datos de envío: {company.name}")
                return company
        
        # Prioridad 2: Usar dirección del cliente
        if self.partner_id and self.partner_id.country_id:
            _logger.info(f"=== Buscando compañía para cliente: {self.partner_id.city}, {self.partner_id.state_id.name if self.partner_id.state_id else ''}, {self.partner_id.country_id.name}")
            company = self.env['res.company'].sudo().find_company_by_location(
                country_id=self.partner_id.country_id.id,
                state_id=self.partner_id.state_id.id if self.partner_id.state_id else None,
                city=self.partner_id.city
            )
            if company:
                _logger.info(f"=== Compañía encontrada por datos del cliente: {company.name}")
                return company
                
        _logger.warning("=== No se encontró compañía geográfica adecuada")
        return False

    def assign_geographic_company(self):
        """Botón para asignar compañía geográficamente"""
        for order in self:
            company = order._get_geographic_company()
            if company:
                if order.state in ('done', 'cancel'):
                    raise UserError(_('No se puede cambiar la compañía en órdenes finalizadas o canceladas.'))
                
                # Asignar compañía al pedido
                order.write({'company_id': company.id})
                
                # Asegurar compatibilidad de empresa en los partners
                self._ensure_partner_company_compatibility(company)
                
                order.message_post(
                    body=f"Compañía asignada automáticamente a: {company.name}"
                )
            else:
                raise UserError(_('No se encontró una compañía adecuada para la ubicación.'))

    def _ensure_partner_company_compatibility(self, company):
        """Asegurar que los partners del pedido sean compatibles con la empresa asignada"""
        self.ensure_one()
        
        partners_to_update = []
        
        # Verificar partner principal
        if self.partner_id and self.partner_id.company_id and self.partner_id.company_id != company:
            partners_to_update.append(self.partner_id)
            
        # Verificar partner de facturación si es diferente
        if (self.partner_invoice_id and 
            self.partner_invoice_id != self.partner_id and
            self.partner_invoice_id.company_id and 
            self.partner_invoice_id.company_id != company):
            partners_to_update.append(self.partner_invoice_id)
            
        # Verificar partner de envío si es diferente
        if (self.partner_shipping_id and 
            self.partner_shipping_id != self.partner_id and
            self.partner_shipping_id.company_id and 
            self.partner_shipping_id.company_id != company):
            partners_to_update.append(self.partner_shipping_id)
        
        # Actualizar empresa de los partners que lo necesiten
        if partners_to_update:
            # Eliminar duplicados
            unique_partners = list(set(partners_to_update))
            
            for partner in unique_partners:
                old_company = partner.company_id.name if partner.company_id else 'Sin empresa'
                
                # Actualizar la empresa del partner
                partner.sudo().write({'company_id': company.id})
                
                _logger.info(f"=== Partner '{partner.name}' actualizado de empresa '{old_company}' a '{company.name}'")
                
                # Agregar nota al partner
                partner.message_post(
                    body=f"Empresa actualizada automáticamente de '{old_company}' a '{company.name}' por asignación geográfica en pedido {self.name}"
                )

    def debug_geographic_assignment(self):
        """Método de debug para probar la asignación paso a paso"""
        self.ensure_one()
        
        message = "=== DEBUG ASIGNACIÓN GEOGRÁFICA ===\n"
        
        # Información de la orden
        message += f"Orden: {self.name}\n"
        message += f"Compañía actual: {self.company_id.name}\n"
        message += f"Cliente: {self.partner_id.name}\n\n"
        
        # Datos del cliente
        if self.partner_id:
            message += "--- Datos del cliente ---\n"
            message += f"País: {self.partner_id.country_id.name if self.partner_id.country_id else 'No definido'}\n"
            message += f"Estado: {self.partner_id.state_id.name if self.partner_id.state_id else 'No definido'}\n"
            message += f"Ciudad: {self.partner_id.city or 'No definida'}\n\n"
        
        # Datos de envío del website
        if self.delivery_country_id:
            message += "--- Datos de envío del website ---\n"
            message += f"País: {self.delivery_country_id.name}\n"
            message += f"Estado: {self.delivery_state_id.name if self.delivery_state_id else 'No definido'}\n"
            message += f"Ciudad: {self.delivery_city or 'No definida'}\n\n"
        
        # Compañías disponibles
        companies = self.env['res.company'].search([('geo_assignment_enabled', '=', True)])
        message += f"--- Compañías con asignación geográfica activa ({len(companies)}) ---\n"
        
        for company in companies:
            message += f"\n🏢 {company.name}:\n"
            message += f"   Prioridad: {company.geo_priority}\n"
            message += f"   Países: {', '.join(company.geo_country_ids.mapped('name'))}\n"
            message += f"   Estados: {', '.join(company.geo_state_ids.mapped('name')) if company.geo_state_ids else 'Todos'}\n"
            message += f"   Ciudades: {company.geo_cities or 'Todas'}\n"
        
        # Resultado de asignación
        company = self._get_geographic_company()
        message += f"\n--- Resultado ---\n"
        message += f"Compañía recomendada: {company.name if company else 'Ninguna'}\n"
        
        _logger.info(message)
        self.message_post(body=message.replace('\n', '<br/>'))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Debug completado. Compañía recomendada: {company.name if company else "Ninguna"}',
                'type': 'info',
                'sticky': False,
            }
        }

    def write(self, vals):
        """Override write para detectar cambios en partner y reasignar compañía"""
        result = super().write(vals)
        
        # Si se cambió el partner, verificar si necesita reasignación geográfica
        if 'partner_id' in vals:
            for order in self:
                if order.state in ['draft', 'sent']:  # Solo órdenes no confirmadas
                    company = order._get_geographic_company()
                    if company and company != order.company_id:
                        _logger.info(f"=== Reasignando orden {order.name} por cambio de partner")
                        order.company_id = company
                        order._ensure_partner_company_compatibility(company)
        
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Asignar compañía automáticamente al crear orden"""
        orders = super().create(vals_list)
        for order in orders:
            # Intentar asignación geográfica siempre, no solo si no tiene compañía
            company = order._get_geographic_company()
            if company and company != order.company_id:
                _logger.info(f"=== Asignando compañía {company.name} a nueva orden {order.name}")
                order.company_id = company
                # Asegurar compatibilidad de empresa en los partners
                order._ensure_partner_company_compatibility(company)
        return orders

    def force_geographic_assignment(self):
        """Método para forzar reasignación geográfica manual"""
        self.ensure_one()
        
        if self.state not in ['draft', 'sent']:
            raise UserError(_('Solo se puede reasignar compañía en órdenes en borrador o enviadas.'))
        
        company = self._get_geographic_company()
        if company:
            old_company = self.company_id.name
            self.company_id = company
            self._ensure_partner_company_compatibility(company)
            
            self.message_post(
                body=f"Compañía reasignada manualmente de '{old_company}' a '{company.name}'"
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Orden reasignada a {company.name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_('No se encontró una compañía adecuada para la ubicación del cliente.')) 