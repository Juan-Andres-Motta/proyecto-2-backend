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

order_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440008",
    "message": "Order created successfully",
}

orders_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440008",
            "client_id": "550e8400-e29b-41d4-a716-446655440000",
            "seller_id": "550e8400-e29b-41d4-a716-446655440001",
            "deliver_id": "550e8400-e29b-41d4-a716-446655440002",
            "route_id": "550e8400-e29b-41d4-a716-446655440003",
            "order_date": "2025-10-09T12:00:00Z",
            "status": "pending",
            "destination_address": "123 Main St, City, Country",
            "creation_method": "web_client",
            "created_at": "2025-10-09T12:00:00Z",
            "updated_at": "2025-10-09T12:00:00Z",
            "items": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440009",
                    "product_id": "550e8400-e29b-41d4-a716-446655440004",
                    "inventory_id": "550e8400-e29b-41d4-a716-446655440005",
                    "quantity": 2,
                    "unit_price": 29.99,
                    "created_at": "2025-10-09T12:00:00Z",
                    "updated_at": "2025-10-09T12:00:00Z",
                }
            ],
        }
    ],
    "total": 150,
    "page": 1,
    "size": 10,
    "has_next": True,
    "has_previous": False,
}
