import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import rich

PUBLIC_URL_LIST = "https://data.mysociety.org/datarepos.json"
DEFAULT_DATAREPO_DOMAIN = "https://mysociety.github.io"


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


def get_public_datasets() -> List[str]:
    """
    Fetch the public url list, which is a list of URLs under a "datarepos" key.
    and return this list
    """
    with urllib.request.urlopen(PUBLIC_URL_LIST) as url:
        data = json.loads(url.read().decode())
        return data["datarepos"]


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
            self.url = f"{DEFAULT_DATAREPO_DOMAIN}/{data_repo_ref}"

        self.data = self._fetch_data()
        self.packages: Dict[str, Package] = {}
        for slug, package in self.data.items():
            self.packages[slug] = Package.from_data(slug, package)

    def _fetch_data(self):
        """
        retrieve the data.json file from the data repo
        """
        try:
            with urllib.request.urlopen(f"{self.url}/data.json") as url:
                data = json.loads(url.read().decode())
                return data
        except urllib.error.HTTPError as exc:
            raise RepoNotFound(
                f"Data repo not found: {self.url}. Available repos: {get_public_datasets()}"
            ) from exc

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
    """
    dataset_url = get_dataset_url(
        repo_name,
        package_name,
        version_name,
        file_name,
        ignore_version_warning,
        done_survey,
    )
    return pd.read_csv(dataset_url)  # type:ignore
