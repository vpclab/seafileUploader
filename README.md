# Seafile Uploader

A package used to upload files to a Seafile server.

## Example

Before viewing the example, you need to put a valid username/email and password into the `example.ini` file. Once that is completed, you can run the example script.

You can view the example by executing `python seafileUploader/example.py` in the module's home folder. This will upload all files in the `./localTestFiles` directory to [here](https://drive.vpclab.com/#group/3/lib/1add79d4-2363-4521-b240-6d6830bb336a) where you can view them through a web interface (You must also log into the web interface).

## Logical example

Things that the uploader requires to work:

* **Local** files directory
* **Remote** files directory
* Seafile repository **ID**
* Seafile server **username**
* Seafile server **password**

This information can be given to the uploader in the form of an ini config file:

```py
uploader = seafileUploader.SeafileUploader(configFilePath='./example.ini')
```

Or it can be given as a dictionary:

```py
settings = {
    'local_path': 'localTestFiles',
    'remote_path': 'remoteTestFiles',
    'resting_path': 'uploaded',
    'repo_id': '1add79d4-2363-4521-b240-6d6830bb336a',
    'username': 'data@vpclab.com',
    'password': '{password}',
}

uploader = seafileUploader.SeafileUploader(**settings)
```

Once the setting have been configured, all you have to do is start the upload process and the seafileUploader module should take care of the rest:

```py
uploader.start()
```