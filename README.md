# discogs2music

Update your Music app album ratings with your Discogs ratings.

## Synopsis

This tool will try to update the album or songs rating value of your Music app
albums by getting the rating of the same album from your Discogs collection.

Differences in album/songs titles and the usage of special characters on
album/songs names may prevent the tool from recognizing the albums properly.

## Getting Started

There are a couple of things needed for the tool to work.

### Prerequisites

Python, version 3.6 or above, needs to be installed on your local computer.
You will also need a Discogs account.

#### Discogs

A Discogs user account is required (to obtain the ratings from). You can
create an account at [https://www.discogs.com/users/create](https://www.discogs.com/users/create)
if you do not have one already.

A Discogs personal token is also required. You can obtain one at
[https://www.discogs.com/settings/developers](https://www.discogs.com/settings/developers)

#### Python 3.x

Python version 3.6 or above is required for the tool to work. Python setup can
be found [here](https://www.python.org/downloads/).

The following python modules are also required to run the tool:

* appscript >= 1.1.2
* progress >= 1.5
* requests >= 2.25.1

### Build

It is recommended the use of a Python Virtual Environment (venv) to build this
tool. The same Virtual Environment can also be used to run the tool.

All of the commands described bellow are to be executed on the root folder of
this project.

A Virtual Environment can be created using the follow command:

```
python3 -m venv venv/
```

After creating the Virtual Environment the same will have to be activated, run
the following command to do that:

```
source venv/bin/activate
```

To build and run the tool some Python modules are required. These modules can
be installed using the following command:

```
pip3 --quiet install --upgrade --requirement requirements.txt build
```

Finaly the Python package for this tool can be created with the command:

```
python3 -m build --wheel
```

After this you should endup with wheel file (`*.whl`) inside a folder called
`dist`.

### Installation

The tool can be install using the wheel file and pip3:

```
pip3 --quiet install dist/discogs2music-*.whl
```

### Usage

```
usage: discogs2music [-h] -a APIKEY [-d DATAFILE] [--debug] [-l] [-o] [-q] [-s] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -a APIKEY, --apikey APIKEY
                        discogs api key (default: None)
  -d DATAFILE, --datafile DATAFILE
                        path to the datafile (default:
                        /Users/fscm/Documents/Projects/Active/discogs2music/discogs2music.json)
  --debug               debug mode (default: False)
  -l, --local           use local file only (does not query discogs for data) (default: False)
  -o, --override        override local data (default: False)
  -q, --quiet           quiet mode (default: False)
  -s, --songs           update songs rating instead of album rating (default: False)
  -v, --version         show program's version number and exit
```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request

Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details on how
to contribute to this project.

## Versioning

This project uses [SemVer](http://semver.org/) for versioning. For the versions
available, see the [tags on this repository](https://github.com/fscm/discogs2music/tags).

## Authors

* **Frederico Martins** - [fscm](https://github.com/fscm)

See also the list of [contributors](https://github.com/fscm/discogs2music/contributors)
who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details
