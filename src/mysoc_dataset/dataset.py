import functools
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List

import pandas as pd
import rich

# URL to consult for public repos and default settings
PUBLIC_URL_LIST = "https://data.mysociety.org/datarepos.json"

# Default domain to fall back on if lookup to above fails
DEFAULT_DATAREPO_DOMAIN = "https://mysociety.github.io"


def timed_cache(**timedelta_kwargs: Any):
    """
    Cache with timedelta timeout
    """

    def _wrapper(f: Callable[..., Any]):
        update_delta = timedelta(**timedelta_kwargs)
        next_update = datetime.utcnow() + update_delta
        # Apply @lru_cache to f with no cache size limit
        f = functools.lru_cache(None)(f)

        @functools.wraps(f)
        def _wrapped(*args: Any, **kwargs: Any):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta
            return f(*args, **kwargs)

        return _wrapped

    return _wrapper


class RepoNotFound(Exception):
    """
    Error to raise if REPO_URL/data.json is not found
    """


class PackageNotFound(Exception):
    """
    Error to raise if a package has been given but isn't avaliable in that repo
    """


class VersionNotFound(Exception):
    """
    Error to raise if a specified version of a package is not avaliable
    """


class FileNotFound(Exception):
    """
    Error to raise if a specified file in a verison is not avaliable
    """


def valid_url(url: str) -> bool:
    """
    check if url is a URL format
    """
    if "https://" in url or "http://" in url:
        return True
    return False


@timed_cache(minutes=1)
def fetch_data_repo(url: str) -> Dict[str, Any]:
    """
    retrieve the data.json file from the data repo
    """
    try:
        with urllib.request.urlopen(url) as url_conn:
            data = json.loads(url_conn.read().decode())
            return data
    except urllib.error.HTTPError as exc:
        raise RepoNotFound(
            f"Data repo not found: {url}. Available repos: {get_public_datasets()}"
        ) from exc


def uncached_get_datarepos_json() -> Dict[str, Any]:
    """
    Retrieve the public URL list - but fail softly and return a {} if nothing found
    """
    try:
        with urllib.request.urlopen(PUBLIC_URL_LIST) as url:
            data = json.loads(url.read().decode())
            return data
    except urllib.error.HTTPError:
        rich.print(
            "[red]Could not access the datarepos.json file. Using default configurations[/red]"
        )
        return {}


# version that is cached for a minute
get_datarepos_json = timed_cache(minutes=1)(uncached_get_datarepos_json)


def get_default_domain() -> str:
    """
    Get the default domain for the data repos
    """
    return get_datarepos_json().get("default_domain", DEFAULT_DATAREPO_DOMAIN)


def get_public_datasets() -> List[str]:
    """
    Fetch the public url list, which is a list of URLs under a "datarepos" key.
    and return this list
    """
    return get_datarepos_json().get("datarepos", [])


@dataclass
class Download:
    """
    A downloadable resource
    """

    slug: str
    url: str
    survey_link: str

    @classmethod
    def load(cls, slug: str, data: Dict[str, Any]) -> "Download":
        """
        Load a download from a dictionary
        """
        return Download(
            slug=slug,
            url=data["url"],
            survey_link=data["survey_link"],
        )


@dataclass
class PackageVersion:
    """
    A collection of downloadable resources associated with a version of a package
    """

    version: str  # short version (may be '1', or 'latest')
    full_version: str  # semvar version
    downloads: Dict[str, Download]

    @classmethod
    def load(cls, slug: str, data: Dict[str, Any]) -> "PackageVersion":
        """
        Load a package version from a dictionary
        """
        return PackageVersion(
            version=slug,
            full_version=data["full_version"],
            downloads={
                slug: Download.load(slug, download)
                for slug, download in data["files"].items()
            },
        )

    def get_filenames(self) -> List[str]:
        """
        Get all downloads
        """
        urls = [x.url for x in self.downloads.values()]
        # extract final filename from url
        return [x.split("/")[-1] for x in urls]

    def get_file(self, slug: str) -> Download:
        """
        Get a download by slug
        """
        try:
            return self.downloads[slug]
        except KeyError as exc:
            raise FileNotFound(
                f"File not found: {slug}. Available files: {list(self.downloads.keys())}"
            ) from exc


@dataclass
class Package:
    """
    A collection of versions of the same package
    """

    slug: str
    latest_version: str
    versions: Dict[str, PackageVersion]

    @classmethod
    def from_data(cls, slug: str, data: Dict[str, Any]):
        """
        Load a package from a dictionary
        """
        return Package(
            slug=slug,
            latest_version=data["latest_version"],
            versions={
                slug: PackageVersion.load(slug, version)
                for slug, version in data["versions"].items()
            },
        )

    def list_versions(self) -> List[str]:
        """
        List all versions of a package
        """
        return list(self.versions.keys())

    def get_version(
        self, version: str, ignore_version_warning: bool = False
    ) -> PackageVersion:
        """
        Get a specific version of a package
        """
        if version not in self.versions:
            raise VersionNotFound(
                f"Version {version} not found. Available versions are {self.list_versions()}"
            )
        version_obj = self.versions[version]

        # raise warning if version is not a full 'x.x.x' semver and version is not self.latest_version
        if version_obj.full_version != self.latest_version:
            if not ignore_version_warning:
                rich.print(
                    f"[yellow]Version {version} of {self.slug} is not the latest version. Latest version is {self.latest_version}[/yellow]"
                )

        return version_obj


class DataRepo:
    """
    Management for the DataRepo level

    Given either a full url, or a data repo name
    Fetch and unpack the data.json to understand resoruces
    """

    def __init__(self, data_repo_ref: str):
        if valid_url(data_repo_ref):
            self.url = data_repo_ref
        else:
            self.url = f"{get_default_domain()}/{data_repo_ref}"

        self.data = fetch_data_repo(f"{self.url}/data.json")
        self.packages: Dict[str, Package] = {}
        for slug, package in self.data.items():
            self.packages[slug] = Package.from_data(slug, package)

    def list_packages(self) -> List[str]:
        """
        List all packages in the data repo
        """
        return list(self.packages.keys())

    def get_package(self, slug: str) -> Package:
        """
        Get a package by slug. Raise PackageNotFound if not found.
        """
        try:
            return self.packages[slug]
        except KeyError as exc:
            raise PackageNotFound(
                f"Package {slug} not found. Available packages: {self.list_packages()}"
            ) from exc


def get_dataset_options(
    repo_name: str,
    package_name: str,
    version_name: str,
    file_name: str,
    ignore_version_warning: bool = False,
) -> Download:
    """
    Get a URL for a specific file in a specific version of a package in a specific data repo
    """
    repo = DataRepo(repo_name)
    package = repo.get_package(package_name)
    version = package.get_version(version_name, ignore_version_warning)
    file = version.get_file(file_name)
    return file


def get_dataset_url(
    repo_name: str,
    package_name: str,
    version_name: str,
    file_name: str,
    ignore_version_warning: bool = False,
    done_survey: bool = False,
) -> str:
    """
    Get a URL for a specific file in a specific version of a package in a specific data repo.

    Args:
        repo_name (str): The name of the data repo either the subfolder of the mysociety default domain or a full URL
        package_name (str): The name of the datapackage in the repo
        version_name (str): The name of the version - may be a full semvar version, a major or minor version, or 'latest'
        file_name (str): The name of the file to download that is part of the package (usually a .csv)
        ignore_version_warning (bool, optional): Ignore the warning if the version is not the latest. Defaults to False.
        done_survey (bool, optional): Have you completed the survey? Defaults to False. Nagging message displayed if not.

    Returns:
        str: The URL to download the file from


    """
    dataset_obj = get_dataset_options(
        repo_name, package_name, version_name, file_name, ignore_version_warning
    )
    if done_survey is False:
        rich.print(
            f"If you find [blue]{package_name}[/blue] helpful, can you tell us how using this survey? {dataset_obj.survey_link}. This message can be removed by setting the `done_survey` option to True."
        )
    return dataset_obj.url


def get_dataset_df(
    repo_name: str,
    package_name: str,
    version_name: str,
    file_name: str,
    ignore_version_warning: bool = False,
    done_survey: bool = False,
) -> pd.DataFrame:
    """
    Get a pandas dataframe for a specific file in a specific version of a package in a specific data repo.
    Get a URL for a specific file in a specific version of a package in a specific data repo.

    Args:
        repo_name (str): The name of the data repo either the subfolder of the mysociety default domain or a full URL
        package_name (str): The name of the datapackage in the repo
        version_name (str): The name of the version - may be a full semvar version, a major or minor version, or 'latest'
        file_name (str): The name of the file to download that is part of the package (usually a .csv)
        ignore_version_warning (bool, optional): Ignore the warning if the version is not the latest. Defaults to False.
        done_survey (bool, optional): Have you completed the survey? Defaults to False. Nagging message displayed if not.

    Returns:
        pd.DataFrame: The dataframe of the file
    """
    dataset_url = get_dataset_url(
        repo_name,
        package_name,
        version_name,
        file_name,
        ignore_version_warning,
        done_survey,
    )
    if file_name.endswith(".csv"):
        return pd.read_csv(dataset_url)  # type:ignore
    elif file_name.endswith(".parquet"):
        return pd.read_parquet(dataset_url)
    else:
        raise ValueError(
            f"""
            File type not supported. Only .csv and .parquet are supported. File {file_name} is not supported. 
            Use `get_dataset_url` to get the URL for the file."
            """
        )
