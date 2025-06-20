# Módulo de Asignación Geográfica de Compañías para Odoo 18

## Descripción del Problema Resuelto

Este módulo resuelve el problema de asignación automática de compañías a usuarios que se registran desde el website de Odoo, basándose en su ubicación geográfica (país, estado/provincia, ciudad).

**Problema original**: Cuando un usuario se registra normalmente, se asigna a "My Company" por defecto, sin considerar su ubicación.

**Solución**: El módulo captura la ubicación durante el registro y asigna automáticamente la compañía más cercana/apropiada.

## Funcionalidades Principales

1. **Formulario de Registro Extendido**: Agrega campos de país, estado/provincia y ciudad al formulario de registro web
2. **Configuración de Compañías**: Permite definir las áreas geográficas que atiende cada compañía
3. **Asignación Automática**: Algoritmo inteligente que selecciona la mejor compañía basada en coincidencias geográficas
4. **Sistema de Prioridades**: Manejo de múltiples coincidencias mediante prioridades configurables

## Cómo Implementar en Odoo.sh

### Paso 1: Subir el Módulo
1. **Descarga/Copia** toda la carpeta `geo_company_assignment` 
2. **Accede a tu repositorio Git** conectado con Odoo.sh
3. **Sube la carpeta** del módulo a la raíz de tu repositorio (al mismo nivel que otros módulos)
4. **Haz commit y push** de los cambios

### Paso 2: Activar el Módulo
1. Entra a tu instancia de Odoo.sh
2. Ve a **Aplicaciones**
3. Busca "Asignación Geográfica"
4. **Instala** el módulo

### Paso 3: Configurar Compañías
1. Ve a **Configuración → Compañías → Asignación Geográfica**
2. Para cada compañía:
   - Marca "Asignación Geográfica" = ✓
   - Define "Prioridad de Asignación" (número menor = mayor prioridad)
   - Selecciona "Países de Servicio"
   - Opcional: Selecciona "Estados/Provincias de Servicio"
   - Opcional: Lista "Ciudades de Servicio" separadas por comas

### Ejemplo de Configuración:

**Compañía Madrid:**
- Países: España
- Estados: Madrid
- Ciudades: Madrid, Alcalá de Henares, Getafe
- Prioridad: 5

**Compañía Barcelona:**
- Países: España  
- Estados: Cataluña
- Ciudades: Barcelona, Hospitalet, Badalona
- Prioridad: 5

**Compañía España General:**
- Países: España
- Ciudades: (dejar vacío para cubrir toda España)
- Prioridad: 10

## Cómo Funciona el Algoritmo

El sistema asigna puntuaciones basadas en coincidencias:

- **Coincidencia de País**: +3 puntos
- **Coincidencia de Estado/Provincia**: +2 puntos  
- **Coincidencia de Ciudad**: +1 punto

**Ejemplo**: Un usuario de "Barcelona, Cataluña, España":
- Compañía Barcelona: 3+2+1 = 6 puntos ✓ (Ganadora)
- Compañía España General: 3 puntos
- Compañía Madrid: 3 puntos

En caso de empate, gana la compañía con menor "Prioridad de Asignación".

## Personalización Adicional

### Modificar Campos del Formulario
Edita `views/website_auth_signup_templates.xml` para:
- Hacer campos obligatorios u opcionales
- Cambiar textos y etiquetas
- Agregar validaciones adicionales

### Ajustar Algoritmo de Asignación  
Modifica `models/res_company.py` método `find_company_by_location()` para:
- Cambiar sistema de puntuación
- Agregar criterios adicionales (código postal, región, etc.)
- Implementar lógica personalizada

### Campos Adicionales
Extiende `models/res_company.py` para agregar:
- Códigos postales
- Radios de cobertura en km
- Horarios de atención por zona
- Idiomas por región

## Pruebas

1. **Registra un usuario nuevo** desde `/web/signup`
2. **Completa todos los campos** incluyendo país, estado y ciudad
3. **Verifica** que el usuario se asignó a la compañía correcta
4. **Revisa** en Configuración → Usuarios que la compañía es la esperada

## Soporte y Mantenimiento

Este módulo es compatible con:
- ✅ Odoo 18.0
- ✅ Odoo.sh
- ✅ Instalaciones on-premise
- ✅ Multi-compañía

Para dudas o mejoras, revisa:
- Logs de Odoo si hay errores durante el registro
- Configuración de compañías si la asignación no es la esperada
- Permisos de usuario si no se pueden modificar configuraciones

## Estructura de Archivos

```
geo_company_assignment/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── res_company.py      # Extensión del modelo Company
│   └── res_users.py        # Lógica de asignación automática
├── views/
│   ├── res_company_views.xml          # Formularios de configuración
│   └── website_auth_signup_templates.xml  # Formulario de registro web
├── data/
│   └── company_locations_data.xml     # Datos de ejemplo
└── security/
    └── ir.model.access.csv            # Permisos de acceso
``` 

comentario de prueba 
