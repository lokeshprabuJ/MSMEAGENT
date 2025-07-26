def calculate_roi(machine_cost: float, monthly_labor_savings: float) -> float:
    if monthly_labor_savings == 0:
        return None
    return round(machine_cost / monthly_labor_savings, 2) 
