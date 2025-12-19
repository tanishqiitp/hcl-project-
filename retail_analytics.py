"""
retail_analytics.py

Modular, extensible analytics base for a retail data platform.
Strictly uses only provided schemas/columns. No I/O, no visualization.
Heavy comments explain business logic and decision enablement.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1️⃣ Automated Data Ingestion & Quality Layer
def quality_layer(store_sales_header, store_sales_line_items, products, stores, customers, promotions):
    """
    Accepts DataFrames, applies sanity checks, separates clean/rejected, outputs analytics-ready sets.
    - Nulls, negative values, mismatched totals.
    - Only columns in schemas are checked.
    """
    # Check for nulls in required columns
    header_required = ['transaction_id','customer_id','store_id','transaction_date','total_amount']
    line_required = ['transaction_id','product_id','quantity','line_item_amount']
    header_nulls = store_sales_header[header_required].isnull().any(axis=1)
    line_nulls = store_sales_line_items[line_required].isnull().any(axis=1)
    # Negative values
    header_neg = store_sales_header['total_amount'] < 0
    line_neg = store_sales_line_items['line_item_amount'] < 0
    # Mismatched totals: sum of line items != header total
    line_sums = store_sales_line_items.groupby('transaction_id')['line_item_amount'].sum()
    header_mismatch = store_sales_header.set_index('transaction_id')['total_amount'] != line_sums
    header_mismatch = header_mismatch.reindex(store_sales_header['transaction_id']).fillna(True)
    # Clean = all checks pass
    clean_header = store_sales_header[~(header_nulls | header_neg | header_mismatch.values)].copy()
    clean_lines = store_sales_line_items[~(line_nulls | line_neg)].copy()
    # Rejected = any check fails
    rejected_header = store_sales_header[(header_nulls | header_neg | header_mismatch.values)].copy()
    rejected_lines = store_sales_line_items[(line_nulls | line_neg)].copy()
    return {
        'clean_header': clean_header,
        'clean_lines': clean_lines,
        'rejected_header': rejected_header,
        'rejected_lines': rejected_lines
    }

# 2️⃣ Promotion Performance Analysis (Pre / During / Post)
def promotion_analysis(store_sales_header, store_sales_line_items, promotion_details, metric='units'):
    """
    Joins sales and promotion tables, labels transactions as pre/during/post, aggregates daily units/revenue.
    metric: 'units' or 'revenue'
    Returns DataFrame with ['date','period','units_sold','revenue']
    """
    # Merge line items with header for date
    lines = store_sales_line_items.merge(store_sales_header[['transaction_id','transaction_date']], on='transaction_id', how='left')
    # For each promotion, label period
    results = []
    for _, promo in promotion_details.iterrows():
        promo_id = promo['promotion_id']
        start, end = pd.to_datetime(promo['start_date']), pd.to_datetime(promo['end_date'])
        # Label each transaction as pre/during/post
        lines['period'] = np.where(lines['transaction_date'] < start, 'pre',
                            np.where(lines['transaction_date'] > end, 'post',
                                'during'))
        # Only consider lines for this promotion's category
        # (if promotion_id matches or product in applicable_category)
        # For strictness, only use promotion_id
        promo_lines = lines[lines['promotion_id'] == promo_id].copy()
        if promo_lines.empty:
            continue
        # Aggregate daily
        daily = promo_lines.copy()
        daily['date'] = pd.to_datetime(daily['transaction_date']).dt.date
        agg = daily.groupby(['date','period']).agg(
            units_sold = ('quantity','sum'),
            revenue = ('line_item_amount','sum')
        ).reset_index()
        agg['promotion_id'] = promo_id
        agg['promotion_name'] = promo['promotion_name']
        # Metric toggle
        if metric == 'units':
            agg['value'] = agg['units_sold']
        else:
            agg['value'] = agg['revenue']
        results.append(agg)
    if results:
        return pd.concat(results, ignore_index=True)
    else:
        return pd.DataFrame(columns=['date','period','units_sold','revenue','promotion_id','promotion_name','value'])

# 3️⃣ SuperCoins Loyalty Engine
def loyalty_engine(store_sales_header, customer_details):
    """
    Rule-based loyalty system:
    - 1 SuperCoin = ₹1
    - Coins earned = 2% of transaction value, max 100 per transaction
    - Max 10% of existing coins redeemable per transaction
    - Coins expire after 1 year (assume expired coins already excluded)
    Returns DataFrame with coins earned, redeemed, updated balance per transaction.
    """
    # Copy to avoid mutating input
    customers = customer_details.set_index('customer_id').copy()
    results = []
    for _, tx in store_sales_header.iterrows():
        cid = tx['customer_id']
        txid = tx['transaction_id']
        amt = tx['total_amount']
        # Earned: 2% of value, max 100
        earned = min(int(np.floor(amt * 0.02)), 100)
        # Redeemable: max 10% of existing coins
        existing = customers.at[cid, 'total_loyalty_points'] if cid in customers.index else 0
        redeemable = min(int(np.floor(existing * 0.10)), earned)
        # Update balance
        new_balance = existing + earned - redeemable
        customers.at[cid, 'total_loyalty_points'] = new_balance
        results.append({
            'transaction_id': txid,
            'customer_id': cid,
            'coins_earned': earned,
            'coins_redeemed': redeemable,
            'updated_balance': new_balance
        })
    return pd.DataFrame(results)

# 4️⃣ Promotion Funnel (Amplitude-Style)
def promotion_funnel(store_sales_header, store_sales_line_items, promotion_details):
    """
    Behavioral funnel:
    - Eligible: customers transacting during promo window (100% baseline)
    - Reacted: purchased any promoted item
    - Purchased: purchased promoted SKU
    Returns DataFrame with absolute counts and normalized percentages.
    """
    results = []
    for _, promo in promotion_details.iterrows():
        promo_id = promo['promotion_id']
        start, end = pd.to_datetime(promo['start_date']), pd.to_datetime(promo['end_date'])
        # Eligible: customers with any transaction during window
        eligible_tx = store_sales_header[(store_sales_header['transaction_date'] >= start) & (store_sales_header['transaction_date'] <= end)]
        eligible_customers = set(eligible_tx['customer_id'])
        # Reacted: purchased any item with this promotion_id
        reacted_lines = store_sales_line_items[(store_sales_line_items['promotion_id'] == promo_id)]
        reacted_customers = set(reacted_lines.merge(store_sales_header[['transaction_id','customer_id']], on='transaction_id')['customer_id'])
        # Purchased: purchased promoted SKU (strict: promotion_id matches)
        purchased_customers = reacted_customers
        n_eligible = len(eligible_customers)
        n_reacted = len(reacted_customers & eligible_customers)
        n_purchased = n_reacted  # same as reacted in this schema
        results.append({
            'promotion_id': promo_id,
            'promotion_name': promo['promotion_name'],
            'eligible': n_eligible,
            'reacted': n_reacted,
            'purchased': n_purchased,
            'pct_reacted': (n_reacted/n_eligible*100) if n_eligible else 0,
            'pct_purchased': (n_purchased/n_eligible*100) if n_eligible else 0
        })
    return pd.DataFrame(results)

# 5️⃣ Customer Segmentation (RFM + Loyalty Overlay)
def rfm_segmentation(store_sales_header, customer_details, ref_date=None):
    """
    Computes RFM metrics, quantile-based scoring, segments:
    - High Spenders: Top 10% by Monetary
    - At-Risk: 60+ days inactive AND total_loyalty_points > 0
    Overlays loyalty as reactivation potential.
    Returns DataFrame with RFM, segment, and loyalty overlay.
    """
    if ref_date is None:
        ref_date = pd.Timestamp(datetime.now().date())
    # Recency: days since last_purchase_date
    cust = customer_details.copy()
    cust['last_purchase_date'] = pd.to_datetime(cust['last_purchase_date'])
    cust['recency'] = (ref_date - cust['last_purchase_date']).dt.days
    # Frequency, Monetary from sales
    tx = store_sales_header.groupby('customer_id').agg(
        frequency=('transaction_id','nunique'),
        monetary=('total_amount','sum')
    ).reset_index()
    cust = cust.merge(tx, on='customer_id', how='left').fillna({'frequency':0,'monetary':0})
    # Quantile scoring
    cust['m_score'] = pd.qcut(cust['monetary'].rank(method='first'), 10, labels=False, duplicates='drop')+1
    # Segments
    cust['segment'] = 'Core'
    cust.loc[cust['m_score'] >= 10, 'segment'] = 'High Spenders'
    cust.loc[(cust['recency'] > 60) & (cust['total_loyalty_points'] > 0), 'segment'] = 'At-Risk'
    # Loyalty overlay: reactivation potential
    cust['reactivation_potential'] = np.where((cust['segment']=='At-Risk') & (cust['total_loyalty_points']>0), 'High', 'Low')
    return cust[['customer_id','recency','frequency','monetary','m_score','segment','reactivation_potential','total_loyalty_points']]

# 6️⃣ Event-Driven Enhancements (Mixpanel-Inspired)
def event_log(store_sales_header, store_sales_line_items, loyalty_df, rfm_df):
    """
    Models implicit events: transaction, promotion purchase, coins earned/redeemed, inactivity crossed.
    Enables segment movement, time-to-action, funnels inside segments.
    Returns DataFrame of events.
    """
    events = []
    # Transaction events
    for _, tx in store_sales_header.iterrows():
        events.append({'customer_id':tx['customer_id'],'event':'transaction','date':tx['transaction_date'],'transaction_id':tx['transaction_id']})
    # Promotion purchase events
    promo_lines = store_sales_line_items[store_sales_line_items['promotion_id'].notnull()]
    for _, row in promo_lines.iterrows():
        events.append({'customer_id':None,'event':'promotion_purchase','date':None,'transaction_id':row['transaction_id'],'promotion_id':row['promotion_id']})
    # Coins earned/redeemed
    for _, row in loyalty_df.iterrows():
        events.append({'customer_id':row['customer_id'],'event':'coins_earned','date':None,'transaction_id':row['transaction_id'],'coins':row['coins_earned']})
        if row['coins_redeemed'] > 0:
            events.append({'customer_id':row['customer_id'],'event':'coins_redeemed','date':None,'transaction_id':row['transaction_id'],'coins':row['coins_redeemed']})
    # Inactivity threshold crossed
    for _, row in rfm_df.iterrows():
        if row['segment'] == 'At-Risk':
            events.append({'customer_id':row['customer_id'],'event':'inactivity_threshold','date':None})
    return pd.DataFrame(events)

# 7️⃣ Automated Loyalty Notification System (Simulated)
def notification_simulator(loyalty_df, rfm_df):
    """
    Simulates trigger-based notifications when loyalty points increase.
    Selects template based on segment, points earned, distance to reward, inactivity risk.
    Outputs structured logs (DataFrame).
    """
    logs = []
    for _, row in loyalty_df.iterrows():
        if row['coins_earned'] > 0:
            cust = rfm_df[rfm_df['customer_id']==row['customer_id']].iloc[0] if not rfm_df[rfm_df['customer_id']==row['customer_id']].empty else None
            segment = cust['segment'] if cust is not None else 'Unknown'
            points_earned = row['coins_earned']
            total_points = row['updated_balance']
            # Distance to next reward: e.g., next 100 coins
            dist_to_next = 100 - (total_points % 100)
            # Template selection
            if segment == 'High Spenders':
                template = 'VIP_Earned'
            elif segment == 'At-Risk':
                template = 'Reactivation_Nudge'
            else:
                template = 'Standard_Earned'
            call_to_action = f"Earn {dist_to_next} more coins for your next reward!"
            logs.append({
                'customer_id': row['customer_id'],
                'template_used': template,
                'points_earned': points_earned,
                'total_points': total_points,
                'call_to_action': call_to_action
            })
    return pd.DataFrame(logs)

# 8️⃣ Inventory & Store Performance Correlation
def inventory_risk_analysis(store_sales_header, store_sales_line_items, inventory, stores):
    """
    Uses only `inventory` (store_id, product_id, current_stock_level) and sales velocity.
    - Top 5 best-selling products (by units)
    - Avg daily sales per store–product
    - Inventory coverage: days_of_inventory_left
    - Out-of-stock risk (forecast-style)
    - Potential lost sales (estimates)
    - Store/region-level comparison
    - Risk classification

    Note: `store_sales_line_items` does not include `store_id` in the provided schema, so
    we join with `store_sales_header` to get store-level sales.
    """
    # Validate inputs
    required_inv_cols = {'store_id','product_id','current_stock_level'}
    if not required_inv_cols.issubset(set(inventory.columns)):
        missing = required_inv_cols - set(inventory.columns)
        raise ValueError(f"inventory DataFrame is missing required columns: {missing}")
    if 'store_id' not in stores.columns:
        raise ValueError("stores DataFrame must contain 'store_id' column")

    # Join header to lines to get store-level sales
    if 'store_id' not in store_sales_line_items.columns:
        if 'transaction_id' not in store_sales_header.columns:
            raise ValueError("store_sales_header must contain 'transaction_id' to join with line items")
        sales = store_sales_line_items.merge(
            store_sales_header[['transaction_id','store_id','transaction_date']],
            on='transaction_id', how='left'
        )
    else:
        sales = store_sales_line_items.copy()

    # Top 5 best-selling products (by units across all stores)
    prod_sales = sales.groupby('product_id').agg(units_sold=('quantity','sum')).reset_index()
    top5 = prod_sales.sort_values('units_sold', ascending=False).head(5)['product_id'].tolist()

    # All store-product pairs for top5 products to ensure completeness
    all_pairs = pd.MultiIndex.from_product([stores['store_id'], top5], names=['store_id','product_id']).to_frame(index=False)

    # Filter sales for top5
    sales = sales[sales['product_id'].isin(top5)].copy()

    # Estimate days in window (fallback to 7). Could be inferred from transaction_date if needed.
    days = 7

    # Group by store-product
    avg_daily = sales.groupby(['store_id','product_id']).agg(
        total_units=('quantity','sum'),
        tx_count=('transaction_id','nunique')
    ).reset_index()
    avg_daily['avg_daily_sales'] = avg_daily['total_units'] / days

    # Merge with all possible store-product pairs to ensure all store_id present
    avg_daily = all_pairs.merge(avg_daily, on=['store_id','product_id'], how='left').fillna({'total_units':0,'tx_count':0,'avg_daily_sales':0})

    # Inventory coverage: merge with inventory (store_id, product_id, current_stock_level)
    merged = avg_daily.merge(inventory[['store_id','product_id','current_stock_level']], on=['store_id','product_id'], how='left')
    merged['current_stock_level'] = merged['current_stock_level'].fillna(0)
    merged['days_of_inventory_left'] = merged['current_stock_level'] / merged['avg_daily_sales'].replace(0, np.nan)

    # Out-of-stock risk: if days_of_inventory_left < 2, critical; <5, watchlist; >20, overstocked
    def classify(x):
        if pd.isna(x): return 'Unknown'
        if x < 2: return 'Critical'
        if x < 5: return 'Watchlist'
        if x > 20: return 'Overstocked'
        return 'Safe'

    merged['risk'] = merged['days_of_inventory_left'].apply(classify)

    # Potential lost sales: if days_of_inventory_left < 1, estimate lost units as avg_daily_sales
    merged['potential_lost_units'] = np.where(merged['days_of_inventory_left'] < 1, merged['avg_daily_sales'], 0)
    merged['potential_lost_revenue'] = merged['potential_lost_units'] * merged['avg_daily_sales']

    # Store/region comparison
    merged = merged.merge(stores[['store_id','store_city','store_region']], on='store_id', how='left')

    return merged[['store_id','store_city','store_region','product_id','avg_daily_sales','current_stock_level','days_of_inventory_left','risk','potential_lost_units','potential_lost_revenue']]
