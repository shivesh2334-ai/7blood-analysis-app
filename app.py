# Update to properly unpack the return values from the function
\n# Assuming this is the relevant section in app.py related to unpacking the values from process_uploaded_file function

try:
    result1, result2, result3, result4, result5 = process_uploaded_file(file)  # Update this line
except Exception as e:
    print(f'An error occurred: {e}')