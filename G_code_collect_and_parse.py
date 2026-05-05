import numpy as np
import pandas as pd
import math

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
    
    #Process G-Code lines
    for line in lines:
        # clear the comments
        line = line.split(';')[0].strip()
        if not line: continue

        parts = line.split()
        cmd = parts[0]

        # Position calibration (G92)
        if cmd == 'G92':
            if current_path:
                paths.append({'z': z, 'points': np.array(current_path)})
                current_path = []
                is_extruding = False
            
            for p in parts[1:]:
                if p.startswith('E'):
                    try: current_e = float(p[1:])
                    except: pass
            continue

        # Movement commands (G0, G1)
        if cmd in ['G0', 'G1']:
            new_x, new_y, new_z, new_e = x, y, z, None
            
            for p in parts[1:]:
                val = float(p[1:])
                if p.startswith('X'): new_x = val
                elif p.startswith('Y'): new_y = val
                elif p.startswith('Z'): new_z = val
                elif p.startswith('E'): new_e = val
            
            # Control the z change
            if new_z != z:
                if current_path:
                    paths.append({'z': z, 'points': np.array(current_path)})
                    current_path = []
                    is_extruding = False
                z = new_z

            # Control extrusion 
            extruding_now = False
            if new_e is not None:
                if new_e > current_e: 
                    extruding_now = True
                    current_e = new_e
            
            if extruding_now:
                if not is_extruding:
                    current_path = [[x, y]] # Starting point
                    is_extruding = True
                current_path.append([new_x, new_y]) # End point
            else:
                # Travel
                if is_extruding and current_path:
                    paths.append({'z': z, 'points': np.array(current_path)})
                    current_path = []
                    is_extruding = False
            
            x, y = new_x, new_y

    # add the last path
    if current_path:
        paths.append({'z': z, 'points': np.array(current_path)})

    # Calculate the diameter
    circles = []
    
    for path in paths:
        pts = path['points']
        z_height = path['z']
        
        if len(pts) < 10: continue 
        
        if np.linalg.norm(pts[-1] - pts[0]) > 0.5: continue
        
        xs = pts[:, 0]
        ys = pts[:, 1]
        
        # Raw measurements before nozzle diam. compensation
        raw_dx = np.ptp(xs)
        raw_dy = np.ptp(ys)
        
        # +45 and -45 projections
        proj_plus = (xs + ys) / np.sqrt(2)
        raw_d_plus = np.ptp(proj_plus)
        
        proj_minus = (xs - ys) / np.sqrt(2)
        raw_d_minus = np.ptp(proj_minus)
        
        # Raw measurement statistics
        raw_measurements = np.array([raw_dx, raw_dy, raw_d_plus, raw_d_minus])
        raw_mean = np.mean(raw_measurements)
        std_d = np.std(raw_measurements)
        
        # Filter: circularity
        if raw_mean > 1.0 and (std_d / raw_mean) < 0.05:
            
            # Nozzle diam. compensation
            final_diameter = raw_mean + nozzle_diameter
            final_dx = raw_dx + nozzle_diameter
            final_dy = raw_dy + nozzle_diameter
            final_d_plus = raw_d_plus + nozzle_diameter
            final_d_minus = raw_d_minus + nozzle_diameter

            circles.append({
                'Z': z_height,
                'Diameter': final_diameter,     # Physical diameter
                'Raw_Diameter': raw_mean,       # G-code path diameter
                'Dx': final_dx,
                'Dy': final_dy,
                'D45': final_d_plus,
                'D-45': final_d_minus,
                'Center_X': np.mean(xs),
                'Center_Y': np.mean(ys),
                'Circularity_Error': std_d
            })
            
    return pd.DataFrame(circles)

#Usage of the func.
df_1 = parse_gcode_circles('PINS.gcode', 0.4)   # Positive for pins
df_2 = parse_gcode_circles('HOLES.gcode', -0.4) # Negative for holes

df_1.to_csv('PINSn.csv', index=False)
df_2.to_csv('HOLESn.csv', index=False)
# print(df.describe())
