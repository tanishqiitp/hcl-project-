import pandas as pd

def calculate_loyalty_for_batch(headers, lines, customers, rules):
    # Simple points: points_per_unit_spend * total_amount + bonus if total_amount >= min_spend_threshold
    # Use rules: pick max bonus rule that applies
    points_list = []
    rules_sorted = rules.sort_values('min_spend_threshold')
    for _, h in headers.iterrows():
        txid = h['transaction_id']
        cust = h['customer_id']
        total = float(h['total_amount'])
        points = 0.0
        # use the highest applicable bonus
        applicable = rules_sorted[rules_sorted['min_spend_threshold']<=total]
        if not applicable.empty:
            rule = applicable.iloc[-1]
        else:
            rule = rules_sorted.iloc[0]
        points = total * rule['points_per_unit_spend'] + rule.get('bonus_points',0)
        points_list.append({'transaction_id':txid,'customer_id':cust,'accrued_points':int(points)})
    accrued = pd.DataFrame(points_list)
    # update customers total points (in-memory simulation)
    cust_map = customers.set_index('customer_id')['total_loyalty_points'].to_dict()
    for _, r in accrued.iterrows():
        cid = r['customer_id']
        cust_map[cid] = int(cust_map.get(cid,0) + r['accrued_points'])
    customers['total_loyalty_points'] = customers['customer_id'].map(cust_map)
    return accrued
