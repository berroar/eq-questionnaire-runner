# eQ Questionnaire Runner

![Build Status](https://github.com/ONSdigital/eq-questionnaire-runner/workflows/Master/badge.svg)
[![codecov](https://codecov.io/gh/ONSdigital/eq-questionnaire-runner/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/eq-questionnaire-runner/branch/master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/4c39ddd3285748f8bfb6b70fd5aaf9cc)](https://www.codacy.com/manual/ONSDigital/eq-questionnaire-runner?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/eq-questionnaire-runner&amp;utm_campaign=Badge_Grade)

## Run with Docker

Install Docker for your system: [https://www.docker.com/](https://www.docker.com/)

To get eq-questionnaire-runner running the following command will build and run the containers

``` shell
RUNNER_ENV_FILE=.development.env docker-compose up -d
```

To launch a survey, navigate to [http://localhost:8000/](http://localhost:8000/)

When the containers are running you are able to access the application as normal, and code changes will be reflected in the running application.
However, any new dependencies that are added would require a re-build.

To rebuild the eq-questionnaire-runner container, the following command can be used.

``` shell
RUNNER_ENV_FILE=.development.env docker-compose build
```

If you need to rebuild the container from scratch to re-load any dependencies then you can run the following

``` shell
RUNNER_ENV_FILE=.development.env docker-compose build --no-cache
```

## Run locally

### Clone the repository

``` shell
git clone git@github.com:ONSdigital/eq-questionnaire-runner.git
```

### Pre-Requisites

In order to run locally you'll need Node.js, snappy, pyenv, jq and wkhtmltopdf installed

``` shell
brew install snappy npm pyenv jq wkhtmltopdf
```

### Setup

Create `.application-version` for local development

This file is automatically created and populated with the git revision id during CI for anything other than development,
but the file is absent when the repo is first cloned and is required for running the app locally. Setting the contents
to `local` removes the implication that any particular revision is used when run locally.

``` shell
echo "local" > .application-version
```

It is preferable to use the version of Python locally that matches that
used on deployment. This project has a `.python_version` file for this
purpose.

Upgrade pip and install dependencies:

``` shell
pyenv install
pip install --upgrade pip setuptools pipenv
pipenv install --dev
```

To update the design system templates run:

``` shell
make load-design-system-templates
```

To download the latest schemas from the [Questionnaire Registry](https://github.com/ONSdigital/eq-questionnaire-schemas):

``` shell
make load-schemas
```

Run the server inside the virtual env created by Pipenv with:

``` shell
make run
```

### Supporting services

Runner requires three supporting services - a questionnaire launcher, a storage backend, and a cache.

#### Run supporting services with Docker

To run the app locally, but the supporting services in Docker, run:

``` shell
make dev-compose-up
```

Note that on Linux you will need to use:

``` shell
make dev-compose-up-linux
```

#### Run supporting services locally

##### [Questionnaire launcher](https://github.com/ONSDigital/eq-questionnaire-launcher)

``` shell
docker run -e SURVEY_RUNNER_SCHEMA_URL=http://docker.for.mac.host.internal:5000 -it -p 8000:8000 onsdigital/eq-questionnaire-launcher:latest
```

##### Storage backends

[DynamoDB](https://github.com/ONSDigital/eq-docker-dynamodb)

``` shell
docker run -it -p 6060:8000 onsdigital/eq-docker-dynamodb:latest
```

or

[Google Datastore](https://hub.docker.com/r/knarz/datastore-emulator/)

``` shell
docker run -it -p 8432:8432 knarz/datastore-emulator:latest
```

##### Cache

``` shell
docker run -it -p 6379:6379 redis:4
```

#### Using Google Cloud Platform for supporting services

To use `EQ_STORAGE_BACKEND` as `datastore` or `EQ_SUBMISSION_BACKEND` as `gcs` directly on GCP and not a docker image, you need to set the GCP project using the following command:

``` shell
gcloud config set project <gcp_project_id>
```

Or set the `GOOGLE_CLOUD_PROJECT` environment variable to your gcp project id.

---

## Frontend Tests

The frontend tests use NodeJS to run. You will need to have node version 14.X to run these tests. To do this, do the following commands:

``` shell
brew install nvm
nvm install
nvm use
```

Install yarn with:

``` shell
npm i -g yarn
```

Fetch npm dependencies:

``` shell
yarn
```

Available commands:

| Command                | Task                                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `yarn test_functional` | Runs the functional tests through Webdriver (requires app running on localhost:5000 and generated pages). |
| `yarn generate_pages`  | Generates the functional test pages.                                                                      |
| `yarn lint`            | Lints the JS, reporting errors/warnings.                                                                  |
| `yarn format`          | Format the json schemas.                                                                                  |

---

### Development with functional tests

The tests are written using [WebdriverIO](https://webdriver.io/docs), [Chai](https://www.chaijs.com/), and [Mocha](https://mochajs.org/)

### Functional test options

The functional tests use a set of selectors that are generated from each of the test schemas. These make it quick to add new functional tests.

To run the functional tests first runner needs to be spin up with:

``` shell
RUNNER_ENV_FILE=.functional-tests.env make run
```

This will set the correct environment variables for running the functional tests.

Then you can run:

``` shell
make test-functional
```

This will delete the `tests/functional/generated_pages` directory and regenerate all the files in it from the schemas.

You can also individually run the `generate_pages` and `test_functional` yarn scripts:

``` shell
yarn generate_pages
yarn test_functional
```


To generate the pages manually you can run the `generate_pages` scripts with the schema directory. Run it from the `tests/functional` directory as follows:

``` shell
./generate_pages.py ../../schemas/test/en/ ./generated_pages -r "../../base_pages"
```

To generate a spec file with the imports included, you can use the `generate_pages.py` script on a single schema with the `-s` argument.

``` shell
./generate_pages.py ../../schemas/test/en/test_multiple_piping.json ./temp_directory -r "../../base_pages" -s spec/test_multiple_piping.spec.js
```

If you have already built the generated pages, then the functional tests can be executed with:

``` shell
yarn test_functional
```

This can be limited to a single spec using:

``` shell
yarn test_functional --spec save_sign_out.spec.js
```

To run a single test, add `.only` into the name of any `describe` or `it` function:

`describe.only('Skip Conditions', function() {...}` or

`it.only('Given this is a test', function() {...}`

Test suites are configured in the `wdio.conf.js` file.
An individual test suite can be run using:

``` shell
yarn test_functional --suite <suite>
```

To run the tests against a remote deployment you will need to specify the environment variable of EQ_FUNCTIONAL_TEST_ENV eg:

``` shell
EQ_FUNCTIONAL_TEST_ENV=https://staging-new-surveys.dev.eq.ons.digital/ yarn test_functional
```

---

## Deploying

For deploying with Concourse see the [CI README](./ci/README.md).

### Deployment with [gcloud](https://cloud.google.com/sdk/gcloud)

To deploy this application with gcloud, you must be logged in using `gcloud auth login` and `gcloud auth application-default login`.

When deploying with gcloud the environment variables specified in [Deploying the app](./README.md#deploying-the-app) must be set.

Then call the following command with environment variables set:

``` shell
./ci/deploy_app.sh
```

### Deploying credentials

Before deploying the app to GCP you need to create the application credentials. Run the following command to provision the credentials:

``` shell
PROJECT_ID=PROJECT_ID EQ_KEYS_FILE=PATH_TO_KEYS_FILE EQ_SECRETS_FILE=PATH_TO_SECRETS_FILE ./ci/deploy_credentials.sh
```

For example:

``` shell
PROJECT_ID=eq-test EQ_KEYS_FILE=dev-keys.yml EQ_SECRETS_FILE=dev-secrets.yml ./ci/deploy_credentials.sh
```

### Deploying the app

The following environment variables must be set when deploying the app.

| Variable Name   | Description                            |
| --------------- | -------------------------------------- |
| PROJECT_ID      | The ID of the GCP target project       |
| DOCKER_REGISTRY | The FQDN of the target Docker registry |
| IMAGE_TAG       |                                        |

The following environment variables are optional:

| Variable Name                | Default          | Description                                                                                                    |
| ---------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------- |
| REGION                       | europe-west2     | The region that will be used for your Cloud Run service                                                        |
| CONCURRENCY                  | 80               | The maximum number of requests that can be processed simultaneously by a given container instance              |
| MIN_INSTANCES                | 1                | The minimum number of container instances that can be used for your Cloud Run service                          |
| MAX_INSTANCES                | 1                | The maximum number of container instances that can be used for your Cloud Run service                          |
| CPU                          | 4                | The number of CPUs to allocate for each Cloud Run container instance                                           |
| MEMORY                       | 4G               | The amount of memory to allocate for each Cloud Run container instance                                         |
| GOOGLE_TAG_MANAGER_ID        |                  | The Google Tag Manger ID - Specifies the GTM account                                                           |
| GOOGLE_TAG_MANAGER_AUTH      |                  | The Google Tag Manger Auth - Ties the GTM container with the whole environment                                 |
| WEB_SERVER_TYPE              | gunicorn-threads | Web server type used to run the application. This also determines the worker class which can be async/threaded |
| WEB_SERVER_WORKERS           | 7                | The number of worker processes                                                                                 |
| WEB_SERVER_THREADS           | 10               | The number of worker threads per worker                                                                        |
| WEB_SERVER_UWSGI_ASYNC_CORES | 10               | The number of cores to initialise when using "uwsgi-async" web server worker type                              |
| DATASTORE_USE_GRPC           | False            | Determines whether to use gRPC for Datastore. gRPC is currently only supported for threaded web servers        |

To deploy the app, run the following command:

``` shell
./ci/deploy_app.sh
```

---

## Internationalisation

We use flask-babel to do internationalisation. To extract messages from source and create the messages.pot file, in the project root run the following command.

``` shell
make translation-templates
```

```make translation-templates``` is a command that uses pybabel to extract static messages.

This will extract messages and place them in the .pot files ready for translation.

These .pot files will then need to be translated. The translation process is documented in Confluence [here](https://collaborate2.ons.gov.uk/confluence/display/SDC/Translation+Process)

Once we have the translated .po files they can be added to the source code and used by the application

## Environment Variables

The following env variables can be used

| Variable Name                             | Default                    | Description                                                                                                    |
| ----------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| EQ_SESSION_TIMEOUT_SECONDS                | 2700 (45 mins)             | The duration of the flask session                                                                              |
| EQ_PROFILING                              | False                      | Enables or disables profiling (True/False) Default False/Disabled                                              |
| EQ_GOOGLE_TAG_MANAGER_ID                  |                            | The Google Tag Manger ID - Specifies the GTM account                                                           |
| EQ_GOOGLE_TAG_MANAGER_AUTH                |                            | The Google Tag Manger Auth - Ties the GTM container with the whole environment                                 |
| EQ_ENABLE_HTML_MINIFY                     | True                       | Enable minification of html                                                                                    |
| EQ_ENABLE_SECURE_SESSION_COOKIE           | True                       | Set secure session cookies                                                                                     |
| EQ_MAX_HTTP_POST_CONTENT_LENGTH           | 65536                      | The maximum http post content length that the system wil accept                                                |
| EQ_MINIMIZE_ASSETS                        | True                       | Should JS and CSS be minimized                                                                                 |
| MAX_CONTENT_LENGTH                        | 65536                      | max request payload size in bytes                                                                              |
| EQ_APPLICATION_VERSION_PATH               | .application-version       | the location of a file containing the application version number                                               |
| EQ_ENABLE_LIVE_RELOAD                     | False                      | Enable livereload of browser when scripts, styles or templates are updated                                     |
| EQ_SECRETS_FILE                           | secrets.yml                | The location of the secrets file                                                                               |
| EQ_KEYS_FILE                              | keys.yml                   | The location of the keys file                                                                                  |
| EQ_SUBMISSION_BACKEND                     |                            | Which submission backend to use ( gcs, rabbitmq, log )                                                         |
| EQ_GCS_SUBMISSION_BUCKET_ID               |                            | The bucket name in GCP to store the submissions in                                                             |
| EQ_GCS_FEEDBACK_BUCKET_ID                 |                            | The bucket name in GCP to store the feedback in                                                                |
| EQ_RABBITMQ_HOST                          |                            |                                                                                                                |
| EQ_RABBITMQ_HOST_SECONDARY                |                            |                                                                                                                |
| EQ_RABBITMQ_PORT                          | 5672                       |                                                                                                                |
| EQ_RABBITMQ_QUEUE_NAME                    | submit_q                   | The name of the submission queue                                                                               |
| EQ_SERVER_SIDE_STORAGE_USER_ID_ITERATIONS | 10000                      |                                                                                                                |
| EQ_STORAGE_BACKEND                        | datastore                  |                                                                                                                |
| EQ_DYNAMODB_ENDPOINT                      |                            |                                                                                                                |
| EQ_REDIS_HOST                             |                            | Hostname of Redis instance used for ephemeral storage                                                          |
| EQ_REDIS_PORT                             |                            | Port number of Redis instance used for ephemeral storage                                                       |
| EQ_DYNAMODB_MAX_RETRIES                   | 5                          |                                                                                                                |
| EQ_DYNAMODB_MAX_POOL_CONNECTIONS          | 30                         |                                                                                                                |
| EQ_QUESTIONNAIRE_STATE_TABLE_NAME         |                            |                                                                                                                |
| EQ_SESSION_TABLE_NAME                     |                            |                                                                                                                |
| EQ_USED_JTI_CLAIM_TABLE_NAME              |                            |                                                                                                                |
| WEB_SERVER_TYPE                           |                            | Web server type used to run the application. This also determines the worker class which can be async/threaded |
| WEB_SERVER_WORKERS                        |                            | The number of worker processes                                                                                 |
| WEB_SERVER_THREADS                        |                            | The number of worker threads per worker                                                                        |
| WEB_SERVER_UWSGI_ASYNC_CORES              |                            | The number of cores to initialise when using "uwsgi-async" web server worker type                              |
| DATASTORE_USE_GRPC                        | False                      | Determines whether to use gRPC for Datastore. gRPC is currently only supported for threaded web servers        |
| ACCOUNT_SERVICE_BASE_URL                  | `https://surveys.ons.gov.uk` | The base URL of the account service used to launch the survey                                                  |
| ONS_URL                                   | `https://www.ons.gov.uk`   | The URL of the ONS website where static content is sourced, e.g. accessibility info                                                  |

The following env variables can be used when running tests

``` shell
EQ_FUNCTIONAL_TEST_ENV - the pre-configured environment [local, docker, preprod] or the url of the environment that should be targeted
```

---

## JWT Integration

Integration with the survey runner requires the use of a signed JWT using public and private key pair (see [https://jwt.io](https://jwt.io),
[https://tools.ietf.org/html/rfc7519](https://tools.ietf.org/html/rfc7519), [https://tools.ietf.org/html/rfc7515](https://tools.ietf.org/html/rfc7515)).

Once signed the JWT must be encrypted using JWE (see [https://tools.ietf.org/html/rfc7516](https://tools.ietf.org/html/rfc7516)).

The JWT payload must contain the following claims:

- exp - expiration time
- iat - issued at time

The header of the JWT must include the following:

- alg - the signing algorithm (must be RS256)
- type - the token type (must be JWT)
- kid - key identification (must be EDCRRM)

The JOSE header of the final JWE must include:

- alg - the key encryption algorithm (must be RSA-OAEP)
- enc - the key encryption encoding (must be A256GCM)

To access the application you must provide a valid JWT. To do this browse to the /session url and append a token parameter.
This parameter must be set to a valid JWE encrypted JWT token. Only encrypted tokens are allowed.

There is a python script for generating tokens for use in development, to run:

``` shell
python token_generator.py
```

---

## Profiling

Refer to our [profiling document](doc/profiling.md).

---

## Updating / Installing dependencies

### Python
To add a new dependency, use `pipenv install [package-name]`, which not only installs the package but Pipenv will also go to the trouble of updating the Pipfile as well.

NB: both the Pipfile and Pipfile.lock files are required in source control to accurately pin dependencies.

### JavaScript
To add a new dependency, use `yarn add [package-name]` and `yarn` to install all the packages locally.

---

## Testing Design System changes (locally) without pushing to actual CDN

### On [Design System](https://github.com/ONSdigital/design-system) Repo
Checkout branch with new changes on

You will need to install the Design System dependencies to do this so run `yarn` in the terminal if you haven't
You will also need to install gulp

Then in the terminal run:

``` shell
yarn cdn-bundle
cd build
browser-sync start --cwd -s --http --port 5678
```

You should now see output indicating that files are being served from `localhost:5678`. So main.css for example will now be served on `http://localhost:5678//css/main.css`

Now switch to the eQ Questionnaire Runner Repo

### On eQ Questionnaire Runner Repo
In a separate terminal window/tab:
Checkout the runner branch you want to test on

Edit your .development.env with following:

``` shell
CDN_URL=http://localhost:5678
CDN_ASSETS_PATH=
```

Edit the Makefile to remove `load-design-system-templates` from the build command. Should now look like this:

``` shell
build: load-schemas translate
```

Run `make load-design-system-templates` in the terminal to make sure you have the Design System templates loaded

Then edit the first line in the `templates/layout/_template.njk` file to remove the version number. Should now look like this:

``` shell
{% set release_version = "" %}
```

Then spin up launcher and runner with `make dev-compose-up` and `make run`

Now when navigating to localhost:8000 and launching a schema, this will now be using the local cdn with the changes from the Design System branch
