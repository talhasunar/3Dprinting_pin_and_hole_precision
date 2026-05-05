The legends and explanations in the "data_org.xlsx" file:

no: batch number	

Outer_first: First printed line strategy.
    1= outer line printed first,
    0= inner line printed first,

infill: the infill setting(%)	

hor_exp: horizontal expansion setting (mm)

feature:
    1: pin features
    0: hole features
    
size_nominal: nominal diameters (8, 10 and 12 mm)	

size_X_gcode: calculated G-Code diameter in x direction
size_Y_gcode:	calculated G-Code diameter in y direction

size_X_measured:	measuerd diameter in x direction
size_Y_measured:	measuerd diameter in y direction

MEAN_size_gcode:	Average of G-Code diameters

MEAN_size_measured:	Average of measured diameters

ERROR_nominal_vs_gcode_mm: The error between nominal diameter and G-Code diameter
ERROR_nominal_vs_measured_mm: The error between nominal diameter and measured diameter
ERROR_real_gcode_vs_measured_mm: The error between G-Code diameter and G-Code diameter
