Various development tools for the log2timeline projects and dependencies.

For more information see:

* Project documentation: https://github.com/log2timeline/devtools/wiki/Home

## Getting started with Plaso development

This guide assumes you have [Docker](https://docs.docker.com/install/) installed.

The build scripts also require 2 python dependencies:

`$ pip install docker GitPython`

Then, set `PLASO_SRC` to the location of the cloned repository, and build your development image:

`$ tools/develop.py build`

To make sure the environment was built correctly you can run the dependency check:

`$ tools/develop.py check_dependencies`

And run the tests:

`$ tools/develop.py test`

If that all works, then you're ready to start up your development environment:

```
$ tools/develop.py start

Starting container with image plaso-dev-environment:latest
To enter the development environment, attach to container relaxed_saha
  e.g. 'docker exec -it relaxed_saha /bin/bash'
```

Attaching to the docker container will provide you with an environment containing all of the dependencies for the Plaso revision checked out in `$PLASO_SRC`, with the Plaso checkout you specified volumed in at `/root/plaso`.