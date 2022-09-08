# mysoc-dataset

A python package and CLI to download mySociety datasets.

The best example of one of these datasets is: https://mysociety.github.io/uk_local_authority_names_and_codes/

These datasets are versioned [frictionless datapackages](https://frictionlessdata.io/). A repository may contain multiple data packages, each data package may contain multiple versions. A version of a datapackage will contain multiple resources (.csvs) and some composite files made up of resources (.xlsx or .sqlite). 


## Installation

It can be installed with:

```
python -m pip install mysoc-dataset
```

or if using poetry:

```
poetry add mysoc-dataset
```

## Usage

### As a package

The package has two basic functions (with helpful error messages) to access the url or a dataframe
of the resource.

```python
from mysoc_dataset import get_dataset_url, get_dataset_df

url = get_dataset_url(
    repo_name="uk_local_authority_names_and_codes",
    package_name="uk_la_future",
    version_name="latest",
    file_name="uk_local_authorities_future.csv",
)

# get a pandas dataframe
df = get_dataset_df(
    repo_name="uk_local_authority_names_and_codes",
    package_name="uk_la_future",
    version_name="latest",
    file_name="uk_local_authorities_future.csv",
)


```

### As a CLI

The CLI can be used to explore avaliable data using the `list` command, get the [frictionless datapackage](https://frictionlessdata.io/) that describes the repo using `detail` fetch the url with the `url` command or download the file using `download`.

This can be used to source files or pipe the URLs into other functions without writing python scripts. 

The CLI can either be run as `python -m mysoc_dataset` or `mysoc-dataset`. 

For instance, the following will print the `datapackage.json` that describes the underlying contents. 

`mysoc-dataset detail --repo uk_local_authority_names_and_codes --version latest --package uk_la_future`

And the following will get the URL of the resource, pegged to the `1` major version:

`mysoc-dataset url --repo uk_local_authority_names_and_codes --version 1 --package uk_la_future --file uk_local_authorities_future.csv`

If the dataset has had a major change, a warning will indicate this is no longer the latest version - while not introducing breaking changes to headers without the script being changed.

Use `mysoc-dataset --help` for more instructions. 

If using the CLI for a dataset, please fill out a survey of what you are using it for to help us explain the value of the data to funders. You can get a URL to the survey page using the 'survey' command. 

`mysoc-dataset survey --repo uk_local_authority_names_and_codes --version latest --package uk_la_future --file uk_local_authorities_future.csv`

# Maintenance

If the repo has a valid PYPI_TOKEN secret, and if the poetry version is bumped and all tests pass - the GitHub Action will automatically publish on push to the main branch.