def calculate_capacity(shelter):
    total_capacity = shelter.get("total_capacity", 0)
    current_occupancy = shelter.get("current_occupancy", 0)

    return total_capacity - current_occupancy
