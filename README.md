# sam-simple-chat

This is a Python3 simple WebSocket chat Client/Server using The AWS Serverless Application Model (SAM).

### Geting Started
In order to build this sam application, you need to install the AWS dependencies. You can follow the instructions here --> https://aws.amazon.com/serverless/sam/

Once you have sorted our the dependencies, you just need to enter following commands
```
sam build; sam deploy --guided
```

You ned to deploy this application in AWS since AWS SAM still lack of support to test WebSocket application locally. (https://github.com/aws/aws-sam-cli/issues/896)

Once your application installed, you need to pip the python dependencies in order to run the chat client. (use virtualenv or anything that you preferred)

```
pip install -r requirements.txt
```

Then execute the client

```
python client.py
```

![Chat Client](https://i.imgur.com/iTuyhtp.png "Chat Client")


### Writing your own client
Use the standard WebSocket API, once you connect to the WebSocket URL there are two actions you can send to the server.

#### sendnotify
```
{"action": "sendnotify"}
```
This action will send an information to the client such as the last 20 messages stored in the DB, total users connected and total messages count

This action also will send information that client is connected to others connected clients.

#### sendmessage
```
{"action": "sendmessage", "message": "Hello..."}
```
This action will send the message to all connected clients
