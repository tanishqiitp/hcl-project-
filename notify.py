def simulate_notifications(accrued_points_df, customers_df):
    # Join and create simple email content strings
    df = accrued_points_df.merge(customers_df, on='customer_id', how='left')
    messages = []
    for _, r in df.iterrows():
        email = r.get('email','unknown')
        pts = r.get('accrued_points',0)
        total = customers_df.loc[customers_df['customer_id']==r['customer_id'],'total_loyalty_points'].values
        total_pts = int(total[0]) if len(total)>0 else pts
        messages.append({'customer_id':r['customer_id'],'email':email,'subject':'Your loyalty points update','body':f'Hi {r.get("first_name","Customer")}, you earned {pts} points. Your total balance is {total_pts}.'})
    return messages
