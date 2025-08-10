#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 재가관리책임자 교육기관 엑셀 파일 확인
xl = pd.ExcelFile('data/scraped/rftr_edu_data_20250809_230223.xlsx')
print('재가관리책임자 교육기관 엑셀 파일 시트:')
print(xl.sheet_names)

print('\n전체 데이터 요약:')
df = pd.read_excel('data/scraped/rftr_edu_data_20250809_230223.xlsx', sheet_name='전체_데이터')
print(f'총 {len(df)}개 교육기관 수집')

print('\n페이지별 데이터:')
for i in range(1, 4):
    page_df = pd.read_excel('data/scraped/rftr_edu_data_20250809_230223.xlsx', sheet_name=f'페이지_{i}')
    print(f'  페이지 {i}: {len(page_df)}개 항목')

print('\n샘플 데이터 (첫 3개 항목):')
print(df[['교육기관명', '주소']].head(3) if '교육기관명' in df.columns and '주소' in df.columns else df.head(3))