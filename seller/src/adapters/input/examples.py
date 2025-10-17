seller_create_example = {
    "name": "John Doe Sales",
    "email": "john@sales.com",
    "phone": "+1-555-0123",
    "city": "New York",
    "country": "United States",
}

seller_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Seller created successfully",
}

sellers_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "john doe sales",
            "email": "john@sales.com",
            "phone": "+1-555-0123",
            "city": "new york",
            "country": "US",
            "created_at": "2025-01-15T10:30:00Z",
            "updated_at": "2025-01-15T10:30:00Z",
        }
    ],
    "total": 150,
    "page": 1,
    "size": 10,
    "has_next": True,
    "has_previous": False,
}

sales_plan_create_example = {
    "seller_id": "550e8400-e29b-41d4-a716-446655440000",
    "sales_period": "Q1-2025",
    "goal": 10000.00,
}

sales_plan_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "seller": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "john doe sales",
        "email": "john@sales.com",
        "phone": "+1-555-0123",
        "city": "new york",
        "country": "US",
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
    },
    "sales_period": "Q1-2025",
    "goal": 10000.00,
    "accumulate": 0.00,
    "status": "in_progress",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z",
}

sales_plans_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "seller": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "john doe sales",
                "email": "john@sales.com",
                "phone": "+1-555-0123",
                "city": "new york",
                "country": "US",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:00Z",
            },
            "sales_period": "Q1-2025",
            "goal": 10000.00,
            "accumulate": 2500.00,
            "status": "in_progress",
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
