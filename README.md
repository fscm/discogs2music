**[LEGACY] This branch is no longer maintained**
> While this project is fully active, this branch is no longer maintained and therefore is no longer up to date. You are still welcome to explore, learn, and use the code provided here.

# discogs2itunes

Update your iTunes album ratings with your Discogs ratings.

## Synopsis

This script will try to update the album or songs rating value of your iTunes
albums by getting the rating of the same album from your Discogs collection.

Differences in album/songs titles and the usage of special characters on
album/songs names may prevent the script from recognizing the albums properly.

The script is available on both Ruby and Python. Both versions will perform the
same tasks however, due to the way that both languages deal with character
encoding, normalization and parametrization, the results may be different.
Please use the one that produces the best results for your iTunes library.

## Getting Started

There are a couple of things needed for either of the scripts to work.

### Prerequisites

Follow the instructions for the version of the script that you wish to use.
Discogs instructions are required for both versions.

#### Discogs

A Discogs user account is required (to obtain the ratings from). You can
create an account at [https://www.discogs.com/users/create](https://www.discogs.com/users/create)
if you do not have one already.

A Discogs personal token is also required. You can obtain one at
[https://www.discogs.com/settings/developers](https://www.discogs.com/settings/developers)


#### Ruby

For the Ruby version of the script the following gems are required:

* getoptlong
* json
* open-uri
* progress_bar
* rb-appscript
* unidecoder

You can install gems with:

```
sudo gem install <gem_name>
```

#### Python

For the Python version of the script the following modules are required:

* appscript
* getopt
* json
* os.path
* progress
* re
* requests
* sys
* time
* unidecode

You can install modules with:

```
sudo pip install <module_name>
```

The python script will also require openssl version 1.0. This script will not
be able to connect to Discogs using TLS with the default openssl version on
Mac OS X (which is 0.9.8).

### Installation

Nothing special to be done. Just download the version of the script that you
wish to use.

### Usage

Both versions of the script use the same arguments.

#### Ruby

```
Usage:
  discogs2itunes.rb -u <username> -k <apikey> [-f <filename>] [-h] [-o] [-s]
Options:
  -f, --datafile <filename>  datafile name (optional)
  -h, --help                 show help (optional)
  -k, --apikey <api_key>     discogs api key
  -o, --override             override local values (optional)
  -s, --songs                update itunes songs rating instead of album rating (optional)
  -u, --username <username>  discogs username
```

#### Python

```
Usage:
  discogs2itunes.py -u <username> -k <apikey> [-f <filename>] [-h] [-o] [-s]
Options:
  -f, --datafile <filename>    datafile name (optional)
  -h, --help                   show help (optional)
  -k, --apikey <api_key>       discogs api key
  -o, --override               override local values (optional)
  -s, --songs                  update itunes songs rating instead of album rating (optional)
  -u, --username <username>    discogs username
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
available, see the [tags on this repository](https://github.com/fscm/discogs2itunes/tags).

## Authors

* **Frederico Martins** - [fscm](https://github.com/fscm)

See also the list of [contributors](https://github.com/fscm/discogs2itunes/contributors) 
who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) 
file for details
