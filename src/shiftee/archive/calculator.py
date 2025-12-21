"""Calculator module to replicate the 'Calculations' sheet logic."""

import logging
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import numpy as np


class ShifteeCalculator:
    """Replicates formulas from the Excel '계산' sheet."""

    def __init__(self, realtime_df: pd.DataFrame, payroll_df: pd.DataFrame):
        self.realtime_df = realtime_df
        # Ensure correct header for payroll (assumed handled by loader or passed correctly)
        self.payroll_df = payroll_df

    def calculate_all(self, limit_date_str: str | None = None) -> pd.DataFrame:
        """Calculate all columns corresponding to the sheet."""
        
        # 0. Basic Setup
        df = self.realtime_df.copy()
        
        # B: 직원, C: 본조직
        # Ensure we have these columns
        if '직원' not in df.columns:
            logging.error("Realtime DF must have '직원' column")
            return pd.DataFrame()
            
        # 1. Pre-calculate Payroll Sum (Precise Work)
        # G Calculation helper
        payroll_stats = self._calculate_payroll_precise_hours(self.payroll_df)
        
        # 2. Vectorized Calculations
        
        # Helper to safely parse hours
        def to_hours(x):
            return self._parse_hour(x)

        # Apply parsing to relevant columns
        metric_cols = ['소정근로시간', '승인된 근로시간', '실제 근로시간', '유급휴가시간']
        for col in metric_cols:
            if col in df.columns:
                df[col] = df[col].apply(to_hours)
            else:
                df[col] = 0.0
                
        # D: 소정근로시간
        contract_hours = df['소정근로시간']
        
        # K: 유급휴가시간
        paid_leave = df['유급휴가시간']
        
        # L: 법정근로시간 = D - K
        legal_hours = contract_hours - paid_leave
        
        # H: 실제 근로시간 (단순) = Realtime['실제 근로시간'] + (결근*8) + (퇴근누락*8)
        # Note: '결근', '퇴근 누락' columns might be strings "1일" etc.
        absent_cnt = df.get('결근', 0).apply(self._to_count)
        missing_cnt = df.get('퇴근 누락', 0).apply(self._to_count)
        
        actual_hours_simple = df['실제 근로시간'] + (absent_cnt * 8) + (missing_cnt * 8)
        
        # G: 실제 근로시간 (보정) = Payroll_Sum + (결근*8) + (퇴근누락*8)
        # Map payroll sums to df by Name
        # '직원' col in Realtime matches '이름' in Payroll
        payroll_sum_series = df['직원'].map(payroll_stats).fillna(0.0)
        actual_hours_corr = payroll_sum_series + (absent_cnt * 8) + (missing_cnt * 8)
        
        # N: 실제 초과근로(보정) = IF((G-L)<0, 0, G-L)
        overtime_corr = (actual_hours_corr - legal_hours).clip(lower=0)
        
        # O: 실제 초과근로(최종)
        # Logic: IF(OR((H-L)>N, H>300), N, IF((H-L)<0, 0, H-L))
        # Part 1: (H-L)
        overtime_simple_diff = actual_hours_simple - legal_hours
        # Part 2: Condition OR(...)
        # (H-L) > N
        cond1 = overtime_simple_diff > overtime_corr
        # H > 300
        cond2 = actual_hours_simple > 300
        use_corr = cond1 | cond2
        
        # Part 3: IF((H-L)<0, 0, H-L) -> This is max(0, H-L)
        overtime_simple_floored = overtime_simple_diff.clip(lower=0)
        
        # Final O
        overtime_final = np.where(use_corr, overtime_corr, overtime_simple_floored)
        
        # P: 조기출근 합산 = N - O
        early_arrival = overtime_corr - overtime_final
        
        # Q: 법정 초과 한도 = (Day / 7) * 12
        if limit_date_str:
            limit_hours = self._calculate_limit_from_range(limit_date_str)
        else:
            limit_hours = (datetime.now().day / 7.0) * 12.0
            
        # R: 월 법규 위반 기준 = 12 * 4.3
        monthly_limit = 12 * 4.3
        
        # S: 월말까지 가능시간 = Q - O (negative -> "가능시간없음")
        # In Excel: IF((S-O)<0, "가능시간없음", S-O). Wait, formula is IF((Q-O)<0...)
        # Let's trust pure math: Limit - Overtime
        remaining = limit_hours - overtime_final
        remaining_display = np.where(remaining < 0, 0, remaining) # Or specific string if needed
        
        # U: 적정성 = IF(O > Q, "위험", "정상")
        status = np.where(overtime_final > limit_hours, "위험", "정상")
        
        # V: 법규 기준초과자 = IF(AND(O<>0, O>=R), "법기준초과", "")
        # Note: AND logic in pandas
        violation_cond = (overtime_final != 0) & (overtime_final >= monthly_limit)
        legal_violation = np.where(violation_cond, "법기준초과", "")
        
        # Construct Result DataFrame
        result_df = pd.DataFrame({
            '직원': df['직원'],
            '본조직': df.get('본조직', ''),
            '소정근로시간': contract_hours,
            '승인된 근로시간': df['승인된 근로시간'],
            '실제 근로시간(단순)': actual_hours_simple, # H
            '실제 근로시간(보정)': actual_hours_corr, # G
            '유급휴가시간': paid_leave,
            '법정근로시간': legal_hours,
            '실제 초과근로(보정)': overtime_corr, # N
            '실제 초과근로(최종)': overtime_final, # O
            '조기출근 합산': early_arrival, # P
            '법정 초과 한도': limit_hours, # Q
            '월 법규 위반 기준': monthly_limit, # R
            '월말까지 가능시간': remaining_display, # S
            '적정성': status, # U
            '법규 기준초과자': legal_violation # V
        })
        
        return result_df

    def _calculate_payroll_precise_hours(self, df_pay: pd.DataFrame) -> pd.Series:
        """Calculate G-column logic from Payroll data.
        Returns Series index by Name.
        """
        # Group by Name
        # Logic: Sum of (Actual End - Actual Start) - Break
        # Note: Need explicit column names from your files
        
        stats = {}
        # Ensure we have required columns
        # Based on previous inspection:
        # '이름', '근무일정\n시작시간', '퇴근시간', '(실제)\n총 휴게시간'
        
        required_cols = ['이름', '근무일정\n시작시간', '퇴근시간']
        # Check if cols exist, if not, try to map or fail gracefully
        available = [c for c in required_cols if c in df_pay.columns]
        if len(available) < 3:
            logging.warning(f"Payroll data missing columns. Found: {available}")
            return pd.Series()

        for name, group in df_pay.groupby('이름'):
            total_hours = 0.0
            for _, row in group.iterrows():
                p_start = row.get('근무일정\n시작시간') # Fallback if no actual start?
                # Actually for precise calculation we might need actual start/end?
                # Formula says: INT(End*1440)/1440 - INT(Start*1440)/1440
                # Let's use '출근시간' and '퇴근시간' if available, else p_start
                
                start_val = row.get('출근시간')
                if pd.isna(start_val):
                    start_val = p_start

                end_val = row.get('퇴근시간')
                break_val = row.get('(실제)\n총 휴게시간')
                
                if pd.notna(start_val) and pd.notna(end_val):
                    try:
                        s = pd.to_datetime(start_val)
                        e = pd.to_datetime(end_val)
                        
                        # Minute precision calc (Excel INT(x*1440)/1440 style)
                        # Basically truncate to minutes
                        s_min = int(s.timestamp() / 60)
                        e_min = int(e.timestamp() / 60)
                        
                        duration_hours = (e_min - s_min) / 60.0
                        
                        # Subtract break
                        b_hours = self._parse_hour(break_val)
                        
                        work = duration_hours - b_hours
                        total_hours += work
                    except:
                        pass
            stats[name] = total_hours
            
        return pd.Series(stats)

    def _parse_hour(self, val: Any) -> float:
        """Parse 'HH:MM' or float to hours."""
        if pd.isna(val) or val == "":
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            if ':' in val:
                try:
                    h, m = val.split(':')
                    return float(h) + float(m) / 60.0
                except:
                    pass
            try:
                return float(val)
            except:
                pass
        from datetime import time
        if isinstance(val, time):
            return val.hour + val.minute / 60.0
        return 0.0

    def _to_count(self, val: Any) -> float:
        """Convert '1일' or 1 to float count."""
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Extract numbers
            import re
            nums = re.findall(r"[\d\.]+", val)
            if nums:
                return float(nums[0])
        return 0.0
        
    def _calculate_limit_from_range(self, range_str: str) -> float:
        # Reusing logic from RiskAnalyzer
        try:
            if '-' in range_str:
                parts = range_str.split('-')
                end_str = parts[-1].strip()
                end_str = end_str.replace('.', '/')
                end_date = pd.to_datetime(end_str)
                return (end_date.day / 7.0) * 12.0
        except:
            pass
        return (datetime.now().day / 7.0) * 12.0
