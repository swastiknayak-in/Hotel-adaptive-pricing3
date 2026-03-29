MONTH_DEMAND  = {1:.5,2:.55,3:.65,4:.7,5:.75,6:.9,7:1.0,8:.95,9:.8,10:.7,11:.6,12:.85}
ROOM_DEMAND   = {'Standard':.8,'Deluxe':.75,'Suite':.5,'Family':.65}

def compute_demand_score(lead_time:int, month:int, room_type:str) -> float:
    lt   = max(0, 1 - lead_time/365)
    mf   = MONTH_DEMAND.get(month, .7)
    rd   = ROOM_DEMAND.get(room_type, .7)
    return round(.4*lt + .3*mf + .3*rd, 4)

def apply_dynamic_pricing(predicted:float, demand:float,
                           floor_pct=.85, ceil_pct=1.40) -> dict:
    dyn   = predicted * (1 + demand)
    floor = predicted * floor_pct
    ceil  = predicted * ceil_pct
    final = max(floor, min(dyn, ceil))
    return {'dynamic_price':round(dyn,2), 'price_floor':round(floor,2),
            'price_ceiling':round(ceil,2), 'final_dynamic_price':round(final,2),
            'demand_score':demand}

def recommend_room(guests:int, stay:int, traveler:str='leisure') -> str:
    if guests >= 4:    return 'Family Suite'
    if stay   >= 5:    return 'Deluxe Room'
    if traveler == 'business': return 'Premium Room'
    return 'Standard Room'
