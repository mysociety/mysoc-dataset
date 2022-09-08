"""
CLI App to download mySociety datasets
"""
import json
import urllib.request
from typing import Any, List

import rich
import rich_click as click
from rich.panel import Panel

from .dataset import DataRepo, get_dataset_options, get_dataset_url, get_public_datasets


class PanelPrint:
    """
    Helper for printing list of items in a panel
    """

    def __init__(self, expand: bool = False, **kwargs: Any) -> None:
        self.items: List[str] = []
        self.panel_properties = kwargs
        self.panel_properties["expand"] = expand

    def print(self, item: str) -> None:
        """
        Add item to panel
        """
        self.items.append(item)

    def display(self) -> None:
        """
        Display panel
        """
        panel = Panel("\n".join(self.items), **self.panel_properties)
        rich.print(panel)


@click.group()  # type: ignore
def cli():
    """
    cli manager for mysoc dataset
    """


@cli.command("list")
@click.option("--repo", help="Data repo name", default="")
@click.option("--package", help="Package name", default="")
@click.option("--version", help="Version name", default="")
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
def do_list(
    repo: str = "", package: str = "", version: str = "", use_json: bool = False
):
    """
    Depending which options have a non blank value, display a list of avaliable repos,
    packages, versions, or files.
    """
    # can't have a set version and not a set package and repo
    if version and not (package and repo):
        raise click.ClickException("Can't set version without package and repo")
    # can't have a set package and not a set repo
    if package and not repo:
        raise click.ClickException("Can't set package without repo")

    if repo == "":
        title = "Public data repos"
        items = get_public_datasets()
    elif package == "":
        title = f"Packages in {repo}"
        items = DataRepo(repo).list_packages()
    elif version == "":
        title = f"Versions in {repo},{package}"
        items = DataRepo(repo).get_package(package).list_versions()
    else:
        title = f"Files in {repo},{package},{version}"
        items = DataRepo(repo).get_package(package).get_version(version).get_filenames()

    # create a rich
    if use_json:
        rich.print(json.dumps(items))
    else:
        p = PanelPrint(
            padding=1,
            style="blue",
            title=title,
            subtitle="See more options with `--help`",
        )
        for item in items:
            rich.print(f"[green]{item}[/green]")
        p.display()


@cli.command("survey")
@click.option("--repo", help="Data repo name")
@click.option("--package", help="Package name")
@click.option("--version", help="Version name", default="latest")
@click.option("--file", "filename", help="file name")
def survey(
    repo: str,
    package: str,
    version: str,
    filename: str,
):
    """
    Retrieve and print the survey url of a file
    """
    if not repo:
        raise click.ClickException("Must provide repo")
    if not package:
        raise click.ClickException("Must provide package")
    if not version:
        raise click.ClickException("Must provide version")
    if not filename:
        raise click.ClickException("Must provide file")

    data_package_url = get_dataset_options(repo, package, version, filename)
    rich.print(data_package_url.survey_link)


@cli.command("url")
@click.option("--repo", help="Data repo name")
@click.option("--package", help="Package name")
@click.option("--version", help="Version name", default="latest")
@click.option("--file", "filename", help="file name")
def get_url(
    repo: str,
    package: str,
    version: str,
    filename: str,
):
    """
    Retrieve and print the url of a file
    """
    if not repo:
        raise click.ClickException("Must provide repo")
    if not package:
        raise click.ClickException("Must provide package")
    if not version:
        raise click.ClickException("Must provide version")
    if not filename:
        raise click.ClickException("Must provide file")

    data_package_url = get_dataset_url(
        repo, package, version, filename, done_survey=True
    )
    rich.print(data_package_url)


@cli.command()
@click.option("--repo", help="Data repo name")
@click.option("--package", help="Package name")
@click.option("--version", help="Version name", default="latest")
@click.option("--file", "filename", help="file name")
@click.option(
    "--dest-dir", "dest_path", help="Destination directory (optional)", default=""
)
@click.option("--done-survey", help="Turns off nag prompt", is_flag=True)
def download(
    repo: str,
    package: str,
    version: str,
    filename: str,
    dest_path: str,
    done_survey: bool = False,
):
    """
    Retrieve and print the url of a file
    """
    if not repo:
        raise click.ClickException("Must provide repo")
    if not package:
        raise click.ClickException("Must provide package")
    if not version:
        raise click.ClickException("Must provide version")
    if not filename:
        raise click.ClickException("Must provide file")

    data_package_url = get_dataset_url(
        repo, package, version, filename, done_survey=done_survey
    )

    # extract file name from url
    file_name = data_package_url.split("/")[-1]

    if dest_path:
        file_name = dest_path + "/" + file_name
    else:
        file_name = "./" + file_name

    # download file
    urllib.request.urlretrieve(data_package_url, file_name)
    rich.print(f"[green]Downloaded file[/green] to {file_name}")


@cli.command("detail")
@click.option("--repo", help="Data repo name")
@click.option("--package", help="Package name")
@click.option("--version", help="Version name", default="latest")
def detail(
    repo: str,
    package: str,
    version: str,
):
    """
    Retrieve and print the frictionless datapackage.json file
    """
    if not repo:
        raise click.ClickException("Must provide repo")
    if not package:
        raise click.ClickException("Must provide package")
    if not version:
        raise click.ClickException("Must provide version")

    data_package_url = get_dataset_url(
        repo, package, version, "datapackage.json", done_survey=True
    )
    # open url and load package into json
    with urllib.request.urlopen(data_package_url) as response:
        data_package = json.load(response)
    rich.print(data_package)


def main():
    """
    Main function to run
    """
    cli()


if __name__ == "__main__":
    main()
