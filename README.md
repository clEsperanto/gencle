# GenCle : clEsperanto code generator

clEsperanto auto-generation code library and scripts. A large part of the python, java, and cpp user API are autogenerated from the low-level library CLIc.
This repository hold python package and script collection to parse the documentation of the CLIc library and generate the code and documentation blocks of the following upstream libraries:
* [`pyclesperanto`](https://github.com/clEsperanto/pyclesperanto) :snake:
* [`ClesperantoJ`](https://github.com/clEsperanto/clesperantoj_prototype) :coffee:
* [`CLIJ3`](https://github.com/clEsperanto/cclij3) :coffee:
* [`Clesperanto`]() :rocket:

## Local install

As this is a very specific usage package and not relevant for high-level user of clEsperanto, we did not deploy any package. 
Clone the repository:
```
git clone https://github.com/clesperanto/gencle
```
Create a environement for running the jupyter notebook
```
mamba create -n gencle && mamba activate gencle
```

## Usage

Primary usage of this repo is by [cle-roboto](https://github.com/clEsperanto/cle-roboto-repo) CI action which will run the corresponding update script based on release.

Update script follow the same command:
```bash
python pyclesperanto_auto_update.py <PATH_TO_PYCLESPERANTO_FOLDER> <VERSION_TAG_TO_UPDATE_TO>
```

List of script updating from a `CLIc` release:
* :snake: [pyclesperanto update script](updates_scripts/pyclesperanto_auto_update.py)
* :coffee: [ClesperantoJ update script](updates_scripts/clesperantoj_auto_update.py)
* :rocket: [Clesperanto update script]() (WIP)

List of script updating from a `clesperantoj` release:
* :coffee: [CLIJ3 update script](updates_scripts/pclij3_auto_update.py)

## ToDo:

* Expend package to auto-generate Cpp code
* Explore better parser solution
