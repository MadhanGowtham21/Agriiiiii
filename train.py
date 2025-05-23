import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Define your ThingSpeak channel details
CHANNEL_ID = "2882231"
READ_API_KEY = "SZDS98NDZ0CWNLVY"


# Function to fetch real-time data from ThingSpeak
def fetch_data():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["feeds"]
        df = pd.DataFrame(data)
        df = df.rename(columns={
            'field1': 'Temperature',
            'field2': 'Humidity',
            'field3': 'Distance',
            'field4': 'Rain Level',
            'field5': 'Soil Moisture',
            'field6': 'Flame',
            'field7': 'Light',
            'field8': 'Water Level'
        })
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        # Convert columns to numeric values, forcing errors to NaN
        df['Temperature'] = pd.to_numeric(df['Temperature'], errors='coerce')
        df['Humidity'] = pd.to_numeric(df['Humidity'], errors='coerce')
        df['Distance'] = pd.to_numeric(df['Distance'], errors='coerce')
        df['Rain Level'] = pd.to_numeric(df['Rain Level'], errors='coerce')
        df['Soil Moisture'] = pd.to_numeric(df['Soil Moisture'], errors='coerce')
        df['Flame'] = pd.to_numeric(df['Flame'], errors='coerce')
        df['Light'] = pd.to_numeric(df['Light'], errors='coerce')
        df['Water Level'] = pd.to_numeric(df['Water Level'], errors='coerce')

        # Drop rows with NaN values
        df = df.dropna()

        return df
    else:
        print("Failed to fetch data from ThingSpeak")
        return None


# Function to train the machine learning model
def train_model():
    data = fetch_data()
    if data is not None:
        # Prepare features and labels
        X = data[['Temperature', 'Humidity', 'Soil Moisture', 'Rain Level', 'Water Level', 'Flame', 'Light']]

        # Assuming you want to predict irrigation need based on these features
        y = (data['Water Level'] < 50).astype(
            int)  # Example: If water level is low, irrigation is needed (1 = yes, 0 = no)

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize and train the Random Forest model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model trained. Accuracy: {accuracy * 100:.2f}%")

        # Save the trained model to disk
        joblib.dump(model, 'irrigation_model.pkl')
        print("Model saved as 'irrigation_model.pkl'")

        return model, accuracy
    else:
        print("No data available to train the model.")
        return None, None


if __name__ == "__main__":
    print("Training model...")
    model, accuracy = train_model()
    if model is not None:
        print(f"Model training completed with accuracy: {accuracy * 100:.2f}%")
    else:
        print("Model training failed.")
