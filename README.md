# dspyce
## Table of Contents
1. [Description](#description)
2. [Contents](#contents)
   1. [packages](#packages)
   2. [UML-Diagramm](#uml-diagramm)
3. [Requirements](#requirements)

## Description
The package **dspyce** helps to communicate with dspace interfaces. Currently, 
[saf (Simple Archive Format)](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/saf) packages and the [RestAPI](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/rest) are supported.

## Contents
The **dspyce** packages contains the following classes and packages.

### packages
1. [bitstreams](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/bitstreams) -> The package for managing DSpace bitstream objects.
2. [metadata](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/metadata) -> The package manages the handling of DSpace metadata information.
3. [saf](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/rest) -> The saf packages helps you to create saf packages based on given DSpaceObject objects.
4. [rest](https://github.com/dspace-unimr/dspyce/tree/main/dspyce/saf) -> The rest packages handles the communication with the RestAPI of a given DSpace instance.


## Requirements
Requirements are defined in [requirements.txt](https://github.com/dspace-unimr/dspyce/blob/main/requirements.txt), to use the package a python
version >= 3.10 is necessary.
> python >= 3.10
```shell
pip install -r requirements.txt
```
