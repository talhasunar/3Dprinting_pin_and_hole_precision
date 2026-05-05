import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Best model equation
def calculate_error(hor_exp, is_pin, outer_first, infill):
    Outer_first = 1.0 if outer_first else 0.0
    feature = 1.0 if is_pin else 0.0
    Error = -0.2458 \
        - (1.9016*hor_exp) \
        + (0.0512*Outer_first) \
        + (0.0029*infill) \
        + (0.0749*feature) \
        + (0.8639*(hor_exp**2)) \
        - (0.1034*hor_exp*Outer_first) \
        - (0.0014*hor_exp*infill) \
        + (3.8636*hor_exp*feature) \
        + (0.0512*(Outer_first**2)) \
        - (0.0020*Outer_first*infill) \
        - (0.1398*Outer_first*feature) \
        + (0.0017*infill*feature) \
        + (0.0749*(feature**2))
    return Error

# Plotting
def plot_2d_curves():
    he_values = np.linspace(-0.3, 0.3, 100)

    errors_hole = [calculate_error(he, False, True, 20) for he in he_values]
    errors_pin  = [calculate_error(he, True, False, 20) for he in he_values]

    plt.figure(figsize=(15, 6))

    # Left graph
    plt.subplot(1, 2, 1)
    importance_df = pd.read_excel('Data_reg_coefs.xlsx')
    importance_df = importance_df.sort_values(by='Abs', ascending=False)
    sns.barplot(x='Abs', y='Name', data=importance_df, palette='coolwarm')
    plt.xlabel('Absolute values', fontsize=16)
    plt.ylabel('Coefficients', fontsize=16)
    plt.xlim(0, 4)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.axvline(0, color='black', linewidth=1)
    plt.text(-0.8, -0.3, 'a)', fontsize=22)

    # Right graph
    plt.subplot(1, 2, 2)

    # Model curves
    plt.plot(he_values, errors_hole, linestyle='--', label='HOLE (Outer Line First)',
             color='dodgerblue', linewidth=2)
    plt.plot(he_values, errors_pin, label='PIN (Inner Line First)',
             color='tomato', linewidth=2)

    # Experimental validation scatters
    marker_map = {'P1': 's', 'P2': '^'} #printers
    color_map = {'HOLE': 'dodgerblue', 'PIN': 'tomato'}


    # Zero error line
    plt.axhline(0, color='black', linestyle='--', linewidth=1)
    plt.text(0.22, 0.02, "Zero Error", color='black', fontstyle="oblique", fontsize=10)
    plt.text(-0.085, 0.4, "(Infill is constant =20%)", color='black',
             fontstyle="oblique", fontsize=12)

    plt.xlabel("Horizontal Expansion (mm)", fontsize=16)
    plt.ylabel("Predicted nominal error (mm)", fontsize=16)
    plt.legend(loc="upper center", fontsize=11, ncol=2)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.text(-0.43, 0.63, 'b)', fontsize=22)
    plt.grid(True, which='major', alpha=0.3)

    plt.tight_layout()
    plt.savefig('Figure.jpg', dpi=600)
    plt.show()


plot_2d_curves()
