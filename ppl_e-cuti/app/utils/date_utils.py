import numpy as np
from datetime import datetime, timedelta
from app.models.user import Holiday

def count_working_days(start_date, end_date, db):
    """Count working days excluding weekends and holidays"""
    # Generate all dates between start and end
    delta = end_date - start_date
    all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    
    # Filter out weekends (Saturday=5, Sunday=6)
    working_days = [date for date in all_dates if date.weekday() < 5]
    
    # Get all holidays
    holidays = Holiday.query.all()
    holiday_dates = [holiday.date for holiday in holidays]
    recurring_holidays = [(holiday.date.month, holiday.date.day) for holiday in holidays if holiday.is_recurring]
    
    # Remove holidays from working days
    working_days_excl_holidays = []
    for date in working_days:
        # Check if date is not a holiday
        if date not in holiday_dates and (date.month, date.day) not in recurring_holidays:
            working_days_excl_holidays.append(date)
    
    return len(working_days_excl_holidays)