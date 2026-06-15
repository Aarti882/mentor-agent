import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "callback_predictor.joblib")

class PredictiveEngine:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _generate_synthetic_data(self, num_samples=1200):
        """Generates a synthetic dataset simulating interview callback rates for Indian MCA students.
        
        Features:
        - skill_match_score: Float (0.0 to 1.0)
        - resume_opt_score: Float (0.0 to 1.0)
        - project_count: Integer (0 to 8)
        - is_product_based: Binary (1 for Product-based, 0 for Service-based)
        - is_off_campus: Binary (1 for Off-campus, 0 for On-campus)
        """
        np.random.seed(42)
        
        skill_match_score = np.random.uniform(0.1, 1.0, num_samples)
        resume_opt_score = np.random.uniform(0.2, 1.0, num_samples)
        project_count = np.random.randint(0, 7, num_samples)
        is_product_based = np.random.binomial(1, 0.4, num_samples) # 40% target product-based
        is_off_campus = np.random.binomial(1, 0.6, num_samples) # 60% hunt off-campus

        # Logic for callback probability:
        # Base logit is higher for higher skill match, resume optimization, and projects.
        # It's lower (harder) for product-based target companies and off-campus routes.
        logit = (
            -2.0 
            + 4.5 * skill_match_score 
            + 2.2 * resume_opt_score 
            + 0.4 * project_count 
            - 1.5 * is_product_based 
            - 0.9 * is_off_campus
            + 1.2 * (skill_match_score * project_count) # Interaction: projects boost skill credibility
        )
        
        # Sigmoid function to get probability
        probability = 1 / (1 + np.exp(-logit))
        
        # Generate binary label (got interview = 1, else 0)
        got_interview = np.random.binomial(1, probability)

        df = pd.DataFrame({
            'skill_match_score': skill_match_score,
            'resume_opt_score': resume_opt_score,
            'project_count': project_count,
            'is_product_based': is_product_based,
            'is_off_campus': is_off_campus,
            'got_interview': got_interview
        })
        
        return df

    def _load_or_train_model(self):
        """Loads a pre-trained model or trains a new one using synthetic data if it doesn't exist."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                return
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")

        # Train a new model
        print("Training predictive analytics model...")
        df = self._generate_synthetic_data()
        
        X = df[['skill_match_score', 'resume_opt_score', 'project_count', 'is_product_based', 'is_off_campus']]
        y = df['got_interview']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Use Random Forest for predictive scoring
        self.model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Save the model
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        print("Model trained and saved successfully.")

    def predict_callback(self, skill_match, resume_opt, projects, company_type, placement_route):
        """Predicts the probability of getting an interview callback.
        
        Parameters:
        - skill_match: float (0.0 to 1.0)
        - resume_opt: float (0.0 to 1.0)
        - projects: int (0 to 10)
        - company_type: str ('Product-based' or 'Service-based')
        - placement_route: str ('Off-campus' or 'On-campus')
        
        Returns:
        - float: probability of callback (0.0 to 100.0)
        """
        # Feature mapping
        is_product_based = 1 if company_type == 'Product-based' else 0
        is_off_campus = 1 if placement_route == 'Off-campus' else 0
        
        # Clip projects to training range maximum of 7 to avoid scale extrapolation errors
        projects_capped = min(projects, 7)
        
        features = np.array([[skill_match, resume_opt, projects_capped, is_product_based, is_off_campus]])
        
        # Predict probability
        prob = self.model.predict_proba(features)[0][1]
        
        return round(float(prob) * 100, 2)

# Singleton instance
engine = PredictiveEngine()

def get_predictive_engine():
    return engine
