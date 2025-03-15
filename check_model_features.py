import pickle

# Load the trained model
MODEL_PATH = "lightgbm_model3.pkl"

with open(MODEL_PATH, "rb") as model_file:
    model = pickle.load(model_file)

# Print model attributes
if hasattr(model, "booster_"):
    print("Expected feature names:", model.booster_.feature_name())
    print("Number of expected features:", len(model.booster_.feature_name()))
else:
    print("The model does not have booster_ attribute. It might not be a LightGBM model.")
