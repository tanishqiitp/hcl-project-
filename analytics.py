import pandas as pd

def promo_effectiveness(line_items, promotions, products):
    # Join products and promotions
    df = line_items.merge(products[['product_id','product_category']], on='product_id', how='left')
    df = df.merge(promotions[['promotion_id','applicable_category']], left_on='promotion_id', right_on='promotion_id', how='left')
    # promoted vs non-promoted baseline by category
    grouped = df.groupby(['product_category','promotion_id'], dropna=False).agg(total_sales=('line_item_amount','sum'), total_qty=('quantity','sum')).reset_index()
    # compute percent lift per promotion compared to non-promoted items in same category
    baseline = grouped[grouped['promotion_id'].isna()].rename(columns={'total_sales':'baseline_sales'})[['product_category','baseline_sales']]
    merged = grouped.merge(baseline, on='product_category', how='left')
    merged['sales_pct_increase'] = ((merged['total_sales'] - merged['baseline_sales'])/merged['baseline_sales'].replace({0:pd.NA}))*100
    return merged.sort_values('sales_pct_increase', ascending=False)

def top_products(line_items, products, top_n=5):
    gp = line_items.groupby('product_id').agg(total_sales=('line_item_amount','sum'), total_qty=('quantity','sum')).reset_index()
    return gp.merge(products[['product_id','product_name']], on='product_id', how='left').sort_values('total_sales', ascending=False).head(top_n)
