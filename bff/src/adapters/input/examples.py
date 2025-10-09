# Catalog examples
provider_create_example = {
    "name": "Tech Solutions Inc",
    "nit": "901234567",
    "contact_name": "John Smith",
    "email": "john@techsolutions.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, Suite 100",
    "country": "United States",
}

# Inventory examples
store_create_example = {
    "name": "Main Store",
    "country": "Colombia",
    "city": "Bogota",
    "address": "Calle 123 #45-67",
}

inventory_create_example = {
    "product_id": "550e8400-e29b-41d4-a716-446655440001",
    "store_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_quantity": 100,
    "reserved_quantity": 10,
    "batch_number": "BATCH001",
    "expiration_date": "2025-12-31T23:59:59Z",
}

# Order examples
order_create_example = {
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "seller_id": "550e8400-e29b-41d4-a716-446655440001",
    "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
    "route_id": "550e8400-e29b-41d4-a716-446655440003",
    "order_date": "2025-10-09T12:00:00Z",
    "destination_address": "123 Main St, City, Country",
    "creation_method": "web_client",
    "items": [
        {
            "product_id": "550e8400-e29b-41d4-a716-446655440004",
            "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
            "quantity": 2,
            "unit_price": 29.99,
        },
        {
            "product_id": "550e8400-e29b-41d4-a716-446655440006",
            "inventory_id": "550e8400-e29b-41d4-a716-446655440007",
            "quantity": 1,
            "unit_price": 15.50,
        },
    ],
}

# Seller examples
seller_create_example = {
    "name": "John Doe Sales",
    "email": "john@sales.com",
    "phone": "+1-555-0123",
    "address": "123 Sales St, New York",
}

sales_plan_create_example = {
    "seller_id": "550e8400-e29b-41d4-a716-446655440000",
    "plan_name": "Q1 2025 Sales Target",
    "target_amount": 50000.00,
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-03-31T23:59:59Z",
}
