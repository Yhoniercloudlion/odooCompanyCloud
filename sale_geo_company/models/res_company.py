from odoo import models, fields, api, _


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
        Sistema de puntuación:
        - Coincidencia país: +3 puntos
        - Coincidencia estado: +2 puntos  
        - Coincidencia ciudad: +1 punto
        """
        if not country_id:
            return False

        # Buscar compañías con asignación geográfica activa
        companies = self.search([('geo_assignment_enabled', '=', True)])
        
        if not companies:
            return False

        scored_companies = []
        
        for company in companies:
            score = 0
            
            # Verificar país (requisito mínimo)
            if country_id in company.geo_country_ids.ids:
                score += 3
            else:
                continue  # Sin país coincidente, descartar esta compañía
                
            # Verificar estado/provincia
            if state_id and company.geo_state_ids:
                if state_id in company.geo_state_ids.ids:
                    score += 2
            elif not company.geo_state_ids:
                # Si la compañía no tiene estados específicos, puede servir cualquier estado del país
                score += 1
                
            # Verificar ciudad
            if city and company.geo_cities:
                cities_list = [c.strip().lower() for c in company.geo_cities.split(',')]
                if city.lower() in cities_list:
                    score += 1
            elif not company.geo_cities:
                # Si la compañía no tiene ciudades específicas, puede servir cualquier ciudad
                score += 0.5
                
            scored_companies.append((company, score))
        
        if not scored_companies:
            return False
            
        # Ordenar por puntuación (descendente) y prioridad (ascendente)
        scored_companies.sort(key=lambda x: (-x[1], x[0].geo_priority))
        
        return scored_companies[0][0] 