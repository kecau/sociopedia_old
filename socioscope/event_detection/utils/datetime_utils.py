

def correct_time(time_str):
    if len(time_str) == 7:
        time_str += '-01 00:00'
    elif len(time_str) == 10:
        time_str += ' 00:00'
    elif len(time_str) == 13:
        time_str += ':00'
    
    return time_str