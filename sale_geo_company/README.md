# Módulo de Asignación Geográfica de Compañías

## Descripción

Este módulo implementa un sistema de asignación automática de compañías basado en la ubicación geográfica de usuarios y clientes.

## Flujo de Funcionamiento

1. **Registro de Usuario**: Cuando un usuario se registra desde un website, se le asigna la compañía propietaria de ese website y **mantiene esa compañía permanentemente**.

2. **Actualización de Dirección**: Cuando el usuario actualiza su dirección, **mantiene la misma compañía** (no se reasigna).

3. **Órdenes de Venta**: Al crear una orden de venta, se asigna automáticamente la **compañía más cercana** según la ubicación del cliente (independiente de la compañía del usuario).

## Configuración

### Paso 1: Configurar Compañías
1. Ve a **Configuración → Compañías → Compañías**
2. Edita cada compañía y ve a la pestaña **"Asignación Geográfica"**
3. Configura:
   - ✅ **Asignación Geográfica Activa**
   - **Prioridad de Asignación** (número menor = mayor prioridad)
   - **Países de Servicio** (obligatorio)
   - **Estados/Provincias de Servicio** (opcional)
   - **Ciudades de Servicio** (opcional, separadas por comas)

### Ejemplo de Configuración:

**Compañía Madrid:**
- Países: España
- Estados: Madrid
- Ciudades: Madrid, Alcalá de Henares, Getafe
- Prioridad: 5

**Compañía España General:**
- Países: España
- Estados: (vacío - sirve toda España)
- Ciudades: (vacío)
- Prioridad: 10

## Sistema de Puntuación

El algoritmo asigna puntuaciones basadas en coincidencias:
- **País**: +3 puntos (obligatorio)
- **Estado/Provincia**: +2 puntos
- **Ciudad**: +1 punto

En caso de empate, gana la compañía con menor **Prioridad de Asignación**.

## Funcionalidades Técnicas

- **Usuarios mantienen su compañía original** (no se reasignan automáticamente)
- **Asignación automática en órdenes de venta** según ubicación del cliente
- **Botón manual** para reasignar compañía en órdenes de venta
- **Sistema de logs** para auditoría de asignaciones
- **Configuración flexible** de áreas geográficas por compañía

## Instalación

1. Instalar el módulo desde **Aplicaciones**
2. Configurar las compañías según se indica arriba
3. El sistema funcionará automáticamente

## Compatibilidad

- ✅ Odoo 18.0
- ✅ Multi-compañía
- ✅ Website
- ✅ Ventas 