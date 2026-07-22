# Database Design - DemandSense AI

## Overview
This document outlines the database schema for DemandSense AI, an AI-powered decision intelligence platform for demand forecasting and supply chain optimization. The database is designed using PostgreSQL with TimescaleDB extension for time-series data optimization.

## Database Schema Overview

### Core Entities
1. **Products & Inventory**
2. **Demand Forecasting**
3. **Inventory Management**
4. **Promotions & Pricing**
5. **Supply Chain & Suppliers**
6. **Users & Roles**
7. **Data Ingestion & Processing**
8. **Analytics & Reporting**

## Detailed Schema

### 1. Product Catalog
```sql
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES product_categories(category_id),
    brand VARCHAR(100),
    unit_of_measure VARCHAR(20),
    weight DECIMAL(10,3),
    dimensions JSONB, -- {length: float, width: float, height: float, unit: 'cm'}
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_category_id UUID REFERENCES product_categories(category_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    level INTEGER NOT NULL, -- 1=top level, 2=subcategory, etc.
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_attributes (
    attribute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    value VARCHAR(255),
    attribute_type VARCHAR(50), -- color, size, material, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_product_attributes_product ON product_attributes(product_id);
```

### 2. Inventory Management
```sql
CREATE TABLE inventory_locations (
    location_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50), -- warehouse, distribution_center, store, etc.
    address TEXT,
    city VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    capacity_units INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory_levels (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_allocated INTEGER NOT NULL DEFAULT 0, -- allocated to open orders
    quantity_available GENERATED ALWAYS AS (quantity_on_hand - quantity_allocated) STORED,
    quantity_on_order INTEGER NOT NULL DEFAULT 0, -- incoming from POs
    safety_stock INTEGER,
    reorder_point INTEGER,
    last_counted TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, location_id)
);

CREATE TABLE inventory_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50), -- receipt, issue, adjustment, transfer, etc.
    quantity_change INTEGER NOT NULL,
    reference_type VARCHAR(50), -- purchase_order, sales_order, adjustment, etc.
    reference_id UUID,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_by UUID REFERENCES users(user_id),
    notes TEXT
);

CREATE INDEX idx_inventory_levels_product_location ON inventory_levels(product_id, location_id);
CREATE INDEX idx_inventory_transactions_product ON inventory_transactions(product_id);
CREATE INDEX idx_inventory_transactions_location ON inventory_transactions(location_id);
CREATE INDEX idx_inventory_transactions_date ON inventory_transactions(transaction_date);
```

### 3. Demand Forecasting
```sql
CREATE TABLE demand_forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL, -- The date the forecast is for
    forecast_horizon INTEGER NOT NULL, -- Days ahead from forecast_date
    predicted_demand DECIMAL(10,3) NOT NULL,
    confidence_lower DECIMAL(10,3),
    confidence_upper DECIMAL(10,3),
    model_used VARCHAR(50), -- prophet, xgboost, lstm, ensemble, etc.
    model_version VARCHAR(20),
    actual_demand DECIMAL(10,3), -- Filled in when actual data becomes available
    forecast_error DECIMAL(10,3), -- Calculated when actual is known
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, location_id, forecast_date, forecast_horizon)
);

CREATE TABLE forecast_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50), -- prophet, xgboost, lstm, etc.
    version VARCHAR(20) NOT NULL,
    training_start_date DATE,
    training_end_date DATE,
    validation_start_date DATE,
    validation_end_date DATE,
    performance_metrics JSONB, -- {mae: float, rmse: float, mape: float, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE forecast_features (
    feature_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id UUID REFERENCES demand_forecasts(forecast_id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(10,4),
    feature_type VARCHAR(50), -- price, promotion, weather, holiday, etc.
    importance_score DECIMAL(3,2) -- SHAP value or similar
);

CREATE INDEX idx_demand_forecasts_product_location_date ON demand_forecasts(product_id, location_id, forecast_date);
CREATE INDEX idx_demand_forecasts_model ON demand_forecasts(model_used);
CREATE INDEX idx_forecast_features_forecast ON forecast_features(forecast_id);
```

### 4. Sales & Demand History
```sql
CREATE TABLE sales_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    quantity_sold INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    customer_type VARCHAR(50), -- retail, wholesale, online, etc.
    channel VARCHAR(50), -- store, ecommerce, marketplace, etc.
    promotion_id UUID REFERENCES promotions(promotion_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE demand_history (
    demand_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    demand_quantity DECIMAL(10,3) NOT NULL,
    demand_type VARCHAR(50), -- actual, forecast, adjusted, etc.
    source VARCHAR(50), -- pos, erp, manual, etc.
    is_holiday BOOLEAN DEFAULT FALSE,
    is_promotion BOOLEAN DEFAULT FALSE,
    temperature DECIMAL(5,2), -- for weather impact
    precipitation DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sales_transactions_product_date ON sales_transactions(product_id, transaction_date);
CREATE INDEX idx_sales_transactions_location_date ON sales_transactions(location_id, transaction_date);
CREATE INDEX idx_demand_history_product_date ON demand_history(product_id, date);
CREATE INDEX idx_demand_history_location_date ON demand_history(location_id, date);
-- Convert demand_history to hypertable for TimescaleDB
SELECT create_hypertable('demand_history', 'date');
```

### 5. Promotions & Pricing
```sql
CREATE TABLE promotions (
    promotion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    promotion_type VARCHAR(50), -- discount, bogo, coupon, etc.
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    discount_type VARCHAR(20), -- percentage, fixed_amount, etc.
    discount_value DECIMAL(5,2),
    max_uses_per_customer INTEGER,
    total_uses_limit INTEGER,
    current_uses INTEGER DEFAULT 0,
    target_products JSONB, -- Array of product_ids or category_ids
    target_locations JSONB, -- Array of location_ids
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE price_history (
    price_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE CASCADE,
    effective_date DATE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    price_type VARCHAR(20), -- regular, promotion, clearance, etc.
    promotion_id UUID REFERENCES promotions(promotion_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_promotions_dates ON promotions(start_date, end_date);
CREATE INDEX idx_price_history_product_date ON price_history(product_id, effective_date);
```

### 6. Supply Chain & Suppliers
```sql
CREATE TABLE suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    lead_time_days INTEGER,
    reliability_score DECIMAL(3,2), -- 0.00 to 1.00
    quality_score DECIMAL(3,2),
    on_time_delivery_rate DECIMAL(3,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE purchase_orders (
    po_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id UUID REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    location_id UUID REFERENCES inventory_locations(location_id) ON DELETE SET NULL,
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(20), -- draft, sent, acknowledged, partially_received, received, cancelled
    total_amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    notes TEXT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE purchase_order_items (
    po_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID REFERENCES purchase_orders(po_id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(product_id) ON DELETE CASCADE,
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL,
    received_date DATE
);

CREATE TABLE supplier_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
    evaluation_period_start DATE NOT NULL,
    evaluation_period_end DATE NOT NULL,
    on_time_delivery_rate DECIMAL(3,2),
    quality_defect_rate DECIMAL(3,2),
    average_lead_time DECIMAL(5,2),
    total_spend DECIMAL(12,2),
    order_count INTEGER,
    risk_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_order_items_po ON purchase_order_items(po_id);
```

### 7. Users & Authentication
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50), -- admin, demand_planner, inventory_manager, supply_chain_director, etc.
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB, -- Array of permission strings
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE user_roles (
    user_role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES users(user_id)
);

CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- CREATE, UPDATE, DELETE, LOGIN, etc.
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INOTimestamp WITH TIME ZONE DEFAULT NOW()
CREATE INDEX INDEX on on ();
CREATE INDEX idx_a VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_username_email ON users(username, email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX idx_audit_logs_action_timestamp ON audit_logs(action, timestamp);
```

### 8. Data Ingestion & Processing
```sql
CREATE TABLE data_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50), -- api, database, file, stream, etc.
    connection_config JSONB, -- Connection details encrypted
    is_active BOOLEAN DEFAULT TRUE,
    last_successful_sync TIMESTAMP WITH TIME ZONE,
    sync_frequency VARCHAR(20), -- realtime, hourly, daily, weekly
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE data_ingestion_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(source_id) ON DELETE SET NULL,
    ingestion_start TIMESTAMP WITH TIME ZONE NOT NULL,
    ingestion_end TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_successful INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20), -- running, success, failed, partial
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE data_quality_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50), -- null_check, range_check, uniqueness, etc.
    column_name VARCHAR(100),
    threshold_value DECIMAL(10,2),
    error_message TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_data_sources_type ON data_sources(source_type);
CREATE INDEX idx_data_ingestion_logs_source_time ON data_ingestion_logs(source_id, ingestion_start);
```

### 9. Alerts & Notifications
```sql
CREATE TABLE alert_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    condition_json JSONB NOT NULL, -- Rule definition in JSON format
    severity VARCHAR(20), -- info, warning, error, critical
    is_active BOOLEAN DEFAULT TRUE,
    notification_channels JSONB, -- email, slack, sms, etc.
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES alert_rules(rule_id) ON DELETE SET NULL,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    entity_type VARCHAR(50), -- product, inventory, forecast, etc.
    entity_id UUID,
    severity VARCHAR(20),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20), -- active, acknowledged, resolved, dismissed
    acknowledged_by UUID REFERENCES users(user_id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(user_id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

CREATE INDEX idx_alerts_rule_triggered ON alerts(rule_id, triggered_at);
CREATE INDEX idx_alerts_entity ON alerts(entity_type, entity_id);
CREATE INDEX idx_alerts_status ON alerts(status);
```

### 10. Simulation & Scenario Planning
```sql
CREATE TABLE scenarios (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    scenario_type VARCHAR(50), -- demand_shift, price_change, supply_disruption, etc.
    start_date DATE NOT NULL,
    end_date DATE,
    parameters JSONB, -- Scenario-specific parameters
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE scenario_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID REFERENCES scenarios(scenario_id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    unit VARCHAR(20),
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_scenarios_type_active ON scenarios(scenario_type, is_active);
CREATE INDEX idx_scenario_results_scenario_date ON scenario_results(scenario_id, calculation_date);
```

## Indexing Strategy
- Primary keys on all tables using UUID
- Foreign key indexes for JOIN performance
- Composite indexes for common query patterns
- TimescaleDB hypertables for time-series data (demand_history, sales_transactions)
- Partial indexes for frequently queried subsets
- Covering indexes for common SELECT queries

## Partitioning Strategy
- Large fact tables (sales_transactions, demand_history) partitioned by date (monthly)
- Inventory snapshots partitioned by month
- Consider range partitioning on date columns for audit logs

## Security Considerations
- Row-level security (RLS) for sensitive data
- Column-level security for PII
- Encryption at rest for sensitive fields
- Audit logging for all data access
- Connection pooling and statement timeout limits

## Performance Considerations
- Connection pooling with PgBouncer
- Read replicas for reporting queries
- Materialized views for aggregated metrics
- Regular vacuum and analyze maintenance
- Monitoring with pg_stat_statements

## Migration Strategy
- Use Alembic for schema migrations
- Backward-compatible changes only
- Blue-green deployment for major schema changes
- Data validation scripts for migrations
- Rollback procedures for all migrations

## Sample Queries

### 1. Get current inventory levels for a product across locations
```sql
SELECT 
    il.location_id,
    l.name as location_name,
    il.quantity_on_hand,
    il.quantity_allocated,
    il.quantity_available,
    il.safety_stock,
    il.reorder_point
FROM inventory_levels il
JOIN inventory_locations l ON il.location_id = l.location_id
WHERE il.product_id = 'product-uuid-here'
ORDER BY l.name;
```

### 2. Get demand forecast accuracy for a product
```sql
SELECT 
    df.forecast_date,
    df.predicted_demand,
    dh.demand_quantity as actual_demand,
    ABS(df.predicted_demand - dh.demand_quantity) as absolute_error,
    CASE 
        WHEN dh.demand_quantity = 0 THEN 0
        ELSE ABS(df.predicted_demand - dh.demand_quantity) / dh.demand_quantity * 100
    end as mape
FROM demand_forecasts df
JOIN demand_history dh ON df.product_id = dh.product_id 
    AND df.location_id = dh.location_id 
    AND df.forecast_date = dh.date
WHERE df.product_id = 'product-uuid-here'
    AND df.forecast_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY df.forecast_date DESC;
```

### 3. Get inventory turnover ratio by product
```sql
WITH monthly_sales AS (
    SELECT 
        product_id,
        DATE_TRUNC('month', transaction_date) as month,
        SUM(quantity_sold) as monthly_sales
    FROM sales_transactions
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY product_id, DATE_TRUNC('month', transaction_date)
),
average_inventory AS (
    SELECT 
        product_id,
        AVG(quantity_on_hand) as avg_inventory
    FROM inventory_levels
    WHERE last_updated >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY product_id
)
SELECT 
    p.product_id,
    p.sku,
    p.name as product_name,
    COALESCE(SUM(ms.monthly_sales), 0) as annual_sales,
    COALESCE(ai.avg_inventory, 0) as average_inventory,
    CASE 
        WHEN COALESCE(ai.avg_inventory, 0) = 0 THEN 0
        ELSE COALESCE(SUM(ms.monthly_sales), 0) / COALESCE(ai.avg_inventory, 0)
    end as inventory_turnover
FROM products p
LEFT JOIN monthly_sales ms ON p.product_id = ms.product_id
LEFT JOIN average_inventory ai ON p.product_id = ai.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, p.sku, p.name, ai.avg_inventory
ORDER BY inventory_turnover DESC;
```

## Maintenance Procedures

### Daily
- Check replication lag
- Monitor connection usage
- Review error logs
- Verify backup completion

### Weekly
- Analyze query performance
- Update table statistics
- Check for bloat
- Review index usage

### Monthly
- Check disk space
- Review user permissions
- Test restore procedures
- Archive old data

### Quarterly
- Capacity planning
- Security audit
- Performance benchmarking
- Disaster recovery test

## Backup Strategy
- Daily full backups
- Hourly WAL archiving
- Point-in-time recovery capability
- Cross-region replication
- Monthly backup restore testing

## Monitoring & Alerting
- Database connection count
- Query execution time (95th percentile)
- Disk usage and I/O wait
- Replication lag
- Lock wait times
- Deadlock frequency
- Backup success/failure
- Storage capacity

This schema provides a solid foundation for the DemandSense AI platform, supporting all the core functionalities outlined in the requirements while maintaining scalability, performance, and data integrity.