# Use a base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY polybot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project
COPY . .

# Run the application
CMD ["python", "-m", "polybot.app"]
