# Moscow time viewer

Small web application which allows you to view the Moscow time in realtime. This app is shows only Moscow time, not time the machine.

## Devops course web application

## Run locally

### Prerequisites

- `pip3` dependecy should be installed.
  You can also check to see which version of pip3 is installed by entering: `pip3 --version`
  Python 3.4+ in most operating systems includes pip3 by default. If your python version is less than 3.4, then you should upgrade your Python version which will automatically install pip3.
  For example, you can install the latest version of Python from ActiveState (Python 3.9), which includes pip3.
- `5000` port on your system should be free

### Production ready

Gunicorn is used as a dependency for this App. 'Green Unicorn' is a Python WSGI HTTP Server for UNIX. It's a pre-fork worker model. The Gunicorn server is broadly compatible with various web frameworks, simply implemented, light on server resources, and fairly speedy. This step is making the app production ready. As well as a app architecture as well.

### Run App Scripts

Invoke next scripts from the root folder of the repository

```
cd app_python/backend
pip3 install --upgrade pip -r requirements.txt
gunicorn main:"create_flask_app()" -b 0.0.0.0:5000 --reload
```

Open `http://localhost:5000` to view app in the browser.

## Docker

### View image on Dockerhub

`0.0.1` [Image link](https://hub.docker.com/repository/docker/zalaldinov/devops-project-image)

#### Pull image locally

```
docker pull zalaldinov/devops-project-image
```

### Prerequisites

Docker CLI installed : [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Launch using docker compose up

Invoke next scripts from the root folder of the repository

```
cd app_python/backend
docker-compose up
```

## Linting

This project is linted locally using

- `hadolint` : linter for dockerfile
- `python` extension for VS code with build in linter

## Testing

To test the project you have to install `pytest` running

```
pip3 install pytest
```

Then just run

```
pytest testing
```

From `backend` folder
