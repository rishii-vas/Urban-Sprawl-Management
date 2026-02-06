import pandas as pd
import random

# Configuration for wards (name, drainage, elevation, green_cover_base, impervious_base, base_pop)
wards_config = [
    ("Koramangala", "average", "low", 15, 75, 18000),
    ("Whitefield", "poor", "medium", 10, 85, 22000),
    ("Indiranagar", "good", "high", 25, 60, 12000),
    ("Jayanagar", "good", "medium", 35, 50, 9500),
    ("Bellandur", "poor", "low", 5, 95, 32000),
    ("HSR Layout", "average", "medium", 20, 70, 16000),
    ("Marathahalli", "poor", "low", 8, 90, 28000),
    ("Hebbal", "average", "low", 22, 68, 11000),
    ("Malleshwaram", "good", "high", 28, 55, 14000),
    ("Peenya", "poor", "medium", 6, 88, 20000)
]

months = [f"2024-{str(m).zfill(2)}" for m in range(1, 13)]
data = []

for ward_id, (name, drain, elev, gc_base, imp_base, pop_base) in enumerate(wards_config, 1):
    for month in months:
        # Rainfall logic (Indian monsoon cycle peaks June-Sept)
        month_num = int(month.split('-')[1])
        if 6 <= month_num <= 9:
            rainfall = random.uniform(250, 600)
        elif month_num in [5, 10]:
            rainfall = random.uniform(100, 250)
        else:
            rainfall = random.uniform(0, 80)
            
        # Slight urban changes over months
        gc = max(0, gc_base - (month_num * 0.1))
        imp = min(100, imp_base + (month_num * 0.1))
        pop = pop_base + (month_num * 50)
        
        # Stress Logic Calculation
        # High rainfall + poor drainage + high impervious → High
        stress_score = (rainfall / 100)
        if drain == "poor": stress_score += 3
        if drain == "average": stress_score += 1.5
        if imp > 80: stress_score += 2
        if elev == "low": stress_score += 2

        if stress_score > 7:
            stress = "High"
        elif stress_score > 4:
            stress = "Medium"
        else:
            stress = "Low"

        # Proxies for stress
        complaints = int(stress_score * random.uniform(10, 30))
        floods = int(max(0, (stress_score - 5) * random.uniform(1, 4))) if stress != "Low" else 0

        data.append([
            ward_id, name, month, round(rainfall, 2), drain, elev, 
            round(gc, 1), round(imp, 1), int(pop), complaints, floods, stress
        ])

# Create DataFrame
columns = [
    "ward_id", "ward_name", "month", "rainfall_mm", "drainage_quality",
    "elevation_category", "green_cover_percent", "impervious_surface_percent",
    "population_density", "water_complaints_count", "flood_incidents_count", "stress_level"
]
df = pd.DataFrame(data, columns=columns)

# Display result
print(df.head(10))
# To save to a file, uncomment the line below:
df.to_csv("urban_water_stress.csv", index=False)

