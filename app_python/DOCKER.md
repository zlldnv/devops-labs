# Docker best practices

## **Dockerfiles**

### **Use Multi-stage Builds**

_Take advantage of multi-stage builds to create leaner, more secure Docker images._

[Multi-stage Docker builds](https://docs.docker.com/develop/develop-images/multistage-build/) allow you to break up your Dockerfiles into several stages. For example, you can have a stage for compiling and building your application, which can then be copied to subsequent stages. Since only the final stage is used to create the image, the dependencies and tools associated with building your application are discarded, leaving a lean and modular production-ready image.

Web development example:

```jsx
*# temp stage***FROM** python:3.9-slim **as** builder

**WORKDIR** /app

**ENV** PYTHONDONTWRITEBYTECODE 1
**ENV** PYTHONUNBUFFERED 1

**RUN** apt-get update && **\**
    apt-get install -y --no-install-recommends gcc

**COPY** requirements.txt .
**RUN** pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

*# final stage***FROM** python:3.9-slim

**WORKDIR** /app

**COPY** --from=builder /app/wheels /wheels
**COPY** --from=builder /app/requirements.txt .

**RUN** pip install --no-cache /wheels/*
```

In this example, the [GCC](https://gcc.gnu.org/) compiler is required for installing certain Python packages, so we added a temp, build-time stage to handle the build phase. Since the final run-time image does not contain GCC, it's much lighter and more secure.

Size comparison:

```jsx
REPOSITORY                 TAG                    IMAGE ID       CREATED          SIZE
docker-single              latest                 8d6b6a4d7fb6   16 seconds ago   259MB
docker-multi               latest                 813c2fa9b114   3 minutes ago    156MB
```

Data science example:

```jsx
*# temp stage***FROM** python:3.9 **as** builder

**RUN** pip wheel --no-cache-dir --no-deps --wheel-dir /wheels jupyter pandas

*# final stage***FROM** python:3.9-slim

**WORKDIR** /notebooks

**COPY** --from=builder /wheels /wheels
**RUN** pip install --no-cache /wheels/*
```

Size comparison:

```jsx
REPOSITORY                  TAG                   IMAGE ID       CREATED         SIZE
ds-multi                    latest                b4195deac742   2 minutes ago   357MB
ds-single                   latest                7c23c43aeda6   6 minutes ago   969MB
```

In summary, multi-stage builds can decrease the size of your production images, helping you save time and money. In addition, this will simplify your production containers. Also, due to the smaller size and simplicity, there's potentially a smaller attack surface.

### **Order Dockerfile Commands Appropriately**

_Pay close attention to the order of your Dockerfile commands to leverage layer caching._

Docker caches each step (or layer) in a particular Dockerfile to speed up subsequent builds. When a step changes, the cache will be invalidated not only for that particular step but all succeeding steps.

Example:

```jsx
**FROM** python:3.9-slim

**WORKDIR** /app

**COPY** sample.py .

**COPY** requirements.txt .

**RUN** pip install -r /requirements.txt
```

In this Dockerfile, we copied over the application code *before* installing the requirements. Now, each time we change *sample.py*, the build will reinstall the packages. This is very inefficient, especially when using a Docker container as a development environment. Therefore, it's crucial to keep the files that frequently change towards the end of the Dockerfile.

> You can also help prevent unwanted cache invalidations by using a .dockerignore file to exclude unnecessary files from being added to the Docker build context and the final image. More on this here shortly.

So, in the above Dockerfile, you should move the `COPY sample.py .` command to the bottom:

```jsx
**FROM** python:3.9-slim

**WORKDIR** /app

**COPY** requirements.txt .

**RUN** pip install -r /requirements.txt

**COPY** sample.py .
```

Notes:

1. Always put layers that are likely to change as low as possible in the Dockerfile.
2. Combine `RUN apt-get update` and `RUN apt-get install` commands. (This also helps to reduce the image size. We'll touch on this shortly.)
3. If you want to turn off caching for a particular Docker build, add the `-no-cache=True` flag.

### **Use Small Docker Base Images**

_Smaller Docker images are more modular and secure._

Building, pushing, and pulling images is quicker with smaller images. They also tend to be more secure since they only include the necessary libraries and system dependencies required for running your application.

_Which Docker base image should you use?_

Unfortunately, it depends.

Here's a size comparison of various Docker base images for Python:

```jsx
REPOSITORY   TAG                 IMAGE ID       CREATED      SIZE
python       3.9.6-alpine3.14    f773016f760e   3 days ago   45.1MB
python       3.9.6-slim          907fc13ca8e7   3 days ago   115MB
python       3.9.6-slim-buster   907fc13ca8e7   3 days ago   115MB
python       3.9.6               cba42c28d9b8   3 days ago   886MB
python       3.9.6-buster        cba42c28d9b8   3 days ago   886MB
```

While the Alpine flavor, based on [Alpine Linux](https://www.alpinelinux.org/), is the smallest, it can often lead to increased build times if you can't find compiled binaries that work with it. As a result, you may end up having to build the binaries yourself, which can increase the image size (depending on the required system-level dependencies) and the build times (due to having to compile from the source).

> Refer to The best Docker base image for your Python application and Using Alpine can make Python Docker builds 50× slower for more on why it's best to avoid using Alpine-based base images.

In the end, it's all about balance. When in doubt, start with a `*-slim` flavor, especially in development mode, as you're building your application. You want to avoid having to continually update the Dockerfile to install necessary system-level dependencies when you add a new Python package. As you harden your application and Dockerfile(s) for production, you may want to explore using Alpine for the final image from a multi-stage build.

> Also, don't forget to update your base images regularly to improve security and boost performance. When a new version of a base image is released -- i.e., 3.9.6-slim -> 3.9.7-slim -- you should pull the new image and update your running containers to get all the latest security patches.

### **Minimize the Number of Layers**

It's a good idea to combine the `RUN`, `COPY`, and `ADD` commands as much as possible since they create layers. Each layer increases the size of the image since they are cached. Therefore, as the number of layers increases, the size also increases.

You can test this out with the `docker history` command:

```jsx
$ docker images
REPOSITORY   TAG       IMAGE ID       CREATED          SIZE
dockerfile   latest    180f98132d02   51 seconds ago   259MB

$ docker history 180f98132d02

IMAGE          CREATED              CREATED BY                                      SIZE      COMMENT
180f98132d02   58 seconds ago       COPY . . *# buildkit                             6.71kB    buildkit.dockerfile.v0*
<missing>      58 seconds ago       RUN /bin/sh -c pip install -r requirements.t…   35.5MB    buildkit.dockerfile.v0
<missing>      About a minute ago   COPY requirements.txt . *# buildkit              58B       buildkit.dockerfile.v0*
<missing>      About a minute ago   WORKDIR /app
...
```

Take note of the sizes. Only the `RUN`, `COPY`, and `ADD` commands add size to the image. You can reduce the image size by combining commands wherever possible. For example:

```jsx
**RUN** apt-get update
**RUN** apt-get install -y netcat
```

Can be combined into a single `RUN` command:

```jsx
**RUN** apt-get update && apt-get install -y netcat
```

Thus, creating a single layer instead of two, which reduces the size of the final image.

While it's a good idea to reduce the number of layers, it's much more important for that to be less of a goal in itself and more a side-effect of reducing the image size and build times. In other words, focus more on the previous three practices -- multi-stage builds, order of your Dockerfile commands, and using a small base image -- than trying to optimize every single command.

Notes:

1. `RUN`, `COPY`, and `ADD` each create layers.
2. Each layer contains the differences from the previous layer.
3. Layers increase the size of the final image.

Tips:

1. Combine related commands.
2. Remove unnecessary files in the same RUN `step` that created them.
3. Minimize the number of times `apt-get upgrade` is run since it upgrades all packages to the latest version.
4. With multi-stage builds, don't worry too much about overly optimizing the commands in temp stages.

Finally, for readability, it's a good idea to sort multi-line arguments alphanumerically:

```jsx
**RUN** apt-get update && apt-get install -y **\**
    git **\**
    gcc **\**
    matplotlib **\**
    pillow  **\**&& rm -rf /var/lib/apt/lists/*
```

### **Use Unprivileged Containers**

By default, Docker runs container processes as root inside of a container. However, this is a bad practice since a process running as root inside the container is running as root in the Docker host. Thus, if an attacker gains access to your container, they have access to all the root privileges and can perform several attacks against the Docker host, like-

1. copying sensitive info from the host's filesystem to the container
2. executing remote commands

To prevent this, make sure to run container processes with a non-root user:

```jsx
**RUN** addgroup --system app && adduser --system --group app

**USER** app
```

You can take it a step further and remove shell access and ensure there's no home directory as well:

```jsx
**RUN** addgroup --gid 1001 --system app && **\**
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

**USER** app
```

Verify:

```jsx
$ docker run -i sample id

uid=1001(app) gid=1001(app) groups=1001(app)
```

Here, the application within the container runs under a non-root user. However, keep in mind, the Docker daemon and the container itself is still running with root privileges. Be sure to review [Run the Docker daemon as a non-root user](https://docs.docker.com/engine/security/rootless/) for help with running both the daemon and containers as a non-root user.

### **Prefer COPY Over ADD**

_Use `COPY` unless you're sure you need the additional functionality that comes with `ADD`._

_What's the difference between `COPY` and `ADD`?_

Both commands allow you to copy files from a specific location into a Docker image:

```jsx
**ADD** <src> <dest>
**COPY** <src> <dest>
```

While they look like they serve the same purpose, `ADD` has some additional functionality:

- `COPY` is used for copying local files or directories from the Docker host to the image.
- `ADD` can be used for the same thing as well as downloading external files. Also, if you use a compressed file (tar, gzip, bzip2, etc.) as the `<src>` parameter, `ADD` will automatically unpack the contents to the given location.

```jsx
*# copy local files on the host  to the destination***COPY** /source/path  /destination/path
**ADD** /source/path  /destination/path

*# download external file and copy to the destination***ADD** http://external.file/url  /destination/path

*# copy and extract local compresses files***ADD** source.file.tar.gz /destination/path
```

### **Cache Python Packages to the Docker Host**

When a requirements file is changed, the image needs to be rebuilt to install the new packages. The earlier steps will be cached, as mentioned in [Minimize the Number of Layers](https://testdriven.io/blog/docker-best-practices/#minimize-the-number-of-layers). Downloading all packages while rebuilding the image can cause a lot of network activity and takes a lot of time. Each rebuild takes up the same amount of time for downloading common packages across builds.

You can avoid this by mapping the pip cache directory to a directory on the host machine. So for each rebuild, the cached versions persist and can improve the build speed.

Add a volume to the docker run as `-v $HOME/.cache/pip-docker/:/root/.cache/pip` or as a mapping in the Docker Compose file.

> The directory presented above is only for reference. Make sure you map the cache directory and not the site-packages (where the built packages reside).

Moving the cache from the docker image to the host can save you space in the final image.

If you're leveraging [Docker BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/), use BuildKit cache mounts to manage the cache:

```jsx
*# syntax = docker/dockerfile:1.2*

...

**COPY** requirements.txt .

**RUN** --mount=type=cache,target=/root/.cache/pip **\**
        pip install -r requirements.txt

...
```

### **Run Only One Process Per Container**

_Why is it recommended to run only one process per container?_

Let's assume your application stack consists of a two web servers and a database. While you could easily run all three from a single container, you should run each in a separate container to make it easier to reuse and scale each of the individual services.

1. **Scaling** - With each service in a separate container, you can scale one of your web servers horizontally as needed to handle more traffic.
2. **Reusability** - Perhaps you have another service that needs a containerized database. You can simply reuse the same database container without bringing two unnecessary services along with it.
3. **Logging** - Coupling containers makes logging much more complex. We'll address this in further detail later in this article.
4. **Portability and Predictability** - It's much easier to make security patches or debug an issue when there's less surface area to work with.

### **Prefer Array Over String Syntax**

You can write the `CMD` and `ENTRYPOINT` commands in your Dockerfiles in both array (exec) or string (shell) formats:

```jsx
*# array (exec)***CMD** ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]

*# string (shell)***CMD** "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app"
```

Both are correct and achieve nearly the same thing; however, you should use the exec format whenever possible. From the [Docker documentation](https://docs.docker.com/compose/faq/#why-do-my-services-take-10-seconds-to-recreate-or-stop):

1. Make sure you're using the exec form of `CMD` and `ENTRYPOINT` in your Dockerfile.
2. For example use `["program", "arg1", "arg2"]` not `"program arg1 arg2"`. Using the string form causes Docker to run your process using bash, which doesn't handle signals properly. Compose always uses the JSON form, so don't worry if you override the command or entrypoint in your Compose file.

So, since most shells don't process signals to child processes, if you use the shell format, `CTRL-C` (which generates a `SIGTERM`) may not stop a child process.

Example:

```jsx
**FROM** ubuntu:18.04

*# BAD: shell format***ENTRYPOINT** top -d

*# GOOD: exec format***ENTRYPOINT** ["top", "-d"]
```

Try both of these. Take note that with the shell format flavor, `CTRL-C` won't kill the process. Instead, you'll see `^C^C^C^C^C^C^C^C^C^C^C`.

Another caveat is that the shell format carries the PID of the shell, not the process itself.

```jsx
*# array format*
root@18d8fd3fd4d2:/app# ps ax
  PID TTY      STAT   TIME COMMAND
    1 ?        Ss     0:00 python manage.py runserver 0.0.0.0:8000
    7 ?        Sl     0:02 /usr/local/bin/python manage.py runserver 0.0.0.0:8000
   25 pts/0    Ss     0:00 bash
  356 pts/0    R+     0:00 ps ax

*# string format*
root@ede24a5ef536:/app# ps ax
  PID TTY      STAT   TIME COMMAND
    1 ?        Ss     0:00 /bin/sh -c python manage.py runserver 0.0.0.0:8000
    8 ?        S      0:00 python manage.py runserver 0.0.0.0:8000
    9 ?        Sl     0:01 /usr/local/bin/python manage.py runserver 0.0.0.0:8000
   13 pts/0    Ss     0:00 bash
  342 pts/0    R+     0:00 ps ax
```

### **Understand the Difference Between ENTRYPOINT and CMD**

_Should I use ENTRYPOINT or CMD to run container processes?_

There are two ways to run commands in a container:

```jsx
**CMD** ["gunicorn", "config.wsgi", "-b", "0.0.0.0:8000"]

*# and***ENTRYPOINT** ["gunicorn", "config.wsgi", "-b", "0.0.0.0:8000"]
```

Both essentially do the same thing: Start the application at `config.wsgi` with a Gunicorn server and bind it to `0.0.0.0:8000`.

The `CMD` is easily overridden. If you run `docker run <image_name> uvicorn config.asgi`, the above CMD gets replaced by the new arguments -- e.g., `uvicorn config.asgi`. Whereas to override the `ENTRYPOINT` command, one must specify the `--entrypoint` option:

`docker run --entrypoint uvicorn config.asgi <image_name>`

Here, it's clear that we're overriding the entrypoint. So, it's recommended to use `ENTRYPOINT` over `CMD` to prevent accidentally overriding the command.

They can be used together as well.

For example:

```jsx
**ENTRYPOINT** ["gunicorn", "config.wsgi", "-w"]
**CMD** ["4"]
```

When used together like this, the command that is run to start the container is:

`gunicorn config.wsgi -w 4`

As discussed above, `CMD` is easily overridden. Thus, `CMD` can be used to pass arguments to the `ENTRYPOINT` command. The number of workers can be easily changed like so:

`docker run <image_name> 6`

This will start the container with six Gunicorn workers rather then four.

### **Include a HEALTHCHECK Instruction**

_Use a `HEALTHCHECK` to determine if the process running in the container is not only up and running, but is "healthy" as well._

Docker exposes an API for checking the status of the process running in the container, which provides much more information than just whether the process is "running" or not since "running" covers "it is up and working", "still launching", and even "stuck in some infinite loop error state". You can interact with this API via the [HEALTHCHECK](https://docs.docker.com/engine/reference/builder/#healthcheck) instruction.

For example, if you're serving up a web app, you can use the following to determine if the `/` endpoint is up and can handle serving requests:

**`HEALTHCHECK** **CMD** curl --fail http://localhost:8000 || exit 1`

If you run `docker ps`, you can see the status of the `HEALTHCHECK`.

Healthy example:

```jsx
CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS                            PORTS                                       NAMES
09c2eb4970d4   healthcheck   "python manage.py ru…"   10 seconds ago   Up 8 seconds (health: starting)   0.0.0.0:8000->8000/tcp, :::8000->8000/tcp   xenodochial_clarke
```

Unhealthy example:

```jsx
CONTAINER ID   IMAGE         COMMAND                  CREATED              STATUS                          PORTS                                       NAMES
09c2eb4970d4   healthcheck   "python manage.py ru…"   About a minute ago   Up About a minute (unhealthy)   0.0.0.0:8000->8000/tcp, :::8000->8000/tcp   xenodochial_clarke
```

You can take it a step further and set up a custom endpoint used only for health checks and then configure the `HEALTHCHECK` to test against the returned data. For example, if the endpoint returns a JSON response of `{"ping": "pong"}`, you can instruct the `HEALTHCHECK` to validate the response body.

Here's how you view the status of the health check status using `docker inspect`:

```jsx
❯ docker inspect --format "{{json .State.Health }}" ab94f2ac7889
{
  "Status": "healthy",
  "FailingStreak": 0,
  "Log": [
    {
      "Start": "2021-09-28T15:22:57.5764644Z",
      "End": "2021-09-28T15:22:57.7825527Z",
      "ExitCode": 0,
      "Output": "..."
```

> Here, the output is trimmed as it contains the whole HTML output.

You can also add a health check to a Docker Compose file:

```jsx
**version**: "3.8"

**services**:
  **web**:
    **build**: .
    **ports**:
      - '8000:8000'
    **healthcheck**:
      **test**: curl --fail http://localhost:8000 || exit 1
      **interval**: 10s
      **timeout**: 10s
      **start_period**: 10s
      **retries**: 3
```

Options:

- `test`: The command to test.
- `interval`: The interval to test for -- i.e., test every `x` unit of time.
- `timeout`: Max time to wait for the response.
- `start_period`: When to start the health check. It can be used when additional tasks are performed before the containers are ready, like running migrations.
- `retries`: Maximum retries before designating a test as `failed`.

> If you're using an orchestration tool other than Docker Swarm -- i.e., Kubernetes or AWS ECS -- it's highly likely that the tool has its own internal system for handling health checks. Refer to the docs of the particular tool before adding the HEALTHCHECK instruction.

## **Images**

### **Version Docker Images**

Whenever possible, avoid using the `latest` tag.

If you rely on the `latest` tag (which isn't really a "tag" since it's applied by default when an image isn't explicitly tagged), you can't tell which version of your code is running based on the image tag. It makes it challenging to do rollbacks and makes it easy to overwrite it (either accidentally or maliciously). Tags, like your infrastructure and deployments, should be [immutable](https://sysdig.com/blog/toctou-tag-mutability/).

Regardless of how you treat your internal images, you should never use the `latest` tag for base images since you could inadvertently deploy a new version with breaking changes to production.

For internal images, use descriptive tags to make it easier to tell which version of the code is running, handle rollbacks, and avoid naming collisions.

For example, you can use the following descriptors to make up a tag:

1. Timestamps
2. Docker image IDs
3. Git commit hashes
4. Semantic version

> For more options, check out this answer from the "Properly Versioning Docker Images" Stack Overflow question.

For example:

```jsx
docker build -t web-prod-a072c4e5d94b5a769225f621f08af3d4bf820a07-0.1.4 .
```

Here, we used the following to form the tag:

1. Project name: `web`
2. Environment name: `prod`
3. Git commit hash: `a072c4e5d94b5a769225f621f08af3d4bf820a07`
4. Semantic version: `0.1.4`

It's essential to pick a tagging scheme and be consistent with it. Since commit hashes make it easy to tie an image tag back to the code quickly, it's highly recommended to include them in your tagging scheme.

### **Don't Store Secrets in Images**

_Secrets are sensitive pieces of information such as passwords, database credentials, SSH keys, tokens, and TLS certificates, to name a few. These should not be baked into your images without being encrypted since unauthorized users who gain access to the image can merely examine the layers to extract the secrets._

Do not add secrets to your Dockerfiles in plaintext, especially if you're pushing the images to a public registry like [Docker Hub](https://hub.docker.com/):

```jsx
**FROM** python:3.9-slim

**ENV** DATABASE_PASSWORD "SuperSecretSauce"
```

Instead, they should be injected via:

1. Environment variables (at run-time)
2. Build-time arguments (at build-time)
3. An orchestration tool like Docker Swarm (via Docker secrets) or Kubernetes (via Kubernetes secrets)

Also, you can help prevent leaking secrets by adding common secret files and folders to your *.dockerignore* file:

- `*/.env **/.aws **/.ssh`

Finally, be explicit about what files are getting copied over to the image rather than copying all files recursively:

\*`# BAD**\*COPY** . .

\*# GOOD**\*copy** ./app.py .`

Being explicit also helps to limit cache-busting.

### **Environment Variables**

You can pass secrets via environment variables, but they will be visible in all child processes, linked containers, and logs, as well as via `docker inspect`. It's also difficult to update them.

```jsx
$ docker run --detach --env "DATABASE_PASSWORD=SuperSecretSauce" python:3.9-slim

d92cf5cf870eb0fdbf03c666e7fcf18f9664314b79ad58bc7618ea3445e39239

$ docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' d92cf5cf870eb0fdbf03c666e7fcf18f9664314b79ad58bc7618ea3445e39239

DATABASE_PASSWORD=SuperSecretSauce
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568
PYTHON_VERSION=3.9.7
PYTHON_PIP_VERSION=21.2.4
PYTHON_SETUPTOOLS_VERSION=57.5.0
PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/c20b0cfd643cd4a19246ccf204e2997af70f6b21/public/get-pip.py
PYTHON_GET_PIP_SHA256=fa6f3fb93cce234cd4e8dd2beb54a51ab9c247653b52855a48dd44e6b21ff28b
```

This is the most straightforward approach to secrets management. While it's not the most secure, it will keep the honest people honest since it provides a thin layer of protection, helping to keep the secrets hidden from curious wandering eyes.

Passing secrets in using a shared volume is a better solution, but they should be encrypted, via [Vault](https://www.vaultproject.io/) or [AWS Key Management Service](https://aws.amazon.com/kms/) (KMS), since they are saved to disc.

### **Build-time Arguments**

You can pass secrets in at build-time using [build-time arguments](https://docs.docker.com/engine/reference/commandline/build/#set-build-time-variables---build-arg), but they will be visible to those who have access to the image via `docker history`.

Example:

```jsx
**FROM** python:3.9-slim

**ARG** DATABASE_PASSWORD
```

Build:

`$ docker build --build-arg "DATABASE_PASSWORD=SuperSecretSauce" .`

If you only need to use the secrets temporarily as part of the build -- i.e., SSH keys for cloning a private repo or downloading a private package -- you should use a multi-stage build since the builder history is ignored for temporary stages:

```jsx
*# temp stage***FROM** python:3.9-slim **as** builder

*# secret***ARG** SSH_PRIVATE_KEY

*# install git***RUN** apt-get update && **\**
    apt-get install -y --no-install-recommends git

*# use ssh key to clone repo***RUN** mkdir -p /root/.ssh/ && **\**echo "**${**PRIVATE_SSH_KEY**}**" > /root/.ssh/id_rsa
**RUN** touch /root/.ssh/known_hosts &&
    ssh-keyscan bitbucket.org >> /root/.ssh/known_hosts
**RUN** git clone git@github.com:testdrivenio/not-real.git

*# final stage***FROM** python:3.9-slim

**WORKDIR** /app

*# copy the repository from the temp image***COPY** --from=builder /your-repo /app/your-repo

*# use the repo for something!*
```

The multi-stage build only retains the history for the final image. Keep in mind that you can use this functionality for permanent secrets that you need for your application, like a database credential.

You can also use the new `--secret` option in Docker build to pass secrets to Docker images that do not get stored in the images.

\*`# "docker_is_awesome" > secrets.txt**\*FROM** alpine

\*# shows secret from default secret location:**\*RUN** --mount=type=secret,id=mysecret cat /run/secrets/mysecret`

This will mount the secret from the `secrets.txt` file.

Build the image:

```jsx
docker build --no-cache --progress=plain --secret id=mysecret,src=secrets.txt .

*# output*
...
*#4 [1/2] FROM docker.io/library/alpine#4 sha256:665ba8b2cdc0cb0200e2a42a6b3c0f8f684089f4cd1b81494fbb9805879120f7#4 CACHED#5 [2/2] RUN --mount=type=secret,id=mysecret cat /run/secrets/mysecret#5 sha256:75601a522ebe80ada66dedd9dd86772ca932d30d7e1b11bba94c04aa55c237de#5 0.635 docker_is_awesome#5 DONE 0.7s#6 exporting to image*
```

Finally, check the history to see if the secret is leaking:

```jsx
❯ docker history 49574a19241c
IMAGE          CREATED         CREATED BY                                      SIZE      COMMENT
49574a19241c   5 minutes ago   CMD ["/bin/sh"]                                 0B        buildkit.dockerfile.v0
<missing>      5 minutes ago   RUN /bin/sh -c cat /run/secrets/mysecret *# b…   0B        buildkit.dockerfile.v0*
<missing>      4 weeks ago     /bin/sh -c *#(nop)  CMD ["/bin/sh"]              0B*
<missing>      4 weeks ago     /bin/sh -c *#(nop) ADD file:aad4290d27580cc1a…   5.6MB*
```

> For more on build-time secrets, review Don't leak your Docker image's build secrets.

### **Docker Secrets**

If you're using [Docker Swarm](https://docs.docker.com/engine/swarm/), you can manage secrets with [Docker secrets](https://docs.docker.com/engine/reference/commandline/secret/).

For example, init Docker Swarm mode:

```jsx
$ docker swarm init
```

Create a docker secret:

```jsx
$ echo "supersecretpassword" | docker secret create postgres_password -
qdqmbpizeef0lfhyttxqfbty0

$ docker secret ls
ID                          NAME                DRIVER    CREATED         UPDATED
qdqmbpizeef0lfhyttxqfbty0   postgres_password             4 seconds ago   4 seconds ago
```

When a container is given access to the above secret, it will mount at `/run/secrets/postgres_password`. This file will contain the actual value of the secret in plaintext.

Using a diffrent orhestration tool?

1. AWS EKS - [Using AWS Secrets Manager secrets with Kubernetes](https://docs.aws.amazon.com/eks/latest/userguide/manage-secrets.html)
2. DigitalOcean Kubernetes - [Recommended Steps to Secure a DigitalOcean Kubernetes Cluster](https://www.digitalocean.com/community/tutorials/recommended-steps-to-secure-a-digitalocean-kubernetes-cluster)
3. Google Kubernetes Engine - [Using Secret Manager with other products](https://cloud.google.com/secret-manager/docs/using-other-products#google-kubernetes-engine)
4. Nomad - [Vault Integration and Retrieving Dynamic Secrets](https://learn.hashicorp.com/tutorials/nomad/vault-postgres?in=nomad/integrate-vault)

### **Use a .dockerignore File**

We've mentioned using a *[.dockerignore* file](https://docs.docker.com/engine/reference/builder/#dockerignore-file) a few times already. This file is used to specify the files and folders that you don't want to be added to the initial build context sent to the Docker daemon, which will then build your image. Put another way, you can use it to define the build context that you need.

When a Docker image is built, the entire Docker context -- i.e., the root of your project -- is sent to the Docker daemon *before* the `COPY` or `ADD` commands are evaluated. This can be pretty expensive, especially if you have many dependencies, large data files, or build artifacts in your project. Plus, the Docker CLI and daemon may not be on the same machine. So, if the daemon is executed on a remote machine, you should be even more mindful of the size of the build context.

What should you add to the *.dockerignore* file?

1. Temporary files and folders
2. Build logs
3. Local secrets
4. Local development files like *docker-compose.yml*
5. Version control folders like ".git", ".hg", and ".svn"

Example:

- `*/.git **/.gitignore **/.vscode **/coverage **/.env **/.aws **/.ssh Dockerfile README.md docker-compose.yml **/.DS_Store **/venv **/env`

In summary, a properly structured *.dockerignore* can help:

1. Decrease the size of the Docker image
2. Speed up the build process
3. Prevent unnecessary cache invalidation
4. Prevent leaking secrets

### **Lint and Scan Your Dockerfiles and Images**

Linting is the process of checking your source code for programmatic and stylistic errors and bad practices that could lead to potential flaws. Just like with programming languages, static files can also be linted. With your Dockerfiles specifically, linters can help ensure they are maintainable, avoid deprecated syntax, and adhere to best practices. Linting your images should be a standard part of your CI pipelines.

[Hadolint](https://github.com/hadolint/hadolint) is the most popular Dockerfile linter:

```jsx
$ hadolint Dockerfile

Dockerfile:1 DL3006 warning: Always tag the version of an image explicitly
Dockerfile:7 DL3042 warning: Avoid the use of cache directory with pip. Use `pip install --no-cache-dir <package>`
Dockerfile:9 DL3059 info: Multiple consecutive `RUN` instructions. Consider consolidation.
Dockerfile:17 DL3025 warning: Use arguments JSON notation **for** CMD and ENTRYPOINT arguments
```

You can see it in action online at [https://hadolint.github.io/hadolint/](https://hadolint.github.io/hadolint/). There's also a [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=exiasr.hadolint).

You can couple linting your Dockerfiles with scanning images and containers for vulnerabilities.

Some options:

1. [Snyk](https://docs.docker.com/engine/scan/) is the exclusive provider of native vulnerability scanning for Docker. You can use the `docker scan` CLI command to scan images.
2. [Trivy](https://aquasecurity.github.io/trivy/) can be used to scan container images, file systems, git repositories, and other configuration files.
3. [Clair](https://github.com/quay/clair) is an open-source project used for the static analysis of vulnerabilities in application containers.
4. [Anchore](https://github.com/anchore/anchore-engine) is an open-source project that provides a centralized service for inspection, analysis, and certification of container images.

In summary, lint and scan your Dockerfiles and images to surface any potential issues that deviate from best practices.

### **Sign and Verify Images**

_How do you know that the images used to run your production code have not been tampered with?_

Tampering can come over the wire via [man-in-the-middle](https://en.wikipedia.org/wiki/Man-in-the-middle_attack) (MITM) attacks or from the registry being compromised altogether.

[Docker Content Trust](https://docs.docker.com/engine/security/trust/) (DCT) enables the signing and verifying of Docker images from remote registries.

To verify the integrity and authenticity of an image, set the following environment variable:

`DOCKER_CONTENT_TRUST=1`

Now, if you try to pull an image that hasn't been signed, you'll receive the following error:

```jsx
Error: remote trust data does not exist **for** docker.io/namespace/unsigned-image:
notary.docker.io does not have trust data **for** docker.io/namespace/unsigned-image
```

You can learn about signing images from the [Signing Images with Docker Content Trust](https://docs.docker.com/engine/security/trust/#signing-images-with-docker-content-trust) documentation.

When downloading images from Docker Hub, make sure to use either [official images](https://docs.docker.com/docker-hub/official_images/) or verififed images from trusted sources. Larger teams should look to using their own internal [private container registry](https://docs.docker.com/registry/deploying/).

## **Bonus Tips**

### **Using Python Virtual Environments**

_Should you use a virtual environment inside a container?_

In most cases, virtual environments are unnecessary as long as you stick to running only a single process per container. Since the container itself provides isolation, packages can be installed system-wide. That said, you may want to use a virtual environment in a multi-stage build rather than building wheel files.

Example with wheels:

```jsx
*# temp stage***FROM** python:3.9-slim **as** builder

**WORKDIR** /app

**ENV** PYTHONDONTWRITEBYTECODE 1
**ENV** PYTHONUNBUFFERED 1

**RUN** apt-get update && **\**
    apt-get install -y --no-install-recommends gcc

**COPY** requirements.txt .
**RUN** pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

*# final stage***FROM** python:3.9-slim

**WORKDIR** /app

**COPY** --from=builder /app/wheels /wheels
**COPY** --from=builder /app/requirements.txt .

**RUN** pip install --no-cache /wheels/*
```

Example with virtualenv:

```jsx
*# temp stage***FROM** python:3.9-slim **as** builder

**WORKDIR** /app

**ENV** PYTHONDONTWRITEBYTECODE 1
**ENV** PYTHONUNBUFFERED 1

**RUN** apt-get update && **\**
    apt-get install -y --no-install-recommends gcc

**RUN** python -m venv /opt/venv
**ENV** PATH="/opt/venv/bin:$PATH"

**COPY** requirements.txt .
**RUN** pip install -r requirements.txt

*# final stage***FROM** python:3.9-slim

**COPY** --from=builder /opt/venv /opt/venv

**WORKDIR** /app

**ENV** PATH="/opt/venv/bin:$PATH"
```

### **Set Memory and CPU Limits**

It's a good idea to limit the memory usage of your Docker containers, especially if you're running multiple containers on a single machine. This can prevent any of the containers from using all available memory and thereby crippling the rest.

The easiest way to limit memory usage is to use `--memory` and `--cpu` options in the Docker cli:

`$ docker run --cpus=2 -m 512m nginx`

The above command limits the container usage to 2 CPUs and 512 megabytes of main memory.

You can do the same in a Docker Compose file like so:

```jsx
**version**: "3.9"
**services**:
  **redis**:
    **image**: redis:alpine
    **deploy**:
      **resources**:
        **limits**:
          **cpus**: 2
          **memory**: 512M
        **reservations**:
          **cpus**: 1
          **memory**: 256M
```

Take note of the `reservations` field. It's used to set a soft limit, which takes priority when the host machine has low memory or CPU resources.

Additional resources:

1. [Runtime options with Memory, CPUs, and GPUs](https://docs.docker.com/config/containers/resource_constraints/)
2. [Docker Compose resouce constraints](https://docs.docker.com/compose/compose-file/compose-file-v3/#resources)

### **Log to stdout or stderr**

Applications running within your Docker containers should write log messages to standard output (stdout) and standard error (stderr) rather than to a file.

You can then configure the Docker daemon to send your log messages to a centralized logging solution (like [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html) or [Papertrail](https://www.papertrail.com/)).

For more, check out [Treat logs as event streams](https://12factor.net/logs) from [The Twelve-Factor App](https://12factor.net/) and [Configure logging drivers](https://docs.docker.com/config/containers/logging/configure/) from the Docker docs.

### **Use a Shared Memory Mount for Gunicorn Heartbeat**

Gunicorn uses a file-based heartbeat system to ensure that all of the forked worker processes are alive.

In most cases, the heartbeat files are found in "/tmp", which is often in memory via [tmpfs](https://en.wikipedia.org/wiki/Tmpfs). Since Docker does not leverage tmpfs by default, the files will be stored on a disk-backed file system. This can cause [problems](https://docs.gunicorn.org/en/20.1.0/faq.html#how-do-i-avoid-gunicorn-excessively-blocking-in-os-fchmod), like random freezes since the heartbeat system uses `os.fchmod`, which may block a worker if the directory is in fact on a disk-backed filesystem.

Fortunately, there is a simple fix: Change the heartbeat directory to a memory-mapped directory via the `--worker-tmp-dir` flag.

```jsx
gunicorn --worker-tmp-dir /dev/shm config.wsgi -b 0.0.0.0:8000
```
