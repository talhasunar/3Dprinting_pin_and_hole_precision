import pandas as pd
import numpy as np
import itertools
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Data
df = pd.read_excel('data_org.xlsx')

# Features list
all_features = ['Outer_first', 'infill', 'hor_exp', 'feature', 'size_nominal']
target = 'ERROR_nominal_vs_measured_mm'
y = df[target]

# Generating feature combinations
feature_combinations = []
for r in range(1, len(all_features) + 1):
    for combo in itertools.combinations(all_features, r):
        feature_combinations.append(list(combo))

print(f"Total feature combination numbers: {len(feature_combinations)}")

# Model settings, we are sweeping the model parameters with arrays
# ANN
ann_pipe = Pipeline([('scaler', StandardScaler()), ('mlp', MLPRegressor(max_iter=2000, random_state=42))])
ann_params = {
    'mlp__hidden_layer_sizes': [(64, 32),(96,48), (128, 64)], #96,48
    'mlp__activation': ['relu'],
    'mlp__alpha': [0.01, 0.05, 0.1, 0.5, 1] #0.1
}

# SVR (RBF)
svr_rbf_pipe = Pipeline([('scaler', StandardScaler()), ('svr', SVR(kernel='rbf'))])
svr_rbf_params = {
    'svr__C': [0.5, 0.75, 1, 2.5, 5], #1
    'svr__epsilon': [0.001, 0.01, 0.1], #0.01
    'svr__gamma': ['scale']
}

# XGBoost
xgb_pipe = Pipeline([('xgb', XGBRegressor(objective='reg:squarederror', random_state=42, n_jobs=1))]) # n_jobs=1 çakışmayı önler
xgb_params = {
    'xgb__n_estimators': [100, 200, 300, 400, 500], # 100
    'xgb__learning_rate': [0.075, 0.1, 0.125], # 1
    'xgb__max_depth': [2, 3, 4, 5] #2
}

# Random Forest
rf_pipe = Pipeline([('rf', RandomForestRegressor(random_state=42, n_jobs=1))])
rf_params = {
    'rf__n_estimators': [300, 400, 500], #400
    'rf__max_depth': [3, 5, 7, 9] #5
}

# Polinom Regresyon
poly_pipe = Pipeline([('poly', PolynomialFeatures()), ('linear', LinearRegression())])
poly_params = {
    'poly__degree': [2, 3, 4, 5] #2
}

model_setup = {
    'ANN': (ann_pipe, ann_params),
    'SVR': (svr_rbf_pipe, svr_rbf_params),
    'XGB': (xgb_pipe, xgb_params),
    'RF': (rf_pipe, rf_params),
    'Poly': (poly_pipe, poly_params)
}

# The main loop for models and feature combinations

kf = KFold(n_splits=5, shuffle=True, random_state=42)
global_log = []

print("\nStarting (can take some time)...")
print("-" * 60)

# Following the counter
counter = 0
total_runs = len(feature_combinations) * len(model_setup)

for features in feature_combinations:
    # select the current feature set
    X_subset = df[features]
    feature_names_str = ", ".join(features)
    feature_count = len(features)
    
    for model_name, (pipeline, params) in model_setup.items():
        counter += 1
        # print at every 10 process
        if counter % 10 == 0 or counter == 1:
            print(f"Processing: {counter}/{total_runs} | Feature number {feature_count} | Model: {model_name}")
        
        # GridSearch
        grid = GridSearchCV(pipeline, params, cv=kf, 
                            scoring='neg_root_mean_squared_error', 
                            n_jobs=-1)
        grid.fit(X_subset, y)
        
        # Save the best results
        best_rmse = -grid.best_score_
        
        # R2 calculator (with the best estimator)
        y_pred = grid.best_estimator_.predict(X_subset) 
        r2 = r2_score(y, y_pred) 
        
        log_entry = {
            'Feature_Set': feature_names_str,
            'Num_Features': feature_count,
            'Model': model_name,
            'Best_RMSE': best_rmse,
            'Best_R2_Fit': r2,
            'Best_Params': str(grid.best_params_)
        }
        global_log.append(log_entry)

# --- Results and reporting

log_df = pd.DataFrame(global_log)

# Ordering: From lowest (RMSE) to highest
sorted_log = log_df.sort_values(by='Best_RMSE', ascending=True).reset_index(drop=True)

print("\n" + "="*80)
print("Best 15 performance (Combination + Model)")
print("="*80)
print(sorted_log[['Model', 'Num_Features', 'Best_RMSE', 'Feature_Set']].head(15).to_string())

print("\n" + "="*80)
print("Successes (According to the mean RMSE)")
print("="*80)
feature_performance = log_df.groupby(['Feature_Set', 'Num_Features'])['Best_RMSE'].mean().reset_index()
feature_performance = feature_performance.sort_values(by='Best_RMSE').head(10)
print(feature_performance.to_string(index=False))

# Save to an excel worksheet
sorted_log.to_excel("all_ML_all_combinations.xlsx", index=False)
