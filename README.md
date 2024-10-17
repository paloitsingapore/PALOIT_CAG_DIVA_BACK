
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

# Requirements
## python 3.12
on mac os: brew install python@3.12
on linux: sudo apt-get install python3.12

## python-tk 
on mac os: brew install python-tk
on linux: sudo apt-get install python-tk


To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```


If you want to deploy you need to configure your AWS credentials. You can do this by running the following command:

```
API_KEY=XXXXXXXXX 
```
example : ASIDSQADSFHDS3SDSN2C

```
API_ENDPOINT=xxxxx
```    
example : API_ENDPOINT_URL=https://xxxxx.execute-api.ap-southeast-1.amazonaws.com/prod

```


You can deploy your code to AWS by running the following command:

```
$ cdk deploy
```


You can add additional faces to the collection by running the following command:

```
$ python face_recognition_gui.py
```

Once you have added your faces, you can run the front end and explore 


To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
