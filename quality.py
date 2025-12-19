import pandas as pd

def run_quality_checks(header, lines, products, stores):
    checks = {}
    checks['missing_product_ids_in_lines'] = int(lines['product_id'].isna().sum())
    checks['negative_line_amounts'] = int((lines['line_item_amount'] < 0).sum())
    checks['invalid_store_ids'] = int((~header['store_id'].isin(stores['store_id'])).sum())
    # header total mismatch: compare sum of lines grouped by tx to header total
    lines_sum = lines.groupby('transaction_id', as_index=False)['line_item_amount'].sum().rename(columns={'line_item_amount':'lines_total'})
    merged = header.merge(lines_sum, left_on='transaction_id', right_on='transaction_id', how='left')
    merged['diff'] = (merged['total_amount'] - merged['lines_total']).fillna(0).abs()
    checks['header_line_mismatch_count'] = int((merged['diff'] > 0.01).sum())
    return pd.Series(checks)
