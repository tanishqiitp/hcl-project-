import pandas as pd

def inventory_correlation(line_items, inventory, products):
    # Identify top products
    top = line_items.groupby('product_id').agg(total_sales=('line_item_amount','sum')).reset_index()
    top = top.merge(products[['product_id','product_name']], on='product_id', how='left').sort_values('total_sales', ascending=False)
    top5 = top.head(5)['product_id'].tolist()
    # For each top product calculate % days out of stock across stores (simulate days)
    inv_top = inventory[inventory['product_id'].isin(top5)]
    summary = inv_top.groupby('product_id').agg(avg_stock=('current_stock_level','mean')).reset_index()
    summary = summary.merge(products[['product_id','product_name']], on='product_id', how='left')
    # potential lost sales is a simplistic estimation: if avg stock < 5 then mark potential lost
    summary['potential_lost_sales_estimate'] = summary['avg_stock'].apply(lambda x: 0 if x>5 else 1000*(5-x))
    return summary.sort_values('potential_lost_sales_estimate', ascending=False)
