import numpy as np
import pandas as pd
import math
import re

def parse_gcode_circles(filename, nozzle_diameter=0.0):
    """
    Extracts circular paths from the G-code file and calculates their physical diameters.

        filename: 
        nozzle_diameter (float): Compensation value to be added to the measured path diameter.
            This value is included in the summation.
                - For PINS (Pin/Outer Diameter): Positive (+) Nozzle Diameter (e.g., 0.4)
                - For HOLES (Hole/Inner Diameter): Negative (-) Nozzle Diameter (e.g., -0.4)
    
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    paths = []
    current_path = []
    
    # Printer state
    x, y, z = 0.0, 0.0, 0.0
    current_e = 0.0
    is_extruding = False
    
    # Time nominal value
    current_nominal = None

    # Processing G-Code lines 
    for line in lines:
        original_line = line.strip()
        line_clean = line.split(';')[0].strip() 
        
        # Search nominal diameter (REGEX) ---
        # "PIN" and "HOLE" word try to cach which pin or which hole
        # Ex: "PIN8", "HOLE 10", ";Printing PIN12"
        if "PIN" in original_line.upper() or "HOLE" in original_line.upper():
            # Regex: PIN and HOLE, optional blanks and other symbols like "/"
            match = re.search(r"(?:PIN|HOLE)[-_ ]?(\d+)", original_line, re.IGNORECASE)
            if match:
                try:
                    current_nominal = float(match.group(1))
                except:
                    pass
        
        if not line_clean: continue

        parts = line_clean.split()
        cmd = parts[0]

        # Movement records
        # G92: Reset
        if cmd == 'G92':
            if current_path:
                paths.append({
                    'z': z, 
                    'points': np.array(current_path), 
                    'nominal': current_nominal
                })
                current_path, is_extruding = [], False
            for p in parts[1:]:
                if p.startswith('E'):
                    try: current_e = float(p[1:])
                    except: pass
            continue

        # G0/G1: Movement
        if cmd in ['G0', 'G1']:
            new_x, new_y, new_z, new_e = x, y, z, None
            
            for p in parts[1:]:
                val = float(p[1:])
                if p.startswith('X'): new_x = val
                elif p.startswith('Y'): new_y = val
                elif p.startswith('Z'): new_z = val
                elif p.startswith('E'): new_e = val
            
            # Z change
            if new_z != z:
                if current_path:
                    paths.append({
                        'z': z, 
                        'points': np.array(current_path),
                        'nominal': current_nominal
                    })
                    current_path, is_extruding = [], False
                z = new_z

            # Controlling the Extruder state
            extruding_now = False
            if new_e is not None and new_e > current_e: 
                extruding_now = True
                current_e = new_e
            
            if extruding_now:
                if not is_extruding:
                    current_path = [[x, y]]
                    is_extruding = True
                current_path.append([new_x, new_y])
            else:
                if is_extruding and current_path:
                    paths.append({
                        'z': z, 
                        'points': np.array(current_path),
                        'nominal': current_nominal
                    })
                    current_path, is_extruding = [], False
            x, y = new_x, new_y

    # The residual path
    if current_path:
        paths.append({'z': z, 'points': np.array(current_path), 'nominal': current_nominal})

    # Calculations
    circles = []
    
    for path in paths:
        pts = path['points']
        z_height = path['z']
        nominal_val = path['nominal']
        
        if len(pts) < 10: continue 
        if np.linalg.norm(pts[-1] - pts[0]) > 0.5: continue
        
        xs = pts[:, 0]
        ys = pts[:, 1]
        
        # Ham Ölçümler
        raw_dx = np.ptp(xs)
        raw_dy = np.ptp(ys)
        
        proj_plus = (xs + ys) / np.sqrt(2)
        raw_d_plus = np.ptp(proj_plus)
        
        proj_minus = (xs - ys) / np.sqrt(2)
        raw_d_minus = np.ptp(proj_minus)
        
        raw_measurements = np.array([raw_dx, raw_dy, raw_d_plus, raw_d_minus])
        raw_mean = np.mean(raw_measurements)
        std_d = np.std(raw_measurements)
        
        # Filter: circularity
        if raw_mean > 1.0 and (std_d / raw_mean) < 0.05:
            
            # Physical diameter
            diameter = raw_mean + nozzle_diameter
            
            # Nominal diameter
            if nominal_val is not None:
                nominal_diameter = nominal_val
            else:
                nominal_diameter = round(diameter)
            
            # Nominal error
            # Measured diam. - Nominal diam.
            error_nom = diameter - nominal_diameter

            circles.append({
                'Z': z_height,
                'Nominal_Diameter': nominal_diameter,
                'Diameter': diameter,
                'Error_nom': error_nom,
                'Raw_Diameter': raw_mean,
                'Dx': raw_dx + nozzle_diameter,
                'Dy': raw_dy + nozzle_diameter,
                'Center_X': np.mean(xs),
                'Center_Y': np.mean(ys),
                'Circularity_Error': std_d
            })
            
    return pd.DataFrame(circles)

# Ex. usage (there must be 'PIN8', 'HOLE 10' in your g-code)

df_1 = parse_gcode_circles('CE6_PINS.gcode', 0.4)   # Positive for pins
df_2 = parse_gcode_circles('CE6_HOLES.gcode', -0.4) # Negative for holes

df_1.to_csv('PIN_theorical.csv', index=False)
df_2.to_csv('HOLE_theorical.csv', index=False)
