# Módulo de Asignación Geográfica de Compañías

## Descripción

Este módulo implementa un sistema de asignación automática de compañías basado en la ubicación geográfica, **usando los campos existentes del checkout del website**.

## Flujo de Funcionamiento

1. **Órdenes de Venta Manuales**: Al crear una orden, se asigna automáticamente la compañía más cercana según la ubicación del cliente.

2. **🆕 Checkout del Website**: Cuando un cliente realiza una compra desde el website y completa los **datos de envío existentes** (país, provincia, ciudad), se asigna automáticamente la compañía más cercana a esa ubicación **solo a la orden de venta**.

3. **El cliente NO cambia de compañía** - solo la orden de venta se asigna geográficamente.

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

**España General:**
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

## Funcionamiento en Website

### **Proceso Automático:**
1. Cliente va al checkout del website
2. Completa los **campos de envío existentes** (país, provincia, ciudad)
3. **Automáticamente** se asigna la compañía más cercana a la orden
4. El cliente continúa con el pago normalmente
5. La orden queda asignada a la compañía correcta

### **No hay cambios visuales** en el website - todo funciona transparentemente en segundo plano.

## Funcionalidades

- ✅ **Asignación automática** en órdenes del website
- ✅ **Asignación automática** en órdenes manuales
- ✅ **Botón manual** para reasignar compañía
- ✅ **Sistema de logs** para auditoría
- ✅ **Configuración flexible** por compañía
- ✅ **NO modifica** la experiencia del usuario en el website

## Instalación

1. **Instalar eCommerce** (website_sale) si no está instalado
2. **Instalar** el módulo "Asignación Geográfica de Compañías"
3. **Configurar** las compañías según se indica arriba
4. **¡Funciona automáticamente!**

## Compatibilidad

- ✅ Odoo 18.0
- ✅ Multi-compañía
- ✅ Website Sale (eCommerce)
- ✅ Sin modificaciones al frontend del website 