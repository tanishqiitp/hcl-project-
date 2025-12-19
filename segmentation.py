import pandas as pd
from datetime import datetime

def compute_rfm_and_segments(headers, customers, ref_date=None):
    if ref_date is None:
        ref_date = datetime.now()
    headers['transaction_date'] = pd.to_datetime(headers['transaction_date'])
    rfm = headers.groupby('customer_id').agg(recency_days=('transaction_date', lambda d: (ref_date - d.max()).days), frequency=('transaction_id','nunique'), monetary=('total_amount','sum')).reset_index()
    # simple scoring: percentile based
    rfm['r_score'] = pd.qcut(rfm['recency_days'].rank(method='first'), 4, labels=[4,3,2,1]).astype(int)
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1,2,3,4]).astype(int)
    rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), 4, labels=[1,2,3,4]).astype(int)
    rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
    # simple segments
    def seg(row):
        if row['rfm_score'].startswith('4') and int(row['m_score'])>=3:
            return 'High-Spenders'
        if row['recency_days']>60:
            return 'At-Risk'
        return 'Core'
    rfm['segment'] = rfm.apply(seg, axis=1)
    # join with customer details
    return rfm.merge(customers[['customer_id','first_name','email']], on='customer_id', how='left')
