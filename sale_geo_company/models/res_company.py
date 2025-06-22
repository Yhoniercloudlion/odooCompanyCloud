from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Campos para configuración geográfica
    geo_assignment_enabled = fields.Boolean(
        string='Asignación Geográfica Activa',
        default=False,
        help='Activar para que esta compañía pueda ser asignada geográficamente'
    )
    geo_priority = fields.Integer(
        string='Prioridad de Asignación',
        default=10,
        help='Menor número = mayor prioridad en caso de empate'
    )
    geo_country_ids = fields.Many2many(
        'res.country',
        'company_country_geo_rel',
        'company_id',
        'country_id',
        string='Países de Servicio'
    )
    geo_state_ids = fields.Many2many(
        'res.country.state',
        'company_state_geo_rel',
        'company_id',
        'state_id',
        string='Estados/Provincias de Servicio'
    )
    geo_cities = fields.Text(
        string='Ciudades de Servicio',
        help='Lista de ciudades separadas por comas (ej: Madrid, Barcelona, Valencia)'
    )

    def find_company_by_location(self, country_id=None, state_id=None, city=None):
        """
        Encuentra la compañía más adecuada basada en ubicación geográfica
        Sistema de puntuación mejorado:
        - Coincidencia país: +3 puntos
        - Coincidencia estado: +2 puntos  
        - Coincidencia ciudad: +1 punto
        - Bonus por coincidencia exacta de ciudad: +0.5 puntos
        """
        if not country_id:
            _logger.warning("=== find_company_by_location: No se proporcionó country_id")
            return False

        # Buscar compañías con asignación geográfica activa
        companies = self.search([('geo_assignment_enabled', '=', True)])
        
        if not companies:
            _logger.warning("=== No hay compañías con asignación geográfica activa")
            return False

        scored_companies = []
        
        # Normalizar ciudad para comparación (sin acentos, minúsculas)
        normalized_city = self._normalize_city_name(city) if city else None
        
        _logger.info(f"=== Evaluando {len(companies)} compañías para: país={country_id}, estado={state_id}, ciudad='{city}' (normalizada: '{normalized_city}')")
        
        for company in companies:
            score = 0
            details = []
            
            # Verificar país (requisito mínimo)
            if country_id in company.geo_country_ids.ids:
                score += 3
                details.append("País: +3")
            else:
                _logger.info(f"=== {company.name}: No atiende país {country_id}")
                continue  # Sin país coincidente, descartar esta compañía
                
            # Verificar estado/provincia
            if company.geo_state_ids:
                # La compañía tiene estados específicos
                if state_id and state_id in company.geo_state_ids.ids:
                    score += 2
                    details.append("Estado específico: +2")
                else:
                    # No coincide con estados específicos, pero puede ser rescatada por ciudad
                    details.append("Estado no coincide: +0")
            else:
                # La compañía no tiene estados específicos, acepta cualquier estado
                score += 1
                details.append("Acepta cualquier estado: +1")
                
            # Verificar ciudad
            if company.geo_cities:
                # La compañía tiene ciudades específicas
                city_match = self._check_city_match(normalized_city, company.geo_cities)
                if city_match:
                    score += 1
                    details.append(f"Ciudad coincide '{city_match}': +1")
                    # Bonus por coincidencia exacta de ciudad
                    if normalized_city and city_match.lower() == normalized_city.lower():
                        score += 0.5
                        details.append("Coincidencia exacta de ciudad: +0.5")
                else:
                    details.append("Ciudad no coincide: +0")
            else:
                # La compañía no tiene ciudades específicas, acepta cualquier ciudad
                score += 0.5
                details.append("Acepta cualquier ciudad: +0.5")
                
            _logger.info(f"=== {company.name}: Puntuación {score} - {', '.join(details)}")
            scored_companies.append((company, score))
        
        if not scored_companies:
            _logger.warning("=== No se encontraron compañías elegibles")
            return False
            
        # Ordenar por puntuación (descendente) y prioridad (ascendente)
        scored_companies.sort(key=lambda x: (-x[1], x[0].geo_priority))
        
        winner = scored_companies[0][0]
        winner_score = scored_companies[0][1]
        
        _logger.info(f"=== 🎯 GANADORA: {winner.name} con {winner_score} puntos (prioridad {winner.geo_priority})")
        
        # Mostrar top 3 para debug
        for i, (comp, score) in enumerate(scored_companies[:3]):
            _logger.info(f"=== Ranking #{i+1}: {comp.name} - {score} puntos")
        
        return winner

    def _normalize_city_name(self, city):
        """Normalizar nombre de ciudad para mejor comparación"""
        if not city:
            return None
            
        # Convertir a minúsculas y quitar espacios extra
        normalized = city.lower().strip()
        
        # Mapeo de ciudades con acentos/variaciones comunes
        city_mappings = {
            'madrid': 'madrid',
            'madrid ': 'madrid',
            ' madrid': 'madrid',
            'barcelona': 'barcelona',
            'sevilla': 'sevilla',
            'valencia': 'valencia',
            'alcala de henares': 'alcalá de henares',
            'alcalá de henares': 'alcalá de henares',
        }
        
        return city_mappings.get(normalized, normalized)

    def _check_city_match(self, normalized_city, geo_cities):
        """Verificar si una ciudad coincide con las ciudades de servicio"""
        if not normalized_city or not geo_cities:
            return False
            
        # Obtener lista de ciudades de servicio (normalizadas)
        service_cities = [self._normalize_city_name(c.strip()) for c in geo_cities.split(',')]
        
        # Buscar coincidencia
        for service_city in service_cities:
            if service_city and normalized_city.lower() == service_city.lower():
                return service_city
                
        return False 