# --------------------------------------------------
# Metadata Cleaner - Dockerfile
# Version: 1.0
# Author: Javier Ripoll
# Website: https://javierripoll.es
# Contact: javier@javierripoll.es
# Date: 2025-02-14
#
# Description:
# This Dockerfile sets up the Metadata Cleaner application
# using Python 3.9, Flask, and uWSGI, ensuring a secure 
# environment with a non-root user.
# --------------------------------------------------

# Use an official Python image
FROM python:3.9

# Create a non-privileged user
RUN useradd -m uwsgiuser

# Set the working directory in the container
WORKDIR /app

# Install ExifTool for metadata cleaning
RUN apt-get update && apt-get install -y libimage-exiftool-perl net-tools

# Copy project files to the container
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


# Change ownership of the files to the new user
RUN chown -R uwsgiuser:uwsgiuser /app

# Expose port 5000 for Flask
EXPOSE 5000

# Switch to non-root user
USER uwsgiuser

# Set default environment variables
ENV MAX_FILES=10
ENV MAX_FILE_SIZE_MB=50
ENV PAGE_TITLE="Metadata Cleaner"
ENV SUPPORT_MESSAGE="For support, please contact your IT Service or SATI."

# Run uWSGI with UID and master mode
CMD ["uwsgi", "--http", "0.0.0.0:5000", "--wsgi-file", "app.py", "--callable", "app", "--uid", "uwsgiuser", "--master"]
