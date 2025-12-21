"""Risk analysis module for detecting overtime risks."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from pydantic import BaseModel


class RiskResult(BaseModel):
    """Result of risk analysis for an employee."""

    employee_id: str
    name: str
    dept: str
    legal_work_hours: float  # 법정근로시간 (소정 - 유급휴가)
    actual_work_hours: float  # 실제근로시간 (정밀 계산)
    overtime_hours: float  # 초과근로시간
    limit_hours: float  # 월말까지 가능한 한도 (누적 기준)
    is_risk: bool  # 위험 여부
    status: str  # "위험", "정상", "법기준초과"


class RiskAnalyzer:
    """Analyzes Shiftee data to detect overtime risks."""

    def __init__(self, realtime_path: Path, payroll_path: Path):
        self.realtime_path = realtime_path
        self.payroll_path = payroll_path

    def analyze(self) -> List[RiskResult]:
        """Run the analysis."""
        logging.info("Loading Realtime Report...")
        df_real = pd.read_excel(self.realtime_path)
        
        logging.info("Loading Payroll Report...")
        # Header is at row 2 (0-indexed 2, so 3rd row)
        # Read A2 cell for date range (row 1, col 0) if possible, or usually it's in the first few rows of raw read
        # Let's read header section first
        df_pay_header = pd.read_excel(self.payroll_path, header=None, nrows=3)
        date_range_str = str(df_pay_header.iloc[1, 0]) # Assuming A2 is at iloc[1, 0]
        
        df_pay_raw = pd.read_excel(self.payroll_path, header=2)
        # Filter out rows where Name is NaN
        df_pay = df_pay_raw[df_pay_raw['이름'].notna()].copy()

        results = []
        
        # Calculate limit based on date range from file
        limit_hours = self._calculate_limit_from_range(date_range_str)
        logging.info(f"Date Range: {date_range_str} -> Limit: {limit_hours:.2f} hours")

        # Pre-calculate Payroll hours per employee
        payroll_stats = self._calculate_payroll_stats(df_pay)

        # Iterate over Realtime data (Main Employee List)
        for _, row in df_real.iterrows():
            name = row.get('직원')
            emp_id = row.get('사원번호')
            dept = row.get('본조직')
            
            if pd.isna(name):
                continue
            
            # 1. Base Metrics from Realtime
            contract_hours = self._parse_hour(row.get('소정근로시간', 0))
            paid_leave = self._parse_hour(row.get('유급휴가시간', 0))
            
            # W column: 결근, X column: 퇴근 누락
            # Assuming columns exists. If not, default to 0.
            absent_cnt = row.get('결근', 0)
            missing_out = row.get('퇴근 누락', 0)
            
            # Treat headers carefully - "결근" might be count or time string? 
            # Looking at 'shiftee데이타', '결근' seems to be a count or string "1일"?
            # Let's assume numeric count for now based on formula `*8`.
            absent_hours = self._to_float(absent_cnt) * 8
            missing_out_hours = self._to_float(missing_out) * 8

            # 2. Legal Work Hours (L) = Contract - Paid Leave
            legal_work_hours = contract_hours - paid_leave
            
            # 3. Precision Actual Work (G)
            # = Sum from Payroll + (Absent + MissingOut) * 8
            payroll_work_hours = payroll_stats.get(name, 0.0)
            
            # Add penalty/default hours for absence/missing
            # Formula: PayrollSum + Absent*8 + Missing*8
            actual_work_hours = payroll_work_hours + absent_hours + missing_out_hours
            
            # 4. Actual Overtime (O) = Actual - Legal
            # If (Actual - Legal) < 0 then 0
            overtime_hours = max(0, actual_work_hours - legal_work_hours)
            
            # 5. Risk Detection
            # "위험" if Overtime > Limit
            is_risk = overtime_hours > limit_hours
            status = "위험" if is_risk else "정상"
            
            # "법기준초과" logic: AND(Overtime<>0, Overtime>=12*4.3) roughly? 
            # Excel: IF(AND(O<>0,O>=R), "법기준초과", "") where R=12*4.3
            legal_limit_monthly = 12 * 4.3
            if overtime_hours > 0 and overtime_hours >= legal_limit_monthly:
                status = "법기준초과"
                is_risk = True

            results.append(RiskResult(
                employee_id=str(emp_id),
                name=name,
                dept=str(dept),
                legal_work_hours=legal_work_hours,
                actual_work_hours=actual_work_hours,
                overtime_hours=overtime_hours,
                limit_hours=limit_hours,
                is_risk=is_risk,
                status=status
            ))

        return results

    def _calculate_payroll_stats(self, df_pay: pd.DataFrame) -> Dict[str, float]:
        """Aggregate actual work hours from payroll data."""
        stats = {}
        
        # Columns
        # Names based on inspect:
        # '이름', '근무일정\n시작시간', '퇴근시간', '(실제)\n총 휴게시간'
        
        for name, group in df_pay.groupby('이름'):
            total_hours = 0.0
            for _, row in group.iterrows():
                # Get timestamps
                # '근무일정\n시작시간' (Planned Start)
                # '퇴근시간' (Actual End)
                planned_start = row.get('근무일정\n시작시간')
                actual_end = row.get('퇴근시간')
                actual_break_str = row.get('(실제)\n총 휴게시간')
                
                # Logic: Only calculate if we have Actual End (and Planned Start)
                if pd.notna(planned_start) and pd.notna(actual_end):
                    try:
                        # Convert to datetime if they are strings, though pandas might index them as timestamps already
                        p_start = pd.to_datetime(planned_start)
                        a_end = pd.to_datetime(actual_end)
                        
                        duration = (a_end - p_start).total_seconds() / 3600.0
                        
                        # Subtract break
                        break_hours = self._parse_hour(actual_break_str)
                        
                        work_hours = duration - break_hours
                        total_hours += work_hours
                    except Exception as e:
                        # Log error but continue
                        # logging.warning(f"Error calculating hours for {name}: {e}")
                        pass
            
            stats[name] = total_hours
            
        return stats

    def _calculate_limit_from_range(self, range_str: str) -> float:
        """Calculate limit hours based on the end date in the range string.
        
        Format example: '2025/11/01 - 2025/11/30'
        Limit = (Day of EndDate / 7) * 12
        """
        try:
            if '-' in range_str:
                # Split by ' - ' or '-'
                parts = range_str.split('-')
                end_str = parts[-1].strip()
                
                # Parse date (supporting YYYY/MM/DD or YYYY.MM.DD)
                end_str = end_str.replace('.', '/')
                end_date = pd.to_datetime(end_str)
                
                # Calculate limit
                # If it's 30th -> 30/7 * 12 = 51.42
                return (end_date.day / 7.0) * 12.0
        except Exception as e:
            logging.warning(f"Failed to parse date range '{range_str}': {e}")
            
        # Fallback to today
        return (datetime.now().day / 7.0) * 12.0

    def _parse_hour(self, val: Any) -> float:
        """Parse time string 'HH:MM' or float to hours."""
        if pd.isna(val) or val == "":
            return 0.0
        
        if isinstance(val, (int, float)):
            return float(val)
            
        if isinstance(val, str):
            # Handle 'HH:MM'
            if ':' in val:
                try:
                    h, m = val.split(':')
                    return float(h) + float(m) / 60.0
                except:
                    pass
            # Handle '30분' etc? Assuming decimal or HH:MM for now
            try:
                return float(val)
            except:
                pass
                
        # datetime.time object
        from datetime import time
        if isinstance(val, time):
            return val.hour + val.minute / 60.0
            
        return 0.0

    def _to_float(self, val: Any) -> float:
        """Convert value like '1' or '1.5' to float safely."""
        try:
            return float(val)
        except:
            return 0.0
