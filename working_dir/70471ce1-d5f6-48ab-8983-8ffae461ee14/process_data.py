import json

# Load the data from extracted_data.json
with open('extracted_data.json') as file:
    data = json.load(file)

# Initialize the sum of cents
cents_sum = 0

# Iterate over each element in the data
for element in data:
    # Check if the confidence parameter is less than 0.5
    if element['totalAmount']['confidenceLevel'] < 0.9:
        print("Warning: Confidence parameter is less than 0.8 for element:.")
        print(element)
        # Read the value parameter (usd) and add the cents to the sum
    cents_sum += int(element['totalAmount']['data'] * 100)

# Print the sum of cents
print(f"Sum of cents: {cents_sum} | Dollars: {cents_sum / 100}") 