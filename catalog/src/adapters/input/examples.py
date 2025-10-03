provider_create_example = {
    "name": "Tech Solutions Inc",
    "nit": "901234567",
    "contact_name": "John Smith",
    "email": "john@techsolutions.com",
    "phone": "+1-555-0123",
    "address": "123 Business St, Suite 100",
    "country": "United States",
}

provider_create_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Provider created successfully",
}

providers_list_response_example = {
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "tech solutions inc",
            "nit": "901234567",
            "contact_name": "john smith",
            "email": "john@techsolutions.com",
            "phone": "+1-555-0123",
            "address": "123 business st, suite 100",
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
