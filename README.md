# mysoc-dataset

A python package and CLI to download mySociety datasets.

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

And the following will get the URL of the resource:

`mysoc-dataset url --repo uk_local_authority_names_and_codes --version latest --package uk_la_future --file uk_local_authorities_future.csv`

Use `mysoc-dataset --help` for more instructions. 

If using the CLI for a dataset, please fill out a survey of what you are using it for to help us explain the value of the data to funders. You can get a URL to the survey page using the 'survey' command. 

`mysoc-dataset survey --repo uk_local_authority_names_and_codes --version latest --package uk_la_future --file uk_local_authorities_future.csv`