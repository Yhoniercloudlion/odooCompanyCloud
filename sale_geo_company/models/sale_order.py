from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_geographic_company(self):
        """Obtener la compañía más adecuada según la ubicación del cliente"""
        self.ensure_one()
        if not self.partner_id or not self.partner_id.country_id:
            return False

        company = self.env['res.company'].sudo().find_company_by_location(
            country_id=self.partner_id.country_id.id,
            state_id=self.partner_id.state_id.id if self.partner_id.state_id else None,
            city=self.partner_id.city
        )

        if company:
            # Log para seguimiento
            self.env['ir.logging'].sudo().create({
                'name': 'sale_geo_company',
                'type': 'server',
                'level': 'INFO',
                'message': f'Venta {self.name} asignada a compañía {company.name} basado en ubicación del cliente: '
                          f'{self.partner_id.country_id.name}, '
                          f'{self.partner_id.state_id.name if self.partner_id.state_id else ""}, '
                          f'{self.partner_id.city or ""}',
                'path': 'sale_geo_company',
                'func': '_get_geographic_company'
            })
            return company
        return False

    def assign_geographic_company(self):
        """Botón para asignar compañía geográficamente"""
        for order in self:
            company = order._get_geographic_company()
            if company:
                if order.state != 'draft':
                    raise UserError(_('Solo se puede cambiar la compañía en órdenes en borrador.'))
                order.write({'company_id': company.id})
            else:
                raise UserError(_('No se encontró una compañía adecuada para la ubicación del cliente.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Sobreescribir create para asignar compañía automáticamente"""
        orders = super().create(vals_list)
        for order in orders:
            # Solo asignar si no tiene compañía ya asignada
            if not order.company_id:
                company = order._get_geographic_company()
                if company:
                    order.company_id = company
        return orders 