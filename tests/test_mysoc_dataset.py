from typing import Any

import pytest
from mysoc_dataset import get_dataset_df, get_dataset_url, get_public_datasets
from mysoc_dataset.dataset import (
    FileNotFound,
    PackageNotFound,
    RepoNotFound,
    VersionNotFound,
)


def test_public_dataset_fetch_works():
    datasets = get_public_datasets()
    assert "https://mysociety.github.io/uk_local_authority_names_and_codes" in datasets


def test_get_dataset_url_works():
    url = get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
    )
    assert "uk_la_future" in url
    assert ".csv" in url
    assert "latest" in url


def test_full_url_works():
    url = get_dataset_url(
        "https://mysociety.github.io/uk_local_authority_names_and_codes/",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
    )
    assert "uk_la_future" in url
    assert ".csv" in url
    assert "latest" in url


def test_non_existant_file_raises_error():
    with pytest.raises(FileNotFound):
        get_dataset_url(
            "uk_local_authority_names_and_codes",
            "uk_la_future",
            "latest",
            "uk_local_authorities_future_nope.csv",
        )


def test_non_existant_version_raises_error():
    with pytest.raises(VersionNotFound):
        get_dataset_url(
            "uk_local_authority_names_and_codes",
            "uk_la_future",
            "b-latest",
            "uk_local_authorities_future_.csv",
        )


def test_non_existant_package_raises_error():
    with pytest.raises(PackageNotFound):
        get_dataset_url(
            "uk_local_authority_names_and_codes",
            "uk_la_future-d",
            "b-latest",
            "uk_local_authorities_future_.csv",
        )


def test_non_existant_repo_raises_error():
    with pytest.raises(RepoNotFound):
        get_dataset_url(
            "uk_local_authority_names_and_codes_blah",
            "uk_la_future-d",
            "b-latest",
            "uk_local_authorities_future_.csv",
        )


def test_survey_message(capsys: Any):
    get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
    )
    assert "can you tell us how using this survey" in capsys.readouterr().out


def test_survey_message_can_be_turned_off(capsys: Any):
    get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
        done_survey=True,
    )
    assert "can you tell us how using this survey" not in capsys.readouterr().out


def test_version_message(capsys: Any):
    get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "0.1.0",
        "uk_local_authorities_future.csv",
        done_survey=True,
    )
    assert "is not the latest version" in capsys.readouterr().out


def test_version_message_can_be_turned_off(capsys: Any):
    get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "0.1.0",
        "uk_local_authorities_future.csv",
        done_survey=True,
        ignore_version_warning=True,
    )
    assert "is not the latest version" not in capsys.readouterr().out


def test_no_version_message_for_latest(capsys: Any):
    get_dataset_url(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
        done_survey=True,
    )
    assert "is not the latest version" not in capsys.readouterr().out


def test_dataframe_load_works_ok():
    df = get_dataset_df(
        "uk_local_authority_names_and_codes",
        "uk_la_future",
        "latest",
        "uk_local_authorities_future.csv",
    )
    assert len(df) > 0
    assert "local-authority-code" in df.columns
