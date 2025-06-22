from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.utils import redirect
import logging

_logger = logging.getLogger(__name__)


class WebsiteSaleGeoCompany(WebsiteSale):

    @http.route()
    def checkout(self, **post):
        """Extender checkout para asignar compañía cuando se completan datos de envío"""
        
        # Ejecutar el checkout original primero
        response = super().checkout(**post)
        
        # Obtener la orden actual
        order = request.website.sale_get_order()
        
        if order and post:
            # Si hay datos en el POST, intentar asignar compañía
            self._try_assign_geographic_company(order, post)
                    
        return response

    @http.route(['/shop/payment'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment(self, **post):
        """Verificar datos de envío antes de proceder al pago"""
        
        order = request.website.sale_get_order()
        
        if not order:
            return redirect('/shop')
        
        # Verificar si faltan datos de envío esenciales
        missing_data = self._check_missing_shipping_data(order)
        
        if missing_data:
            _logger.info(f"=== Faltan datos de envío para orden {order.name}: {missing_data}")
            # Redirigir al checkout para completar datos
            return redirect('/shop/checkout?missing_data=true')
        
        # Si hay datos de envío, intentar asignar compañía una última vez
        self._try_assign_geographic_company_from_partner(order)
        
        # Proceder al pago normal
        return super().shop_payment(**post)

    def _check_missing_shipping_data(self, order):
        """Verificar qué datos de envío faltan"""
        missing = []
        
        # Verificar partner principal
        if not order.partner_id:
            missing.append("cliente")
            return missing
        
        partner = order.partner_id
        
        # Verificar datos básicos de envío
        if not partner.country_id:
            missing.append("país")
        
        if not partner.state_id and partner.country_id and partner.country_id.state_required:
            missing.append("estado/provincia")
            
        if not partner.city:
            missing.append("ciudad")
            
        if not partner.street:
            missing.append("dirección")
            
        return missing

    def _try_assign_geographic_company(self, order, post_data):
        """Intentar asignar compañía geográfica desde datos del POST"""
        
        try:
            # Extraer datos del POST
            country_id = self._extract_country_id(post_data)
            state_id = self._extract_state_id(post_data)
            city = self._extract_city(post_data)
            
            if country_id:
                _logger.info(f"=== Asignando compañía para orden {order.name}: País={country_id}, Estado={state_id}, Ciudad={city}")
                self._assign_company_by_location(order, country_id, state_id, city)
                
        except Exception as e:
            _logger.error(f"=== Error en asignación geográfica: {e}")

    def _try_assign_geographic_company_from_partner(self, order):
        """Intentar asignar compañía geográfica desde datos del partner"""
        
        try:
            if not order.partner_id:
                return
                
            partner = order.partner_id
            
            if partner.country_id:
                country_id = partner.country_id.id
                state_id = partner.state_id.id if partner.state_id else None
                city = partner.city
                
                _logger.info(f"=== Asignando compañía desde partner para orden {order.name}: País={country_id}, Estado={state_id}, Ciudad={city}")
                self._assign_company_by_location(order, country_id, state_id, city)
                
        except Exception as e:
            _logger.error(f"=== Error en asignación desde partner: {e}")

    def _extract_country_id(self, post_data):
        """Extraer country_id del POST"""
        for key in ['country_id', 'partner_country_id']:
            if key in post_data:
                try:
                    return int(post_data[key])
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_state_id(self, post_data):
        """Extraer state_id del POST"""
        for key in ['state_id', 'partner_state_id']:
            if key in post_data:
                try:
                    return int(post_data[key])
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_city(self, post_data):
        """Extraer city del POST"""
        for key in ['city', 'partner_city']:
            if key in post_data and post_data[key]:
                return post_data[key].strip()
        return None

    def _assign_company_by_location(self, order, country_id, state_id, city):
        """Asignar compañía basada en ubicación geográfica"""
        
        try:
            # Usar el método existente del modelo res.company
            company = request.env['res.company'].sudo().find_company_by_location(
                country_id=country_id,
                state_id=state_id,
                city=city
            )
            
            if company and company != order.company_id:
                # Asignar la nueva compañía
                order.sudo().write({'company_id': company.id})
                
                # Obtener nombres para el log
                country_name = request.env['res.country'].sudo().browse(country_id).name
                state_name = request.env['res.country.state'].sudo().browse(state_id).name if state_id else 'N/A'
                city_name = city or 'N/A'
                
                _logger.info(f"=== ✅ ÉXITO: Orden {order.name} asignada a {company.name} "
                           f"basado en: {city_name}, {state_name}, {country_name}")
                
                # Asegurar compatibilidad de empresas
                order._ensure_partner_company_compatibility()
                
            elif company == order.company_id:
                _logger.info(f"=== Orden {order.name} ya está asignada a la compañía correcta: {company.name}")
            else:
                _logger.warning(f"=== No se encontró compañía específica para la ubicación, manteniendo compañía actual")
                
        except Exception as e:
            _logger.error(f"=== Error al asignar compañía por ubicación: {e}")