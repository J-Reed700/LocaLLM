#!/bin/bash

# Path to the app.py file
APP_FILE="app.py"

# Temporary requirements file
REQ_FILE="requirements.txt"

# Check if pipreqs is installed
if ! command -v pipreqs &> /dev/null
then
    echo "pipreqs could not be found. Installing pipreqs..."
    pip install pipreqs
    if [ $? -ne 0 ]; then
        echo "Failed to install pipreqs. Please install it manually and rerun the script."
        exit 1
    fi
fi

# Generate requirements.txt using pipreqs
echo "Generating requirements.txt from $APP_FILE..."
pipreqs . --force --ignore "$REQ_FILE"

# Remove 'typing' if present
echo "Removing 'typing' from requirements.txt if present..."
sed -i.bak '/^typing/d' "$REQ_FILE"

# Display the cleaned requirements
echo "Cleaned requirements.txt:"
cat "$REQ_FILE"

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "pyproject.toml not found. Please ensure you are in the Poetry project directory."
    exit 1
fi

# Loop through each package in requirements.txt and add it using Poetry
echo "Adding dependencies to Poetry..."
while IFS= read -r package || [ -n "$package" ]; do
    # Skip empty lines and comments
    if [[ -z "$package" || "$package" == \#* ]]; then
        continue
    fi

    # Check if the package already exists in pyproject.toml
    if poetry show "$package" &> /dev/null; then
        echo "Package '$package' is already added. Skipping..."
        continue
    fi

    echo "Adding package: $package"
    poetry add "$package"
    if [ $? -ne 0 ]; then
        echo "Failed to add package '$package'. Please add it manually."
    fi
done < "$REQ_FILE"

# Clean up temporary files
rm "$REQ_FILE.bak"

echo "All dependencies have been added successfully."

# Optional: Remove requirements.txt after adding dependencies
# rm "$REQ_FILE"