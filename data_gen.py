import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def _dates(start, days):
    return [start + timedelta(days=int(x)) for x in range(days)]

def generate_stores(n=5):
    data = []
    for i in range(1, n+1):
        data.append({
            'store_id': f'S{i:03}',
            'store_name': f'Store {i}',
            'store_city': f'City{i%3}',
            'store_region': f'Region{(i%2)+1}',
            'opening_date': datetime(2020,1,1) + timedelta(days=30*i)
        })
    return pd.DataFrame(data)

def generate_products(n=20):
    cats = ['Electronics','Apparel','Grocery','Home']
    data = []
    for i in range(1, n+1):
        data.append({
            'product_id': f'P{i:04}',
            'product_name': f'Product {i}',
            'product_category': cats[i % len(cats)],
            'unit_price': round(5 + np.random.rand()*95,2)
        })
    return pd.DataFrame(data)

def generate_customers(n=200):
    data=[]
    for i in range(1,n+1):
        data.append({
            'customer_id': f'C{i:05}',
            'first_name': f'Cust{i}',
            'email': f'cust{i}@example.com',
            'loyalty_status': 'Bronze',
            'total_loyalty_points': 0,
            'last_purchase_date': None,
            'segment_id': None
        })
    return pd.DataFrame(data)

def generate_promotions():
    return pd.DataFrame([
        {'promotion_id':'PR001','promotion_name':'10% off Electronics','start_date':datetime.now()-timedelta(days=7),'end_date':datetime.now()+timedelta(days=7),'discount_percentage':0.10,'applicable_category':'Electronics'},
        {'promotion_id':'PR002','promotion_name':'Apparel Weekend','start_date':datetime.now()-timedelta(days=3),'end_date':datetime.now()+timedelta(days=4),'discount_percentage':0.15,'applicable_category':'Apparel'}
    ])

def generate_loyalty_rules():
    return pd.DataFrame([
        {'rule_id':1,'rule_name':'Standard Earning','points_per_unit_spend':1.0,'min_spend_threshold':0.0,'bonus_points':0},
        {'rule_id':2,'rule_name':'Big Spender Bonus','points_per_unit_spend':1.0,'min_spend_threshold':100.0,'bonus_points':50}
    ])

def generate_inventory(products, stores):
    rows=[]
    for _,p in products.iterrows():
        for _,s in stores.iterrows():
            rows.append({'store_id':s['store_id'],'product_id':p['product_id'],'current_stock_level': np.random.randint(0,50)})
    return pd.DataFrame(rows)

def generate_sales(products, stores, customers, promotions, days=7):
    start = datetime.now() - timedelta(days=days)
    headers=[]
    lines=[]
    tx_id=1
    for day in range(days):
        txs = np.random.poisson(20)
        for t in range(txs):
            cid = customers.sample(1).iloc[0]['customer_id']
            sid = stores.sample(1).iloc[0]['store_id']
            tx_date = start + timedelta(days=day, seconds=np.random.randint(0,86400))
            lines_in_tx = np.random.randint(1,4)
            total=0
            for li in range(lines_in_tx):
                prod = products.sample(1).iloc[0]
                qty = np.random.randint(1,5)
                promo = None
                # randomly apply promotion if category matches
                applicable = promotions[promotions['applicable_category']==prod['product_category']]
                if (not applicable.empty) and (np.random.rand()<0.2):
                    promo = applicable.sample(1).iloc[0]['promotion_id']
                    discount = applicable.sample(1).iloc[0]['discount_percentage']
                else:
                    discount = 0.0
                line_amount = round(prod['unit_price'] * qty * (1-discount),2)
                total += line_amount
                lines.append({'line_item_id':f'L{tx_id:07d}{li}','transaction_id':f'TX{tx_id:06d}','product_id':prod['product_id'],'promotion_id': promo,'quantity':qty,'line_item_amount':line_amount})
            headers.append({'transaction_id':f'TX{tx_id:06d}','customer_id':cid,'store_id':sid,'transaction_date':tx_date,'total_amount':round(total,2)})
            tx_id+=1
    return pd.DataFrame(headers), pd.DataFrame(lines)

def generate_all_datasets(seed=0):
    np.random.seed(seed)
    stores = generate_stores(6)
    products = generate_products(30)
    customers = generate_customers(300)
    promotions = generate_promotions()
    loyalty_rules = generate_loyalty_rules()
    inventory = generate_inventory(products, stores)
    headers, lines = generate_sales(products, stores, customers, promotions, days=7)
    return {
        'stores': stores,
        'products': products,
        'customer_details': customers,
        'promotion_details': promotions,
        'loyalty_rules': loyalty_rules,
        'inventory': inventory,
        'store_sales_header': headers,
        'store_sales_line_items': lines
    }
