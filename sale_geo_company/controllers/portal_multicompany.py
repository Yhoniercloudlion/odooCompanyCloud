from odoo import http, fields, _
from odoo.http import request
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.sale.controllers.portal import CustomerPortal
import logging

_logger = logging.getLogger(__name__)


class PortalMultiCompany(PortalAccount, CustomerPortal):
    """Extiende el portal estándar para eliminar la restricción de company_id
    y mostrar al cliente todos sus documentos aunque la venta esté asignada
    a una compañía distinta."""

    _items_per_page = 20  # mantener paginación coherente

    # ---------------------------------------------------------------------
    # Sobrescribir el método que genera el dominio de facturas
    # ---------------------------------------------------------------------
    def _get_invoices_domain(self, invoice_type=None):
        """Sobrescribe el método padre para usar el partner actual y eliminar 
        restricciones de company_id"""
        
        # Obtener el partner del usuario actual
        partner = request.env.user.partner_id
        if not partner:
            return []
            
        # Usar el partner comercial para incluir todas las facturas relacionadas
        commercial = partner.commercial_partner_id
        
        # Dominio base
        domain = [
            ('partner_id', 'child_of', commercial.id),
            ('state', 'in', ('posted', 'cancel')),
        ]
        
        # Agregar filtro por tipo de factura si se especifica
        if invoice_type == 'in':
            # Facturas de proveedor (bills)
            domain.append(('move_type', 'in', ('in_invoice', 'in_refund')))
        elif invoice_type == 'out' or invoice_type is None:
            # Facturas de cliente (por defecto)
            domain.append(('move_type', 'in', ('out_invoice', 'out_refund')))
        
        return domain

    # ---------------------------------------------------------------------
    # Sobrescribir el método que genera el dominio de órdenes de venta
    # ---------------------------------------------------------------------
    def _get_orders_domain(self):
        """Sobrescribe el método padre para mostrar todas las órdenes 
        relacionadas con el partner comercial"""
        
        partner = request.env.user.partner_id
        if not partner:
            return []
            
        commercial = partner.commercial_partner_id
        return [('partner_id', 'child_of', commercial.id)]

    # ---------------------------------------------------------------------
    # Contadores del dashboard                                                
    # ---------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        """Sobrescribe para usar nuestros dominios personalizados"""
        values = super()._prepare_home_portal_values(counters)

        if 'order_count' in counters:
            values['order_count'] = request.env['sale.order'].sudo().search_count(
                self._get_orders_domain()
            )

        if 'invoice_count' in counters:
            values['invoice_count'] = request.env['account.move'].sudo().search_count(
                self._get_invoices_domain() + [('move_type', 'in', ('out_invoice', 'out_refund'))]
            )
            
        # Agregar contadores adicionales necesarios para el portal
        if 'bill_count' in counters:
            values['bill_count'] = request.env['account.move'].sudo().search_count(
                self._get_invoices_domain() + [('move_type', 'in', ('in_invoice', 'in_refund'))]
            )
            
        # Contar facturas vencidas
        overdue_domain = self._get_invoices_domain() + [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('payment_state', 'not in', ('paid', 'in_payment')),
            ('invoice_date_due', '<', fields.Date.today())
        ]
        values['overdue_invoice_count'] = request.env['account.move'].sudo().search_count(overdue_domain)
            
        return values

    # ---------------------------------------------------------------------
    # Sobrescribir rutas principales de pedidos y facturas
    # ---------------------------------------------------------------------
    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Sobrescribir para usar dominio sin restricción de compañía"""
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Usar nuestro dominio personalizado
        domain = self._get_orders_domain()

        # Filtros adicionales por fecha
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # Configurar ordenamiento
        searchbar_sortings = {
            'date': {'label': _('Fecha más reciente'), 'order': 'date_order desc'},
            'name': {'label': _('Referencia'), 'order': 'name'},
            'stage': {'label': _('Estado'), 'order': 'state'},
        }
        if not sortby:
            sortby = 'date'

        # Paginación
        pager_values = self._get_portal_pager_values(
            request.env['sale.order'].sudo(), domain, self._items_per_page, page,
            url="/my/orders", url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            sortby=sortby
        )

        # Buscar órdenes CON SUDO
        orders = request.env['sale.order'].sudo().search(
            domain, order=searchbar_sortings[sortby]['order'],
            limit=self._items_per_page, offset=pager_values['offset']
        )

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'orders': orders,
            'page_name': 'order',
            'archive_groups': [],
            'default_url': '/my/orders',
            'pager': pager_values['pager'],
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        
        _logger.info(f"=== Portal órdenes para {partner.name}: {len(orders)} órdenes encontradas")
        return request.render("sale.portal_my_orders", values)

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        """Sobrescribir para permitir acceso sin restricción de compañía"""
        
        # Usar sudo para acceder al pedido sin restricción de compañía
        order_sudo = request.env['sale.order'].sudo().browse(order_id)
        
        # Verificar que el pedido pertenece al partner del usuario
        partner = request.env.user.partner_id
        if not partner or order_sudo.partner_id.commercial_partner_id != partner.commercial_partner_id:
            return request.not_found()
        
        # Verificar acceso con token si se proporciona
        if access_token:
            try:
                order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
            except Exception as e:
                _logger.warning(f"=== Fallo verificación de token para pedido {order_id}: {e}")
                # Continuar con sudo si el partner coincide
                
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, 
                                   report_ref='sale.action_report_saleorder', download=download)

        values = {
            'sale_order': order_sudo,
            'object': order_sudo,  # Requerido para el template message_thread
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
            'res_company': order_sudo.company_id,
        }
        
        _logger.info(f"=== Acceso a pedido {order_sudo.name} (Compañía: {order_sudo.company_id.name}) para {partner.name}")
        return request.render('sale.sale_order_portal_template', values)

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Sobrescribir para usar dominio sin restricción de compañía"""
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Dominio base
        domain = self._get_invoices_domain()

        # Aplicar filtros por tipo
        searchbar_filters = {
            'all': {'label': _('Todas'), 'domain': []},
            'invoices': {'label': _('Facturas'), 'domain': [('move_type', 'in', ('out_invoice', 'out_refund'))]},
            'bills': {'label': _('Facturas de proveedor'), 'domain': [('move_type', 'in', ('in_invoice', 'in_refund'))]},
        }
        
        if not filterby:
            filterby = 'invoices'
            
        # Aplicar filtro seleccionado
        domain += searchbar_filters[filterby]['domain']

        # Filtros adicionales por fecha
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # Configurar ordenamiento
        searchbar_sortings = {
            'date': {'label': _('Fecha'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Fecha de vencimiento'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Referencia'), 'order': 'name desc'},
            'state': {'label': _('Estado'), 'order': 'state'},
        }
        
        if not sortby:
            sortby = 'date'

        # Calcular contadores necesarios para el template
        invoice_count = request.env['account.move'].sudo().search_count(
            self._get_invoices_domain() + [('move_type', 'in', ('out_invoice', 'out_refund'))]
        )
        bill_count = request.env['account.move'].sudo().search_count(
            self._get_invoices_domain() + [('move_type', 'in', ('in_invoice', 'in_refund'))]
        )
        
        # Contar facturas vencidas
        overdue_domain = self._get_invoices_domain() + [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('payment_state', 'not in', ('paid', 'in_payment')),
            ('invoice_date_due', '<', fields.Date.today())
        ]
        overdue_invoice_count = request.env['account.move'].sudo().search_count(overdue_domain)

        # Paginación
        pager_values = self._get_portal_pager_values(
            request.env['account.move'].sudo(), domain, self._items_per_page, page,
            url="/my/invoices", 
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            sortby=sortby
        )

        # Buscar facturas CON SUDO
        invoices = request.env['account.move'].sudo().search(
            domain, order=searchbar_sortings[sortby]['order'],
            limit=self._items_per_page, offset=pager_values['offset']
        )

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'invoices': invoices,
            'page_name': 'invoice',
            'archive_groups': [],
            'default_url': '/my/invoices',
            'pager': pager_values['pager'],
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'invoice_count': invoice_count,
            'bill_count': bill_count,
            'overdue_invoice_count': overdue_invoice_count,
        })
        
        _logger.info(f"=== Portal facturas para {partner.name}: {len(invoices)} facturas encontradas (filtro: {filterby})")
        return request.render("account.portal_my_invoices", values)

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_invoice_page(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        """Sobrescribir para permitir acceso sin restricción de compañía"""
        
        # Usar sudo para acceder a la factura sin restricción de compañía
        invoice_sudo = request.env['account.move'].sudo().browse(invoice_id)
        
        # Verificar que la factura pertenece al partner del usuario
        partner = request.env.user.partner_id
        if not partner or invoice_sudo.partner_id.commercial_partner_id != partner.commercial_partner_id:
            return request.not_found()
        
        # Verificar acceso con token si se proporciona
        if access_token:
            try:
                invoice_sudo = self._document_check_access('account.move', invoice_id, access_token=access_token)
            except Exception as e:
                _logger.warning(f"=== Fallo verificación de token para factura {invoice_id}: {e}")
                # Continuar con sudo si el partner coincide

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type,
                                   report_ref='account.account_invoices', download=download)

        values = {
            'invoice': invoice_sudo,
            'object': invoice_sudo,  # Requerido para el template message_thread
            'message': False,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': invoice_sudo.partner_id.id,
            'report_type': 'html',
            'action': invoice_sudo._get_portal_return_action(),
            'res_company': invoice_sudo.company_id,
        }
        
        _logger.info(f"=== Acceso a factura {invoice_sudo.name} (Compañía: {invoice_sudo.company_id.name}) para {partner.name}")
        return request.render('account.portal_invoice_page', values)

    def _get_portal_pager_values(self, model, domain, items_per_page, page, url, url_args, sortby):
        """Método auxiliar para configurar paginación"""
        total = model.search_count(domain)
        
        from odoo.addons.portal.controllers.portal import pager
        pager_values = pager(
            url=url,
            url_args=url_args,
            total=total,
            page=page,
            step=items_per_page
        )
        
        return {
            'pager': pager_values,
            'offset': (page - 1) * items_per_page,
        }