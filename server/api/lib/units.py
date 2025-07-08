def convert_from_ml(val_ml, unit: str):
    unit = unit.lower()
    if unit == "ml":
        return val_ml

    if unit == "l":
        val_ml = val_ml / 1000
    elif unit == "gal":
        val_ml = val_ml * 0.0002641721
    elif unit == "gal (imperial)":
        val_ml = val_ml * 0.000219969
    elif unit == "pt":
        val_ml = val_ml * 0.0021133764
    elif unit == "p (imperial)":
        val_ml = val_ml * 0.00175975
    elif unit == "qt":
        val_ml = val_ml * 0.0010566882
    elif unit == "qt (imperial)":
        val_ml = val_ml * 0.000879877
    elif unit == "cup":
        val_ml = val_ml * 0.0042267528
    elif unit == "cup (imperial)":
        val_ml = val_ml * 0.00351951
    elif unit == "oz":
        val_ml = val_ml * 0.033814
    elif unit == "oz (imperial)":
        val_ml = val_ml * 0.0351951
    else:
        raise Exception(f"invalid volume unit for conversion: '{unit}'")
    
    return val_ml

def convert_to_ml(val, unit: str):
    unit = unit.lower()
    if unit == "ml":
        return val
    
    if unit == "l":
        val = val * 1000
    elif unit == "gal":
        val = val / 0.0002641721
    elif unit == "gal (imperial)":
        val = val / 0.000219969
    elif unit == "pt":
        val = val / 0.0021133764
    elif unit == "p (imperial)":
        val = val / 0.00175975
    elif unit == "qt":
        val = val / 0.0010566882
    elif unit == "qt (imperial)":
        val = val / 0.000879877
    elif unit == "cup":
        val = val / 0.0042267528
    elif unit == "cup (imperial)":
        val = val / 0.00351951
    elif unit == "oz":
        val = val / 0.033814
    elif unit == "oz (imperial)":
        val = val / 0.0351951
    else:
        raise Exception(f"invalid volume unit for conversion: '{unit}'")
    
    return val

def convert_to_g(val, unit:str):
    unit = unit.lower()

    if unit == "g":
        return val
    
    if unit == "oz":
        val = val * 28.349523125
    elif unit == "lb":
        val = val * 453.59237
    else:
        raise Exception(f"invalid volume unit for conversion: '{unit}'")
    
    return val

def convert_from_g(val, unit:str):
    unit = unit.lower()

    if unit == "g":
        return val
    
    if unit == "oz":
        val = val * 0.03527396195
    elif unit == "lb":
        val = val * 0.0022046226
    else:
        raise Exception(f"invalid volume unit for conversion: '{unit}'")
    
    return val