# API Design Document - DemandSense AI

## Overview
This document outlines the RESTful API design for the DemandSense AI platform. All APIs follow REST principles and return JSON responses. The API is versioned using URL versioning (/api/v1/).

## API Design Principles
1. **RESTful Resources**: Resources are nouns, not verbs
2. **HTTP Methods**: 
   - GET: Retrieve resources
   - POST: Create resources
   - PUT/PATCH: Update resources
   - DELETE: Remove resources
3. **Status Codes**: Proper HTTP status codes for all responses
4. **Authentication**: JWT Bearer tokens in Authorization header
5. **Pagination**: Limit/offset or cursor-based pagination for list endpoints
6. **Filtering**: Query parameters for filtering, sorting, and searching
7. **Versioning**: URL-based API versioning (/api/v1/)
8. **Error Handling**: Consistent error response format
9. **Rate Limiting**: Implement rate limiting to prevent abuse
10. **CORS**: Proper CORS headers for web client access

## Base URL Structure
```
https://api.demandsense.ai/api/v1/
```
For development: `http://localhost:8000/api/v1/`

## Authentication
All endpoints (except auth endpoints) require authentication:
```
Authorization: Bearer <jwt_token>
```

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": {/* resource data */},
  "meta": {/* pagination info, timestamps, etc. */}
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {/* optional detailed error information */}
  }
}
```

### Pagination Response
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 234,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## API Endpoints

### 1. Authentication Service
#### POST /auth/register
Register a new user
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string"
}
```

#### POST /auth/login
Authenticate user and return JWT token
```json
{
  "username": "string",
  "password": "string"
}
```

#### POST /auth/refresh
Refresh access token using refresh token
```json
{
  "refresh_token": "string"
}
```

#### POST /auth/logout
Logout user (invalidate token)

### 2. Product Catalog Service
#### GET /products
Get list of products with filtering and pagination
Query Parameters:
- page: int (default: 1)
- limit: int (default: 50)
- category_id: UUID
- brand: string
- is_active: boolean
- search: string (search in name, sku, description)

#### GET /products/{product_id}
Get a specific product by ID

#### POST /products
Create a new product
```json
{
  "sku": "string",
  "name": "string",
  "description": "string",
  "category_id": "uuid",
  "brand": "string",
  "unit_of_measure": "string",
  "weight": "number",
  "dimensions": {
    "length": "number",
    "width": "number", 
    "height": "number",
    "unit": "string"
  }
}
```

#### PUT /products/{product_id}
Update a product (partial updates allowed)

#### DELETE /products/{product_id}
Soft delete a product (set is_active = false)

#### GET /products/{product_id}/attributes
Get attributes for a product

#### POST /products/{product_id}/attributes
Add attribute to a product
```json
{
  "name": "string",
  "value": "string",
  "attribute_type": "string"
}
```

### 3. Inventory Management Service
#### GET /inventory
Get inventory levels with filtering
Query Parameters:
- product_id: UUID
- location_id: UUID
- min_quantity: int
- max_quantity: int
- below_reorder_point: boolean
- out_of_stock: boolean

#### GET /inventory/{inventory_id}
Get specific inventory record

#### POST /inventory/adjust
Adjust inventory levels
```json
{
  "product_id": "uuid",
  "location_id": "uuid",
  "quantity_change": "integer",
  "transaction_type": "string", // adjustment, receipt, issue, transfer
  "reference_type": "string", // purchase_order, sales_order, etc.
  "reference_id": "uuid",
  "notes": "string"
}
```

#### GET /inventory/transactions
Get inventory transaction history
Query Parameters:
- product_id: UUID
- location_id: UUID
- start_date: date
- end_date: date
- transaction_type: string
- page: int
- limit: int

### 4. Demand Forecasting Service
#### GET /forecasts
Get demand forecasts with filtering
Query Parameters:
- product_id: UUID
- location_id: UUID
- start_date: date
- end_date: date
- model_used: string
- page: int
- limit: int

#### GET /forecasts/{forecast_id}
Get specific forecast by ID

#### POST /forecasts/generate
Generate new forecasts
```json
{
  "product_ids": ["uuid"],
  "location_ids": ["uuid"], 
  "forecast_horizon": "integer", // days
  "model_type": "string", // prophet, xgboost, lstm, ensemble
  "include_external_factors": "boolean"
}
```

#### GET /forecasts/{product_id}/accuracy
Get forecast accuracy metrics for a product
Query Parameters:
- start_date: date
- end_date: date
- location_id: UUID (optional)

#### POST /models/train
Train forecasting models
```json
{
  "product_ids": ["uuid"],
  "model_types": ["prophet", "xgboost", "lstm"],
  "training_start_date": "date",
  "training_end_date": "date",
  "validation_start_date": "date",
  "validation_end_date": "date"
}
```

### 5. Sales & Demand History Service
#### GET /sales
Get sales transactions with filtering
Query Parameters:
- product_id: UUID
- location_id: UUID
- customer_type: string
- channel: string
- start_date: date
- end_date: date
- min_amount: number
- max_amount: number
- page: int
- limit: int

#### GET /sales/{transaction_id}
Get specific sales transaction

#### POST /sales/bulk
Import sales transactions in bulk
```json
{
  "transactions": [
    {
      "product_id": "uuid",
      "location_id": "uuid", 
      "date": "date",
      "quantity_sold": "integer",
      "unit_price": "number",
      "currency": "string",
      "customer_type": "string",
      "channel": "string",
      "promotion_id": "uuid"
    }
  ]
}
```

#### GET /demand-history
Get historical demand data
Query Parameters:
- product_id: UUID
- location_id: UUID
- date: date
- start_date: date
- end_date: date
- demand_type: string
- source: string

### 6. Promotions & Pricing Service
#### GET /promotions
Get promotions with filtering
Query Parameters:
- active_only: boolean
- start_date: date
- end_date: date
- promotion_type: string
- page: int
- limit: int

#### GET /promotions/{promotion_id}
Get specific promotion by ID

#### POST /promotions
Create a new promotion
```json
{
  "name": "string",
  "description": "string",
  "promotion_type": "string",
  "start_date": "date",
  "end_date": "date",
  "discount_type": "string",
  "discount_value": "number",
  "max_uses_per_customer": "integer",
  "total_uses_limit": "integer",
  "target_products": ["uuid"],
  "target_locations": ["uuid"]
}
```

#### PUT /promotions/{promotion_id}
Update a promotion

#### DELETE /promotions/{promotion_id}
Delete a promotion

#### GET /prices
Get price history with filtering
Query Parameters:
- product_id: UUID
- location_id: UUID
- effective_date: date
- start_date: date
- end_date: date
- price_type: string
- page: int
- limit: int

### 7. Supply Chain Management Service
#### GET /suppliers
Get suppliers with filtering
Query Parameters:
- is_active: boolean
- country: string
- min_reliability_score: number
- page: int
- limit: int

#### GET /suppliers/{supplier_id}
Get specific supplier by ID

#### POST /suppliers
Create a new supplier
```json
{
  "supplier_code": "string",
  "name": "string",
  "contact_person": "string",
  "email": "string",
  "phone": "string",
  "address": "string",
  "city": "string",
  "state_province": "string",
  "country": "string",
  "postal_code": "string",
  "lead_time_days": "integer"
}
```

#### GET /purchase-orders
Get purchase orders with filtering
Query Parameters:
- supplier_id: UUID
- location_id: UUID
- status: string
- order_date: date
- start_date: date
- end_date: date
- page: int
- limit: int

#### GET /purchase-orders/{po_id}
Get specific purchase order by ID

#### POST /purchase-orders
Create a new purchase order
```json
{
  "supplier_id": "uuid",
  "location_id": "uuid",
  "expected_delivery_date": "date",
  "notes": "string",
  "items": [
    {
      "product_id": "uuid",
      "quantity_ordered": "integer",
      "unit_price": "number"
    }
  ]
}
```

#### PUT /purchase-orders/{po_id}/receive
Receive items for a purchase order
```json
{
  "items": [
    {
      "po_item_id": "uuid",
      "quantity_received": "integer",
      "received_date": "date"
    }
  ]
}
```

#### GET /suppliers/{supplier_id}/performance
Get supplier performance metrics
Query Parameters:
- start_date: date
- end_date: date

### 8. Analytics & Reporting Service
#### GET /analytics/dashboard
Get dashboard metrics for homepage
Query Parameters:
- date_range: string (today, yesterday, last_7_days, last_30_days, custom)
- start_date: date (for custom range)
- end_date: date (for custom range)

#### GET /analytics/inventory-turnover
Get inventory turnover analysis
Query Parameters:
- product_id: UUID
- category_id: UUID
- time_period: string (last_30_days, last_90_days, last_year)
- location_id: UUID

#### GET /analytics/forecast-accuracy
Get forecast accuracy metrics
Query Parameters:
- product_id: UUID
- location_id: UUID
- model_type: string
- time_period: string
- start_date: date
- end_date: date

#### GET /analytics/sales-trends
Get sales trend analysis
Query Parameters:
- product_id: UUID
- category_id: UUID
- time_period: string
- location_id: UUID
- group_by: string (day, week, month)

#### POST /scenarios/create
Create a new simulation scenario
```json
{
  "name": "string",
  "description": "string",
  "scenario_type": "string",
  "start_date": "date",
  "end_date": "date",
  "parameters": {
    // Scenario-specific parameters
  }
}
```

#### GET /scenarios/{scenario_id}/results
Get results for a simulation scenario

### 9. Data Ingestion Service
#### POST /ingest/csv
Upload and process CSV file
Form Data:
- file: CSV file
- source_type: string (pos, erp, inventory, etc.)
- delimiter: string (optional, default: ",")
- has_header: boolean (optional, default: true)

#### POST /ingest/excel
Upload and process Excel file
Form Data:
- file: Excel file (.xlsx, .xls)
- source_type: string
- sheet_name: string (optional)

#### POST /ingest/api
Configure API data ingestion
```json
{
  "name": "string",
  "source_type": "string",
  "endpoint_url": "string",
  "auth_type": "string",
  "auth_config": {},
  "polling_interval": "integer", // seconds
  "headers": {},
  "query_params": {}
}
```

#### GET /ingest/sources
Get configured data sources
Query Parameters:
- source_type: string
- is_active: boolean
- page: int
- limit: int

#### GET /ingest/logs
Get ingestion logs
Query Parameters:
- source_type: string
- status: string
- start_date: date
- end_date: date
- page: int
- limit: int

#### POST /ingest/test-connection
Test connection to a data source
```json
{
  "source_type": "string",
  "connection_config": {}
}
```

### 10. Alerts & Notifications Service
#### GET /alerts
Get alerts with filtering
Query Parameters:
- status: string (active, acknowledged, resolved, dismissed)
- severity: string (info, warning, error, critical)
- entity_type: string
- entity_id: UUID
- start_date: timestamp
- end_date: timestamp
- page: int
- limit: int

#### GET /alerts/{alert_id}
Get specific alert by ID

#### POST /alerts/{alert_id}/acknowledge
Acknowledge an alert
```json
{
  "notes": "string" // optional
}
```

#### POST /alerts/{alert_id}/resolve
Resolve an alert
```json
{
  "resolution_notes": "string"
}
```

#### GET /alert-rules
Get alert rules with filtering
Query Parameters:
- is_active: boolean
- severity: string
- page: int
- limit: int

#### POST /alert-rules
Create a new alert rule
```json
{
  "name": "string",
  "description": "string",
  "condition_json": {
    // Rule definition in JSON format
  },
  "severity": "string",
  "notification_channels": ["email", "slack", "sms"]
}
```

#### PUT /alert-rules/{rule_id}
Update an alert rule

#### DELETE /alert-rules/{rule_id}
Delete an alert rule

### 11. Users & Roles Service
#### GET /users
Get users with filtering
Query Parameters:
- role: string
- is_active: boolean
- department: string
- search: string (search in name, email, username)
- page: int
- limit: int

#### GET /users/{user_id}
Get specific user by ID

#### POST /users
Create a new user
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "department": "string",
  "is_active": "boolean"
}
```

#### PUT /users/{user_id}
Update a user
```json
{
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "department": "string",
  "is_active": "boolean"
}
```

#### DELETE /users/{user_id}
Deactivate a user (soft delete)

#### POST /users/{user_id}/change-password
Change user password
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

#### GET /roles
Get all roles

#### GET /roles/{role_id}
Get specific role by ID

#### POST /roles
Create a new role
```json
{
  "role_name": "string",
  "description": "string",
  "permissions": ["string"] // array of permission strings
}
```

### 12. Health & Monitoring Endpoints
#### GET /health
Basic health check
Returns: {"status": "healthy"}

#### GET /health/detailed
Detailed health check including database, cache, external services
Returns: {
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "redis": "healthy", 
    "kafka": "healthy"
  }
}

#### GET /metrics
Prometheus metrics endpoint

#### GET /version
Get API version and build information

## Error Codes
- AUTHENTICATION_FAILED: Invalid or missing credentials
- AUTHORIZATION_FAILED: Insufficient permissions
- VALIDATION_ERROR: Input validation failed
- RESOURCE_NOT_FOUND: Requested resource not found
- RESOURCE_CONFLICT: Resource already exists or conflict
- INTERNAL_SERVER_ERROR: Unexpected server error
- SERVICE_UNAVAILABLE: Service temporarily unavailable
- RATE_LIMIT_EXCEEDED: Too many requests
- INVALID_TOKEN: Invalid or expired JWT token
- TOKEN_EXPIRED: JWT token has expired

## Security Considerations
1. All passwords must be hashed using bcrypt or similar strong hashing algorithm
2. JWT tokens should have short expiration (15-30 minutes) with refresh tokens
3. Implement rate limiting (e.g., 100 requests/minute per IP)
4. Use HTTPS in production
5. Implement input validation and sanitization
6. Use parameterized queries to prevent SQL injection
7. Implement CORS policies appropriately
8. Log security-relevant events (failed logins, access violations)
9. Regular security scanning and penetration testing
10. Keep dependencies updated

## Performance Considerations
1. Implement caching for frequently accessed data (Redis)
2. Use database indexing strategically
3. Implement pagination for list endpoints
4. Use connection pooling for database connections
5. Consider read replicas for reporting queries
6. Implement CDN for static assets
7. Use gzip compression for responses
8. Optimize database queries with EXPLAIN ANALYZE
9. Monitor slow queries and optimize accordingly
10. Consider materialized views for complex aggregations

## Versioning Strategy
- Version URL: /api/v1/
- Backward compatibility maintained within major versions
- Deprecation notices provided 6 months before removing endpoints
- Semantic versioning: MAJOR.MINOR.PATCH
- MINOR versions add new features without breaking changes
- PATCH versions contain bug fixes and security updates
- MAJOR versions may contain breaking changes

## Documentation
- Interactive API documentation using Swagger/OpenAPI
- Postman collections available for testing
- Code SDKs available for popular languages (Python, JavaScript, Java)
- Change log maintained for each version
- Deprecation policy clearly documented

## Testing Strategy
- Unit tests for all business logic
- Integration tests for API endpoints
- Contract testing between services
- Load testing for performance validation
- Security testing for vulnerabilities
- Chaos engineering for resilience testing
- Automated testing in CI/CD pipeline
- Manual exploratory testing for UX validation

## Deployment Considerations
- Blue-green deployment strategy
- Database migrations backward compatible
- Feature flags for gradual rollouts
- Health checks for load balancers
- Circuit breaker pattern for service dependencies
- Distributed tracing for monitoring
- Centralized logging and monitoring
- Auto-scaling based on metrics
- Disaster recovery procedures