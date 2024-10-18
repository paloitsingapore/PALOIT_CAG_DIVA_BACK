
# Welcome to your Python project!

## You will find the CDK and the backend tools
- Directions
- Backend Stack
- Face Indexing and Recognition
- Orchestration Layer

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

# Requirements
### python 3.12
on mac os: brew install python@3.12
on linux: sudo apt-get install python3.12

### python-tk 
on mac os: brew install python-tk
on linux: sudo apt-get install python-tk


Create .env file at the root of the project based in the .env_template file

##### PLEASE NOTE
To facilitate the exploration of the POC, PALO IT shares a working environement. 
This enviroment will be running until end of Novemeber.
```
CDK_DEFAULT_ACCOUNT=034362042832
CDK_DEFAULT_REGION=ap-southeast-1
API_ENDPOINT_URL= https://ed5zq5eya8.execute-api.ap-southeast-1.amazonaws.com/prod/
API_KEY=sO7UjJjqBg61I8uWVS6cu1ijLtwEx4Wg2x7xQUdK
```


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


## CDK  (can be ignored if using the provided credentials)

### Prerequisites
 
**AWS CLI**: Ensure that the AWS CLI is installed and configured with appropriate credentials.
 
```
$ aws configure
```
 
**CDK Toolkit**: Install the CDK Toolkit globally if it’s not already installed.
 
 
```
$ npm install -g aws-cdk
```



The `cdk.json` file tells the CDK Toolkit how to execute your app.

You can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```
You can deploy your code to AWS by running the following command:

```
$ cdk deploy
```


To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation



## Face Indexing and Recognition

To start, you will need to index faces using the face recognition indexing built in Python.

You can add additional faces to the collection by running the following command:
```
$ python face_recognition_gui.py
```

Put the Name of the passenger and select the persona.

For the POC, we created 3 personas. Find details in the presentation deck.

To help you indexing the faces we created 2 videos in the folder 
- to index the face
- to recognise a face.


Once you have added your faces, you can run the front end and explore 


### Next step, Front end configuration.
When the face has been indexed, you can install and run the frontend.


##### PLEASE NOTE
For the test of the POC, you can ignore deploying your own CDK.
PALO IT shares a working environement and this enviroment will be running until end of Novemeber.

1 - Add Faces and peronas
2 - run the front end at this address http://staging.d32b1muquuvyhn.amplifyapp.com/


Enjoy!
