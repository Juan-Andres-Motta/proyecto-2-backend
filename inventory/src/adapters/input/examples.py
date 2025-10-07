store_create_example = {
    "name": "Main Store",
    "country": "Colombia",
    "city": "Bogota",
    "address": "Calle 123 #45-67",
}

store_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Store created successfully",
}

stores_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "main store",
            "country": "CO",
            "city": "bogota",
            "address": "calle 123 #45-67",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
        }
    ],
    "total": 50,
    "page": 1,
    "size": 10,
    "has_next": True,
    "has_previous": False,
}

inventory_create_example = {
    "product_id": "550e8400-e29b-41d4-a716-446655440001",
    "store_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_quantity": 100,
    "reserved_quantity": 10,
    "batch_number": "BATCH001",
    "expiration_date": "2025-12-31T23:59:59Z",
}

inventory_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "message": "Inventory created successfully",
}

inventories_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "product_id": "550e8400-e29b-41d4-a716-446655440001",
            "store_id": "550e8400-e29b-41d4-a716-446655440000",
            "total_quantity": 100,
            "reserved_quantity": 10,
            "batch_number": "BATCH001",
            "expiration_date": "2025-12-31T23:59:59Z",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
        }
    ],
    "total": 25,
    "page": 1,
    "size": 10,
    "has_next": True,
    "has_previous": False,
}
