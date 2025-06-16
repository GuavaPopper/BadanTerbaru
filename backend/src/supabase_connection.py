import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment variables from root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file")

# Initialize Supabase client
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Database functions - replacements for the SQLite functions in app.py
def get_all_measurements():
    supabase = get_supabase_client()
    response = supabase.table('measurements').select('*').order('timestamp', desc=True).execute()
    
    # Check for errors
    if hasattr(response, 'error') and response.error is not None:
        print(f"Error fetching measurements: {response.error}")
        return []
    
    return response.data

def get_latest_measurement():
    supabase = get_supabase_client()
    response = supabase.table('measurements').select('*').order('timestamp', desc=True).limit(1).execute()
    
    # Check for errors
    if hasattr(response, 'error') and response.error is not None:
        print(f"Error fetching latest measurement: {response.error}")
        return None
    
    return response.data[0] if response.data else None

def insert_measurement(measurement_data):
    """
    Insert a new measurement into the Supabase database
    
    Args:
        measurement_data (dict): Dictionary containing:
            - height (float)
            - shoulder_width (float)
            - chest_circumference (float)
            - waist_circumference (float)
            - timestamp (str, optional): If not provided, current time will be used
    
    Returns:
        dict: The inserted record or None if there was an error
    """
    if 'timestamp' not in measurement_data:
        measurement_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    supabase = get_supabase_client()
    response = supabase.table('measurements').insert(measurement_data).execute()
    
    # Check for errors
    if hasattr(response, 'error') and response.error is not None:
        print(f"Error inserting measurement: {response.error}")
        return None
    
    return response.data[0] if response.data else None

# You can add more functions as needed, such as:
# - delete_measurement(id)
# - update_measurement(id, data)
# - get_measurement_by_id(id)
# - get_measurements_by_date_range(start_date, end_date)

# Example usage:
if __name__ == "__main__":
    # Example: Get all measurements
    all_measurements = get_all_measurements()
    print(f"Total measurements: {len(all_measurements)}")
    
    # Example: Get latest measurement
    latest = get_latest_measurement()
    if latest:
        print(f"Latest measurement from: {latest['timestamp']}")
        print(f"Height: {latest['height']} cm")
        print(f"Shoulder width: {latest['shoulder_width']} cm")
        print(f"Chest circumference: {latest['chest_circumference']} cm")
        print(f"Waist circumference: {latest['waist_circumference']} cm")
    
    # Example: Insert a new measurement
    # new_measurement = {
    #     "height": 175.0,
    #     "shoulder_width": 45.2,
    #     "chest_circumference": 95.5,
    #     "waist_circumference": 82.3
    # }
    # result = insert_measurement(new_measurement)
    # if result:
    #     print(f"New measurement added with id: {result['id']}") 