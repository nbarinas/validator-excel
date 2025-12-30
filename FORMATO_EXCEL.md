# Formato de Excel para Carga de Llamadas

## Columnas Requeridas

El archivo Excel debe contener las siguientes columnas (el sistema acepta variaciones en los nombres):

### 📞 **Teléfono** (OBLIGATORIO)
- **Nombres aceptados**: `Telefono`, `Celular`, `Numero`, `Movil`
- **Descripción**: Número de teléfono principal del contacto
- **Ejemplo**: `3001234567`

### 👤 **Nombre**
- **Nombres aceptados**: `Nombre`, `Cliente`, `Usuario`
- **Descripción**: Nombre completo de la persona
- **Ejemplo**: `María González`

### 🆔 **Cédula**
- **Nombres aceptados**: `Cedula`, `CC`, `ID`, `Identificacion`
- **Descripción**: Número de identificación
- **Ejemplo**: `1234567890`

### 🏙️ **Ciudad**
- **Nombres aceptados**: `Ciudad`, `City`
- **Descripción**: Ciudad de residencia
- **Ejemplo**: `Bogotá`, `Medellín`

### 📝 **Observaciones**
- **Nombres aceptados**: `Observaciones`, `Observacion`, `Obs`
- **Descripción**: Notas o comentarios iniciales
- **Ejemplo**: `Cliente interesado en producto X`

### ⏰ **Hora de Llamada**
- **Nombres aceptados**: `Hora de llamada`, `Hora`, `Cita`
- **Descripción**: Hora programada para contacto
- **Ejemplo**: `14:30`, `2:30 PM`

### 🏷️ **Marca de Producto**
- **Nombres aceptados**: `Marca de producto`, `Marca`
- **Descripción**: Marca o producto de interés
- **Ejemplo**: `Samsung`, `iPhone`

### 📱 **Otro Número**
- **Nombres aceptados**: `Otro numero`, `Otro telefono`, `Telefono 2`
- **Descripción**: Número de teléfono alternativo
- **Ejemplo**: `3109876543`

---

## Ejemplo de Estructura

| Telefono   | Nombre         | Cedula     | Ciudad   | Observaciones        | Hora de llamada | Marca de producto | Otro numero |
|------------|----------------|------------|----------|---------------------|----------------|------------------|-------------|
| 3001234567 | María González | 1234567890 | Bogotá   | Interesada en plan  | 14:30          | Samsung          | 3109876543  |
| 3102345678 | Juan Pérez     | 9876543210 | Medellín | Requiere información| 10:00          | iPhone           |             |

---

## Notas Importantes

1. ✅ **Solo el Teléfono es obligatorio** - Las demás columnas son opcionales
2. ✅ **Los nombres de columnas NO distinguen mayúsculas/minúsculas**
3. ✅ **Se aceptan múltiples variaciones** de nombres de columna (ver lista arriba)
4. ✅ **Las filas sin teléfono se omiten automáticamente**
5. ✅ **Los valores vacíos se manejan correctamente**

---

## Cómo Cargar

1. Prepara tu archivo Excel con las columnas mencionadas
2. Ve a **Call Center CRM** (solo superusuarios)
3. Haz clic en **"Cargar Base de Datos"**
4. Selecciona el archivo Excel
5. Ingresa el nombre del estudio
6. Haz clic en **"Cargar"**

El sistema procesará automáticamente todas las filas válidas y creará las llamadas en estado "pending".
