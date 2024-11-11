
import boto3

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')  

# Define the table
table = dynamodb.Table('Tanks')

# Function to store data
def store_data(data):
    try:
        response = table.put_item(Item=data)
        print("Data stored successfully:", response)
    except Exception as e:
        print("Error storing data:", e)

# Example data to store for testing
data = {
    "PK": "Tank#1",
    "SK": "0001",
    "TankNumber": 1,
    "Value": 45,
    "Status": "Connected",
    "timestamp": "2024-11-09T12:00:00Z"
}

# Store data
store_data(data)
