# Multi-User Blog

> A multi-user blog to publish your stories and make them known.

The application is live here - https://avenue-147516.appspot.com

## Features

* A modern web application running on Google App Engine - an open cloud platform.
* Intuitive website workflow.
* Use of templates to unify the site.
* Secure passwords.
* Local permissions implemented appropriately.
* Code follows Python Guide Style.

## Setup


### Create a project on Google Cloud Platform
* Visit `console.cloud.google.com`. Create a new project.
* Find `App Engine` on the left-side navigation and click on `Dashboard`.
* Select Python as the language
* Select appropriate location to server your app from.


### Download and install SDK
* Create an environment variable for the correct distribution:
```
export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
```
* Add the Cloud SDK distribution URI as a package source:
```
echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
```
* Import the Google Cloud public key:
```
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
```
* Update and install the Cloud SDK:
```
sudo apt-get update && sudo apt-get install google-cloud-sdk
```
* Install the python additional component:
```
sudo apt-get install google-cloud-sdk-app-engine-python
```
* Run the following to select the current project:
```
gcloud init
```

## Local Development

* Use `dev_appserver.py` to locally run an instance of the app.
```
$ dev_appserver.py [PATH_TO_YOUR_APP]
```
* You can access your application at `http://localhost:8080`

## Deploy application

* Follow the [App Engine Quickstart](https://cloud.google.com/appengine/docs/standard/python/quickstart) to get a sample app up and running.

* Change directory into application and use `gcloud` command to deploy your app:
```
gcloud app deploy app.yaml --project [YOUR_PROJECT_ID]
```

## License
MIT © [Niraj Pandkar](https://github.com/nirajpandkar)