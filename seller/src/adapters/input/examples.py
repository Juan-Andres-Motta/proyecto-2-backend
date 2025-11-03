seller_create_example = {
    "cognito_user_id": "550e8400-e29b-41d4-a716-446655440000",
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
            "cognito_user_id": "550e8400-e29b-41d4-a716-446655440000",
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
        "cognito_user_id": "550e8400-e29b-41d4-a716-446655440000",
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
                "cognito_user_id": "550e8400-e29b-41d4-a716-446655440000",
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

visit_create_example = {
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "fecha_visita": "2025-11-16T10:00:00-05:00",
    "notas_visita": "Follow-up on product demo",
}

visit_response_example = {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "seller_id": "550e8400-e29b-41d4-a716-446655440000",
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "fecha_visita": "2025-11-16T10:00:00-05:00",
    "status": "programada",
    "notas_visita": "Follow-up on product demo",
    "recomendaciones": None,
    "archivos_evidencia": None,
    "client_nombre_institucion": "Hospital Central",
    "client_direccion": "Calle 123 #45-67",
    "client_ciudad": "Bogotá",
    "client_pais": "Colombia",
    "created_at": "2025-11-01T15:30:00Z",
    "updated_at": "2025-11-01T15:30:00Z",
}

visit_update_status_example = {
    "status": "completada",
    "recomendaciones": "Recommend ordering 50 units of Product X for Q1",
}

visit_list_response_example = {
    "visits": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440010",
            "seller_id": "550e8400-e29b-41d4-a716-446655440000",
            "client_id": "550e8400-e29b-41d4-a716-446655440000",
            "fecha_visita": "2025-11-16T10:00:00-05:00",
            "status": "programada",
            "notas_visita": "Follow-up on product demo",
            "recomendaciones": None,
            "archivos_evidencia": None,
            "client_nombre_institucion": "Hospital Central",
            "client_direccion": "Calle 123 #45-67",
            "client_ciudad": "Bogotá",
            "client_pais": "Colombia",
            "created_at": "2025-11-01T15:30:00Z",
            "updated_at": "2025-11-01T15:30:00Z",
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440011",
            "seller_id": "550e8400-e29b-41d4-a716-446655440000",
            "client_id": "550e8400-e29b-41d4-a716-446655440001",
            "fecha_visita": "2025-11-16T14:00:00-05:00",
            "status": "programada",
            "notas_visita": "Initial visit for new client",
            "recomendaciones": None,
            "archivos_evidencia": None,
            "client_nombre_institucion": "Clínica San José",
            "client_direccion": "Carrera 7 #100-50",
            "client_ciudad": "Medellín",
            "client_pais": "Colombia",
            "created_at": "2025-11-01T15:35:00Z",
            "updated_at": "2025-11-01T15:35:00Z",
        },
    ],
    "count": 2,
}

generate_evidence_upload_url_example = {
    "filename": "visit-photo-001.jpg",
    "content_type": "image/jpeg",
}

presigned_upload_url_response_example = {
    "upload_url": "https://medisupply-evidence.s3.us-east-1.amazonaws.com/",
    "fields": {
        "key": "visits/550e8400-e29b-41d4-a716-446655440010/abc123-visit-photo-001.jpg",
        "Content-Type": "image/jpeg",
        "policy": "eyJleHBpcmF0aW9uIjogIjIwMjUtMTEtMDFUMTY6MzA6MDBaIiwgImNvbmRpdGlvbnMiOiBbeyJidWNrZXQiOiAibWVkaXN1cHBseS1ldmlkZW5jZSJ9XX0=",
        "x-amz-algorithm": "AWS4-HMAC-SHA256",
        "x-amz-credential": "AKIAIOSFODNN7EXAMPLE/20251101/us-east-1/s3/aws4_request",
        "x-amz-date": "20251101T153000Z",
        "x-amz-signature": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    },
    "s3_url": "https://medisupply-evidence.s3.us-east-1.amazonaws.com/visits/550e8400-e29b-41d4-a716-446655440010/abc123-visit-photo-001.jpg",
    "expires_at": "2025-11-01T16:30:00Z",
}

confirm_evidence_upload_example = {
    "s3_url": "https://medisupply-evidence.s3.us-east-1.amazonaws.com/visits/550e8400-e29b-41d4-a716-446655440010/abc123-visit-photo-001.jpg",
}
