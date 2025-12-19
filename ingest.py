def ingest_to_memory(datasets):
    """Return the core tables (DataFrames) from generated datasets."""
    store_sales_header = datasets['store_sales_header']
    store_sales_line_items = datasets['store_sales_line_items']
    stores = datasets['stores']
    products = datasets['products']
    customer_details = datasets['customer_details']
    promotion_details = datasets['promotion_details']
    loyalty_rules = datasets['loyalty_rules']
    inventory = datasets['inventory']
    return store_sales_header, store_sales_line_items, stores, products, customer_details, promotion_details, loyalty_rules, inventory
