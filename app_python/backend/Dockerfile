# We use python 3.9 image from docker hub
FROM python:3.9
# Set working directory for the project inside container
WORKDIR /backend
# Copy/update the needed libraries for the project
COPY requirements.txt /backend
RUN pip3 install --upgrade pip -r requirements.txt
# IMPORTANT: copy the contents of the folder where the Dockerfile is located to the working directory of the container
COPY . /backend
# set the port which will be used for the server
EXPOSE 5000
