<p align="center">
<img src="https://socialify.git.ci/jairmedeiros/tarchia/image?description=1&amp;font=Jost&amp;language=1&amp;name=1&amp;pattern=Plus&amp;theme=Auto" alt="project-image"></p>

<h2>🛠️ Installation Steps:</h2>

1. Install dependencies

```
pip install -r requirements.txt
```

2. Run the CLI

```
python ./main.py
```

<h2>🤔 Usage:</h2>

```
usage: tarchia [-h] [-i] [-o ORIGIN] -t TAG [--no-dxp] {deploy,forceDeploy} module

A python script to update Liferay Site Initializers

positional arguments:
  {deploy,forceDeploy}  set the command to be used to build the Site Initializer project
  module                set the Site Initializer project module path

options:
  -h, --help            show this help message and exit
  -i, --ignore          ignore master reset process (default: False)
  -o ORIGIN, --origin ORIGIN
                        set the git origin to fetch new changes from master branch (default: upstream)
  -t TAG, --tag TAG     set tag of Liferay version (eg. 7.4.3.81-ga81) (default: None)
  --no-dxp              disable DXP profile setup before build Liferay instance (default: False)

```

<h2>💻 Built with</h2>

Technologies used in the project:

* [jproperties](https://github.com/Tblue/python-jproperties)
* [alive-progress](https://github.com/rsalmei/alive-progress)
