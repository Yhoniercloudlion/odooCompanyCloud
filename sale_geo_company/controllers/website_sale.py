from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleGeoCompany(WebsiteSale):

    @http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
    def shop_checkout(self, **post):
        """Interceptar el checkout principal para capturar datos de envío"""
        
        _logger.info(f"=== SHOP CHECKOUT: Datos recibidos: {post}")
        
        # Ejecutar el checkout original
        response = super().shop_checkout(**post)
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order:
            _logger.info(f"=== Orden en shop_checkout: {order.name}")
            self._try_assign_geographic_company(order, post)
                    
        return response

    @http.route()
    def checkout(self, **post):
        """Extender el checkout para capturar datos de envío y asignar compañía automáticamente"""
        
        _logger.info(f"=== CHECKOUT GEO COMPANY: Datos recibidos: {post}")
        
        # Marcar contexto para identificar partners del website
        context = dict(request.env.context)
        context.update({
            'from_website': True,
            'website_sale_order': True
        })
        request.env.context = context
        
        # Ejecutar el checkout original
        response = super().checkout(**post)
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order:
            _logger.info(f"=== Orden encontrada: {order.name}, Compañía actual: {order.company_id.name}")
            
            # Intentar asignar compañía en cada paso del checkout
            self._try_assign_geographic_company(order, post)
                    
        return response

    @http.route()
    def address(self, **kw):
        """Capturar también en la página de dirección"""
        
        _logger.info(f"=== ADDRESS GEO COMPANY: Datos recibidos: {kw}")
        
        # Marcar contexto para identificar partners del website
        context = dict(request.env.context)
        context.update({
            'from_website': True,
            'website_sale_order': True
        })
        request.env.context = context
        
        # Ejecutar el método original
        response = super().address(**kw)
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order:
            _logger.info(f"=== Orden en address: {order.name}")
            self._try_assign_geographic_company(order, kw)
                    
        return response

    @http.route(['/shop/address'], type='http', auth="public", website=True, sitemap=False)
    def shop_address(self, **kw):
        """Interceptar específicamente la página de dirección"""
        
        _logger.info(f"=== SHOP ADDRESS: Datos recibidos: {kw}")
        
        # Ejecutar el método original
        response = super().address(**kw)
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order:
            _logger.info(f"=== Orden en shop_address: {order.name}")
            self._try_assign_geographic_company(order, kw)
                    
        return response

    def _try_assign_geographic_company(self, order, post_data):
        """Intentar asignar compañía geográfica basada en los datos disponibles"""
        
        try:
            # Refrescar la orden para obtener datos actualizados
            order.invalidate_recordset()
            
            # Capturar datos de diferentes fuentes posibles
            country_id = self._extract_country_id(post_data, order)
            state_id = self._extract_state_id(post_data, order)
            city = self._extract_city(post_data, order)
            
            _logger.info(f"=== Datos extraídos: País={country_id}, Estado={state_id}, Ciudad={city}")
            
            # Si no tenemos datos de POST, intentar obtener del partner actualizado
            if not country_id and order.partner_id:
                order.partner_id.invalidate_recordset()
                if order.partner_id.country_id:
                    country_id = order.partner_id.country_id.id
                    state_id = order.partner_id.state_id.id if order.partner_id.state_id else None
                    city = order.partner_id.city
                    _logger.info(f"=== Datos del partner actualizado: País={country_id}, Estado={state_id}, Ciudad={city}")
            
            # Si tenemos al menos el país, intentar asignar
            if country_id:
                self._assign_company_to_order(order, country_id, state_id, city, post_data)
            else:
                _logger.warning("=== No se pudo extraer country_id de los datos ni del partner")
                
        except Exception as e:
            _logger.error(f"=== Error en _try_assign_geographic_company: {e}")

    def _extract_country_id(self, post_data, order):
        """Extraer country_id de múltiples fuentes"""
        
        # Buscar en los datos del POST
        country_sources = [
            'country_id', 'partner_country_id', 'shipping_country_id', 
            'billing_country_id', 'delivery_country_id'
        ]
        
        for source in country_sources:
            if source in post_data:
                try:
                    country_id = int(post_data[source])
                    _logger.info(f"=== País encontrado en {source}: {country_id}")
                    return country_id
                except (ValueError, TypeError):
                    continue
        
        # Buscar en el partner de la orden
        if order.partner_id and order.partner_id.country_id:
            _logger.info(f"=== País del partner: {order.partner_id.country_id.id}")
            return order.partner_id.country_id.id
            
        # Buscar en partner de envío si existe
        if order.partner_shipping_id and order.partner_shipping_id.country_id:
            _logger.info(f"=== País del partner de envío: {order.partner_shipping_id.country_id.id}")
            return order.partner_shipping_id.country_id.id
            
        return None

    def _extract_state_id(self, post_data, order):
        """Extraer state_id de múltiples fuentes"""
        
        state_sources = [
            'state_id', 'partner_state_id', 'shipping_state_id', 
            'billing_state_id', 'delivery_state_id'
        ]
        
        for source in state_sources:
            if source in post_data:
                try:
                    state_id = int(post_data[source])
                    _logger.info(f"=== Estado encontrado en {source}: {state_id}")
                    return state_id
                except (ValueError, TypeError):
                    continue
        
        # Buscar en el partner
        if order.partner_id and order.partner_id.state_id:
            return order.partner_id.state_id.id
            
        if order.partner_shipping_id and order.partner_shipping_id.state_id:
            return order.partner_shipping_id.state_id.id
            
        return None

    def _extract_city(self, post_data, order):
        """Extraer city de múltiples fuentes"""
        
        city_sources = ['city', 'partner_city', 'shipping_city', 'billing_city', 'delivery_city']
        
        for source in city_sources:
            if source in post_data and post_data[source]:
                city = post_data[source].strip()
                _logger.info(f"=== Ciudad encontrada en {source}: {city}")
                return city
        
        # Buscar en el partner
        if order.partner_id and order.partner_id.city:
            return order.partner_id.city
            
        if order.partner_shipping_id and order.partner_shipping_id.city:
            return order.partner_shipping_id.city
            
        return None

    def _assign_company_to_order(self, order, country_id, state_id, city, post_data):
        """Asignar compañía a la orden basada en ubicación"""
        
        try:
            # Usar el algoritmo existente para encontrar la compañía
            company = request.env['res.company'].sudo().find_company_by_location(
                country_id=country_id,
                state_id=state_id,
                city=city
            )
            
            _logger.info(f"=== Compañía encontrada por algoritmo: {company.name if company else 'Ninguna'}")
            
            if company and company != order.company_id:
                # Guardar los datos de envío en la orden
                vals = {
                    'delivery_country_id': country_id,
                    'delivery_state_id': state_id,
                    'delivery_city': city,
                    'company_id': company.id
                }
                
                order.sudo().write(vals)
                
                # Log detallado para seguimiento
                country_name = request.env['res.country'].sudo().browse(country_id).name
                state_name = request.env['res.country.state'].sudo().browse(state_id).name if state_id else ''
                
                _logger.info(f"=== ✅ ÉXITO: Orden {order.name} asignada a {company.name} "
                           f"basado en: {city}, {state_name}, {country_name}")
                           
            elif company == order.company_id:
                _logger.info(f"=== Orden ya está asignada a la compañía correcta: {company.name}")
            else:
                _logger.warning(f"=== No se encontró compañía para país={country_id}, estado={state_id}, ciudad={city}")
                
        except Exception as e:
            _logger.error(f"=== Error al asignar compañía: {e}")
            # No interrumpir el checkout si hay error

    @http.route(['/shop/payment/validate'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_validate(self, **post):
        """Extender validación de pago para asegurar compatibilidad de empresas"""
        
        _logger.info(f"=== SHOP PAYMENT VALIDATE: Datos recibidos: {post}")
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order:
            try:
                # ÚLTIMO INTENTO: Asignar compañía geográfica antes del pago
                _logger.info(f"=== ÚLTIMO INTENTO de asignación geográfica para orden {order.name}")
                self._try_assign_geographic_company(order, post)
                
                # Asegurar que el usuario del partner tenga acceso a todas las compañías
                self._ensure_user_company_access(order)
                
                # Asegurar compatibilidad de empresa en partners
                order._ensure_partner_company_compatibility(order.company_id)
                
                _logger.info(f"=== Compatibilidad de empresas verificada para orden {order.name}")
                
            except Exception as e:
                _logger.error(f"=== Error verificando compatibilidad de empresas: {e}")
        
        # Ejecutar el método original
        return super().shop_payment_validate(**post)

    def _ensure_user_company_access(self, order):
        """Asegurar que el usuario del partner tenga acceso a todas las compañías"""
        
        if not order.partner_id:
            return
            
        # Buscar usuarios relacionados con este partner
        users = request.env['res.users'].sudo().search([
            ('partner_id', '=', order.partner_id.id),
            ('active', '=', True)
        ])
        
        for user in users:
            # Verificar si el usuario necesita actualización
            all_companies = request.env['res.company'].sudo().search([('active', '=', True)])
            
            if len(user.company_ids) < len(all_companies):
                # Asignar todas las compañías al usuario
                user.sudo().write({
                    'company_ids': [(6, 0, all_companies.ids)]
                })
                
                _logger.info(f"=== Usuario {user.name} actualizado con acceso a {len(all_companies)} compañías")
                
                # Configurar partner sin restricción de compañía
                user.partner_id.sudo().write({'company_id': False})
                
                _logger.info(f"=== Partner {user.partner_id.name} configurado sin restricción de compañía") 