# Supply Chain Resilience Service (Port 8006)
#### Suppliers
- `GET /suppliers` - List suppliers with filtering
  - Query params: `is_active`, `country`, `min_reliability_score`, `skip`, `limit`
- `GET /suppliers/{id}` - Get a specific supplier
- `POST /suppliers` - Create a new supplier
- `PUT /suppliers/{id}` - Update a supplier
- `DELETE /suppliers/{id}` - Delete (deactivate) a supplier

#### Purchase Orders
- `GET /purchase-orders` - List purchase orders with filtering
  - Query params: `supplier_id`, `location_id`, `status`, `order_date_from`, `order_date_to`, `skip`, `limit`
- `GET /purchase-orders/{id}` - Get a specific purchase order
- `POST /purchase-orders` - Create a new purchase order
- `PUT /purchase-orders/{id}` - Update a purchase order
- `POST /purchase-orders/{id}/receive` - Receive items for a purchase order

#### Supplier Performance
- `GET /suppliers/{supplier_id}/performance` - Get performance history for a supplier
  - Query params: `start_date`, `end_date`
- `POST /suppliers/performance` - Create a new supplier performance record

#### Supply Chain Risks
- `GET /risks` - List supply chain risks with filtering
  - Query params: `risk_type`, `severity`, `status`, `skip`, `limit`
- `GET /risks/{id}` - Get a specific risk
- `POST /risks` - Create a new supply chain risk
- `PUT /risks/{id}` - Update a supply chain risk
- `DELETE /risks/{id}` - Delete a supply chain risk