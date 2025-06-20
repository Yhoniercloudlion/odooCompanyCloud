from odoo import models, fields, api
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Campos para definir la ubicación geográfica de la compañía
    service_country_ids = fields.Many2many(
        'res.country',
        'company_country_rel',
        'company_id',
        'country_id',
        string='Países de Servicio',
        help='Países donde esta compañía presta servicios'
    )
    
    service_state_ids = fields.Many2many(
        'res.country.state',
        'company_state_rel',
        'company_id',
        'state_id',
        string='Estados/Provincias de Servicio',
        help='Estados o provincias específicas donde presta servicios'
    )
    
    service_cities = fields.Text(
        string='Ciudades de Servicio',
        help='Lista de ciudades separadas por comas donde presta servicios'
    )
    
    is_geographic_assignment = fields.Boolean(
        string='Asignación Geográfica',
        default=True,
        help='Si está marcado, esta compañía puede ser asignada automáticamente a usuarios basado en ubicación'
    )
    
    assignment_priority = fields.Integer(
        string='Prioridad de Asignación',
        default=10,
        help='Prioridad para asignación automática (menor número = mayor prioridad)'
    )

    @api.model
    def find_company_by_location(self, country_id, state_id=None, city=None):
        """
        Encuentra la compañía más adecuada basada en la ubicación del usuario
        """
        domain = [('is_geographic_assignment', '=', True)]
        companies = self.search(domain, order='assignment_priority asc')
        
        best_match = None
        best_score = 0
        
        for company in companies:
            score = 0
            
            # Verificar coincidencia de país
            if country_id in company.service_country_ids.ids:
                score += 3
                
                # Verificar coincidencia de estado/provincia
                if state_id and state_id in company.service_state_ids.ids:
                    score += 2
                
                # Verificar coincidencia de ciudad
                if city and company.service_cities:
                    cities_list = [c.strip().lower() for c in company.service_cities.split(',')]
                    if city.lower() in cities_list:
                        score += 1
                
                # Si es mejor puntuación, actualizar mejor coincidencia
                if score > best_score:
                    best_score = score
                    best_match = company
        
        return best_match or self.env.company  # Retorna la compañía actual como fallback 