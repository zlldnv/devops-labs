# We use python 3.9 image from docker hub
FROM python:3.9
# Set working directory for the project inside container
WORKDIR /backend
# IMPORTANT: copy the contents of the folder where the Dockerfile is located to the working directory of the container
COPY . /backend
# Install/Update the needed libraries for the project
RUN pip3 install --upgrade pip -r requirements.txt
# set the port which will be used for the server
EXPOSE 5000
#gunicorn invokes in file main.py, function create_flask_app using 0.0.0.0:5000 address
CMD ["sh", "-c", "gunicorn 'main:create_flask_app()' -b 0.0.0.0:5000 --reload"]
