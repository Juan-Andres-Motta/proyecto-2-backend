# Entity Validations Report - Frontend Form Implementation Guide

This report details all database constraints and business validation rules for each entity in the system. Use this to implement form validations in the frontend.

---

## 1. SELLER MICROSERVICE

### Entity: Seller

**Endpoint**: POST `/sellers`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `name` | string | ✅ Yes | 255 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `email` | string | ✅ Yes | 255 | • Valid email format<br>• Cannot be empty |
| `phone` | string | ✅ Yes | 50 | • Trimmed<br>• Cannot be empty |
| `city` | string | ✅ Yes | 100 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `country` | string | ✅ Yes | 100 | • Valid ISO country code (name, alpha-2, or alpha-3)<br>• Normalized to alpha-2 on backend<br>• Cannot be empty |

**Business Rules**:
- Country must exist in ISO 3166-1 standard
- Email must be in valid email format

---

### Entity: SalesPlan

**Endpoint**: POST `/sales-plans`

| Field | Type | Required | Constraints | Validation Rules |
|-------|------|----------|-------------|------------------|
| `seller_id` | UUID | ✅ Yes | - | • Must be a valid UUID<br>• Seller must exist in system |
| `sales_period` | string | ✅ Yes | 50 | • Format: `Q{1-4}-{YEAR}`<br>• Example: "Q1-2025"<br>• Quarter must be 1-4<br>• Year must be between 2000-2100 |
| `goal` | float | ✅ Yes | Decimal(10,2) | • Must be > 0<br>• Max value: 99,999,999.99<br>• Up to 2 decimal places |
| `accumulate` | float | ❌ No | - | • **DO NOT include in form**<br>• Auto-set to 0 on creation |
| `status` | string | ❌ No | - | • **DO NOT include in form**<br>• Auto-calculated based on period and progress |

**Business Rules**:
1. **Sales Period Format**: Must match regex `^Q[1-4]-\d{4}$`
2. **Year Range**: Between 2000 and 2100
3. **Goal**: Must be a positive number
4. **Status** (read-only, calculated):
   - Future quarter → "planned"
   - Current quarter + goal not met → "in_progress"
   - Current quarter + goal met → "completed"
   - Past quarter + goal not met → "failed"
   - Past quarter + goal met → "completed"

---

## 2. ORDER MICROSERVICE

### Entity: Order

**Endpoint**: POST `/orders`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `customer_id` | UUID | ✅ Yes | - | • Must be a valid UUID<br>• Customer must exist |
| `metodo_creacion` | string (enum) | ✅ Yes | - | • Must be one of:<br>&nbsp;&nbsp;- `"visita_vendedor"`<br>&nbsp;&nbsp;- `"app_cliente"`<br>&nbsp;&nbsp;- `"app_vendedor"` |
| `items` | array | ✅ Yes | - | • Must contain at least 1 item<br>• Each item must be valid OrderItem |
| `seller_id` | UUID | ⚠️ Conditional | - | • **Required** if `metodo_creacion` = `"visita_vendedor"` or `"app_vendedor"`<br>• **Must be null** if `metodo_creacion` = `"app_cliente"` |
| `visit_id` | UUID | ⚠️ Conditional | - | • **Required** if `metodo_creacion` = `"visita_vendedor"`<br>• **Must be null** if `metodo_creacion` = `"app_cliente"`<br>• **Optional** if `metodo_creacion` = `"app_vendedor"` |

**Additional Fields** (populated by backend from customer/seller services):
- `customer_name`, `customer_phone`, `customer_email` (from Customer service)
- `seller_name`, `seller_email` (from Seller service if applicable)
- `direccion_entrega`, `ciudad_entrega`, `pais_entrega` (from Customer service)
- `fecha_pedido` (auto-set by backend)
- `monto_total` (calculated from items)
- `route_id`, `fecha_entrega_estimada` (set by Delivery service later)

**CRITICAL Business Rules**:

#### Rule 1: VISITA_VENDEDOR (Seller Visit Order)
```
IF metodo_creacion = "visita_vendedor" THEN
  - seller_id is REQUIRED (cannot be null)
  - visit_id is REQUIRED (cannot be null)
  - seller_name is REQUIRED (fetched from Seller service)
```

#### Rule 2: APP_VENDEDOR (Seller App Order)
```
IF metodo_creacion = "app_vendedor" THEN
  - seller_id is REQUIRED (cannot be null)
  - visit_id is OPTIONAL (can be null)
  - seller_name is REQUIRED (fetched from Seller service)
```

#### Rule 3: APP_CLIENTE (Customer App Order)
```
IF metodo_creacion = "app_cliente" THEN
  - seller_id MUST BE NULL
  - visit_id MUST BE NULL
```

#### Rule 4: Order Items
- Order must have at least 1 item
- Total is calculated automatically from items

---

### Entity: OrderItem

**Included in Order creation**

| Field | Type | Required | Validation Rules |
|-------|------|----------|------------------|
| `producto_id` | UUID | ✅ Yes | • Must be a valid UUID<br>• Product must exist in Catalog service |
| `cantidad` | integer | ✅ Yes | • Must be > 0<br>• Must be a positive integer |

**Additional Fields** (populated by backend):
- `inventario_id` (determined by FEFO allocation)
- `precio_unitario` (product price × 1.30 = 30% markup)
- `precio_total` (cantidad × precio_unitario)
- Product data: `product_name`, `product_sku` (denormalized)
- Warehouse data: `warehouse_id`, `warehouse_name`, `warehouse_city`, `warehouse_country` (denormalized)
- Batch data: `batch_number`, `expiration_date` (for traceability)

**Business Rules**:
1. **Quantity**: Must be positive integer (> 0)
2. **Pricing**: 30% markup applied automatically (precio_unitario = product_price × 1.30)
3. **Total Calculation**: precio_total = cantidad × precio_unitario (must match within 0.01 tolerance)
4. **FEFO Allocation**: Inventory allocated based on First Expiry, First Out

---

## 3. CATALOG MICROSERVICE

### Entity: Product

**Endpoint**: POST `/products` or POST `/products/batch`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `provider_id` | UUID | ✅ Yes | - | • Must be a valid UUID<br>• Provider must exist |
| `name` | string | ✅ Yes | 255 | • Min length: 1<br>• Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `category` | string (enum) | ✅ Yes | 100 | • Must be one of:<br>&nbsp;&nbsp;- `"medicamentos_especiales"`<br>&nbsp;&nbsp;- `"insumos_quirurgicos"`<br>&nbsp;&nbsp;- `"reactivos_diagnosticos"`<br>&nbsp;&nbsp;- `"equipos_biomedicos"`<br>&nbsp;&nbsp;- `"otros"` |
| `sku` | string | ✅ Yes | 100 | • Min length: 1<br>• Trimmed<br>• **Auto-uppercased**<br>• **Must be globally unique**<br>• Cannot be empty |
| `price` | float | ✅ Yes | Decimal(10,2) | • Must be > 0 (strictly positive)<br>• Max value: 99,999,999.99<br>• Up to 2 decimal places |

**Category Display Labels** (for UI):
- `medicamentos_especiales` → "Medicamentos Especiales"
- `insumos_quirurgicos` → "Insumos Quirúrgicos"
- `reactivos_diagnosticos` → "Reactivos Diagnósticos"
- `equipos_biomedicos` → "Equipos Biomédicos"
- `otros` → "Otros"

**Business Rules**:
1. **SKU Uniqueness**: SKU must be unique across ALL products (show error if duplicate)
2. **Price**: Must be strictly positive (> 0)
3. **Category**: Must be one of the predefined categories
4. **Provider**: Must exist in system before creating product

---

### Entity: Provider

**Endpoint**: POST `/providers`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `name` | string | ✅ Yes | 255 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `nit` | string | ✅ Yes | 50 | • Trimmed<br>• Tax ID number<br>• Cannot be empty |
| `contact_name` | string | ✅ Yes | 255 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `email` | string | ✅ Yes | 255 | • Valid email format<br>• Cannot be empty |
| `phone` | string | ✅ Yes | 50 | • Trimmed<br>• Cannot be empty |
| `address` | string | ✅ Yes | 500 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `country` | string | ✅ Yes | 100 | • Valid ISO country code (name, alpha-2, or alpha-3)<br>• Normalized to alpha-2 on backend<br>• Cannot be empty |

**Business Rules**:
1. **Country Validation**: Must be a valid ISO 3166-1 country code
2. **Email**: Must be in valid email format
3. **NIT**: No specific format validation (varies by country)

---

## 4. INVENTORY MICROSERVICE

### Entity: Warehouse

**Endpoint**: POST `/warehouses`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `name` | string | ✅ Yes | 255 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `country` | string | ✅ Yes | 100 | • Valid ISO country code (name, alpha-2, or alpha-3)<br>• Normalized to alpha-2 on backend<br>• Cannot be empty |
| `city` | string | ✅ Yes | 100 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |
| `address` | string | ✅ Yes | 500 | • Trimmed<br>• Title-cased automatically<br>• Cannot be empty |

**Business Rules**:
1. **Country Validation**: Must be a valid ISO 3166-1 country code
2. **Location Data**: Used for delivery routing and inventory allocation

---

### Entity: Inventory

**Endpoint**: POST `/inventories`

| Field | Type | Required | Max Length | Validation Rules |
|-------|------|----------|------------|------------------|
| `product_id` | UUID | ✅ Yes | - | • Must be a valid UUID<br>• Product must exist in Catalog service |
| `warehouse_id` | UUID | ✅ Yes | - | • Must be a valid UUID<br>• Warehouse must exist |
| `total_quantity` | integer | ✅ Yes | - | • Must be >= 0 (zero or positive)<br>• Cannot be negative |
| `batch_number` | string | ✅ Yes | 255 | • Trimmed<br>• **Auto-uppercased**<br>• Cannot be empty<br>• Used for traceability |
| `expiration_date` | datetime | ✅ Yes | - | • Must be a valid datetime<br>• Should be in the future (warning if past)<br>• Format: ISO 8601 |
| `product_sku` | string | ✅ Yes | 100 | • Denormalized from Catalog<br>• Must match product's SKU |
| `product_name` | string | ✅ Yes | 500 | • Denormalized from Catalog<br>• Must match product's name |
| `product_price` | float | ✅ Yes | Decimal(10,2) | • Denormalized from Catalog<br>• Must match product's price<br>• Must be > 0 |

**Additional Fields** (populated by backend):
- `reserved_quantity` (auto-set to 0 on creation)
- `warehouse_name`, `warehouse_city` (denormalized from Warehouse)

**Business Rules**:
1. **Quantity Validation**: `total_quantity` cannot be negative (>= 0)
2. **Reserved Quantity**: Automatically set to 0 on creation, updated during order allocation
3. **Batch Traceability**: Each inventory record represents a specific batch
4. **FEFO Support**: Expiration date used for First Expiry, First Out allocation
5. **Denormalization**: Product data must be provided (fetched from Catalog service by BFF)

---

## 5. CROSS-CUTTING VALIDATION PATTERNS

### Country Validation
Used in: **Seller**, **Provider**, **Warehouse**

**Accepted Formats**:
- Full country name: "United States", "Colombia", "Mexico"
- ISO Alpha-2: "US", "CO", "MX"
- ISO Alpha-3: "USA", "COL", "MEX"

**Processing**:
- Backend normalizes to Alpha-2 (2-letter code)
- API responses return full country name

**Frontend Implementation**:
```javascript
// Use a country dropdown with ISO codes
// Libraries: react-select-country, world-countries, etc.
```

---

### Email Validation
Used in: **Seller**, **Provider**

**Rules**:
- Standard RFC 5322 email format
- Must contain "@" and valid domain
- Cannot be empty

**Frontend Implementation**:
```javascript
// HTML5 input type="email"
// Or regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
```

---

### UUID Validation
Used in: All foreign key references

**Rules**:
- Must be valid UUID v4 format
- Example: `"550e8400-e29b-41d4-a716-446655440000"`

**Frontend Implementation**:
```javascript
// Regex: /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
```

---

### Decimal/Money Validation
Used in: **SalesPlan** (goal, accumulate), **Product** (price), **Inventory** (product_price)

**Rules**:
- Format: Decimal(10,2)
- Max value: 99,999,999.99
- 2 decimal places
- Most fields require > 0 (strictly positive)

**Frontend Implementation**:
```javascript
// Input type="number" step="0.01" min="0.01"
// Or use currency input libraries
```

---

### String Normalization
Applied automatically by backend, but good to mirror in frontend:

| Transform | Fields | Example |
|-----------|--------|---------|
| `.strip().title()` | Names, cities, addresses | "john doe" → "John Doe" |
| `.strip().upper()` | SKUs, batch numbers | "abc-123" → "ABC-123" |
| `.strip()` | Phone, NIT, other strings | " 123 " → "123" |

---

## 6. CONDITIONAL VALIDATION SUMMARY

### Order Creation Method (metodo_creacion)

| Creation Method | seller_id | visit_id | seller_name | Use Case |
|-----------------|-----------|----------|-------------|----------|
| `visita_vendedor` | ✅ Required | ✅ Required | ✅ Required | Order created during physical seller visit |
| `app_vendedor` | ✅ Required | ⚠️ Optional | ✅ Required | Order created by seller via their mobile app |
| `app_cliente` | ❌ Must be null | ❌ Must be null | ❌ Not applicable | Order created by customer via their app |

**Frontend Form Logic**:
```javascript
if (metodo_creacion === "visita_vendedor") {
  // Show and require: seller_id, visit_id fields
  // Validate: both must have valid UUIDs
}
else if (metodo_creacion === "app_vendedor") {
  // Show and require: seller_id field
  // Show as optional: visit_id field
  // Validate: seller_id must have valid UUID
}
else if (metodo_creacion === "app_cliente") {
  // Hide: seller_id, visit_id fields
  // Ensure: both fields are not sent or sent as null
}
```

---

## 7. FORM VALIDATION CHECKLIST

### For Each Form Field:
- [ ] Check if field is required (✅ Yes / ❌ No / ⚠️ Conditional)
- [ ] Add max length validation (if string)
- [ ] Add min/max value validation (if number)
- [ ] Add format validation (email, UUID, date, enum)
- [ ] Add custom business rules (uniqueness, cross-field validation)
- [ ] Display appropriate error messages
- [ ] Disable submit button until form is valid

### For Order Form (Special Attention):
- [ ] Implement conditional validation based on `metodo_creacion`
- [ ] Validate at least 1 item in items array
- [ ] Validate each item's `cantidad` > 0
- [ ] Ensure `seller_id`/`visit_id` rules are enforced

### For Product Form (Special Attention):
- [ ] Validate SKU uniqueness (check with backend before submit)
- [ ] Validate price > 0 (not >= 0)
- [ ] Validate category is from enum list

### For Sales Plan Form (Special Attention):
- [ ] Validate sales_period format: Q{1-4}-{YEAR}
- [ ] Validate year range: 2000-2100
- [ ] Validate goal > 0
- [ ] Do NOT include `accumulate` or `status` fields

---

## 8. ERROR MESSAGES REFERENCE

### Suggested User-Friendly Error Messages:

| Validation | Error Message |
|------------|---------------|
| Required field empty | "This field is required" |
| Invalid email | "Please enter a valid email address" |
| Invalid country | "Please select a valid country" |
| Price <= 0 | "Price must be greater than zero" |
| Quantity <= 0 | "Quantity must be at least 1" |
| Invalid UUID | "Invalid ID format" |
| SKU duplicate | "This SKU already exists in the system" |
| Invalid sales period | "Sales period must be in format Q1-2025 (Q1-Q4)" |
| Year out of range | "Year must be between 2000 and 2100" |
| Invalid creation method | "Please select a valid creation method" |
| Missing seller_id | "Seller is required for this order type" |
| Missing visit_id | "Visit ID is required for seller visits" |
| Items array empty | "Order must contain at least one item" |
| Max length exceeded | "Maximum {max} characters allowed" |
| Expiration date past | "Warning: Expiration date is in the past" |

---

## 9. ENTITY RELATIONSHIPS DIAGRAM

```
Provider (1) ----< (N) Product
Product (1) ----< (N) Inventory
Warehouse (1) ----< (N) Inventory
Seller (1) ----< (N) SalesPlan
Order (1) ----< (N) OrderItem

Order references:
  - Customer (customer_id) - external service
  - Seller (seller_id) - optional, based on metodo_creacion
  - Visit (visit_id) - optional, based on metodo_creacion

OrderItem references:
  - Product (producto_id)
  - Inventory (inventario_id)
```

---

## 10. NOTES FOR FRONTEND DEVELOPERS

1. **UUID Fields**: All ID fields are UUIDs, not integers. Use proper UUID validation.

2. **Conditional Fields**: Order form has complex conditional logic based on `metodo_creacion`. Implement with state management.

3. **Denormalization**: Some fields like `product_name`, `warehouse_city` are denormalized. Don't be confused by duplicate data.

4. **Auto-calculated Fields**: Fields like `monto_total`, `status`, `accumulate` are calculated by backend. Never send them in POST requests.

5. **Country Codes**: Store as Alpha-2 internally, display full names to users. Use a country library.

6. **Decimal Precision**: Use proper money/decimal input components. Avoid floating-point precision issues.

7. **Date Formats**: Backend expects ISO 8601 format for dates/datetimes.

8. **Enum Values**: Use exact string values (lowercase with underscores), not display labels.

9. **Batch Operations**: Products can be created in batch. Consider bulk upload forms.

10. **Form Dependencies**: Some forms require data from other services (e.g., Order needs Customer data). Use BFF or aggregate calls.

---

**Report Generated**: 2025-10-19
**Backend Repository**: proyecto-2-backend
**Microservices Covered**: Seller, Order, Catalog, Inventory
