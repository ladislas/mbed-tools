#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib

import pytest

from unittest import mock

from mbed_tools.project._internal.libraries import MbedLibReference, LibraryReferences
from tests.project.factories import make_mbed_lib_reference


@pytest.fixture
def mock_clone():
    with mock.patch("mbed_tools.project._internal.git_utils.clone") as clone:
        yield clone


@pytest.fixture
def mock_checkout():
    with mock.patch("mbed_tools.project._internal.git_utils.checkout") as checkout:
        yield checkout


@pytest.fixture
def mock_get_repo():
    with mock.patch("mbed_tools.project._internal.git_utils.get_repo") as get_repo:
        yield get_repo


@pytest.fixture
def mock_get_default_branch():
    with mock.patch("mbed_tools.project._internal.git_utils.get_default_branch") as get_default_branch:
        yield get_default_branch


@pytest.fixture
def mock_repo():
    with mock.patch("mbed_tools.project._internal.git_utils.git.Repo") as repo:
        yield repo


class TestLibraryReferences:
    def test_hydrates_top_level_library_references(self, mock_clone, tmp_path):
        fs_root = pathlib.Path(tmp_path, "foo")
        lib = make_mbed_lib_reference(fs_root, ref_url="https://git")
        mock_clone.side_effect = lambda url, dst_dir: dst_dir.mkdir()

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.fetch()

        mock_clone.assert_called_once_with(lib.get_git_reference().repo_url, lib.source_code_path)
        assert lib.is_resolved()

    def test_hydrates_recursive_dependencies(self, mock_clone, tmp_path):
        fs_root = pathlib.Path(tmp_path, "foo")
        lib = make_mbed_lib_reference(fs_root, ref_url="https://git")
        # Create a lib reference without touching the fs at this point, we want to mock the effects of a recursive
        # reference lookup and we need to assert the reference was resolved.
        lib2 = MbedLibReference(
            reference_file=(lib.source_code_path / "lib2.lib"), source_code_path=(lib.source_code_path / "lib2")
        )
        # Here we mock the effects of a recursive reference lookup. We create a new lib reference as a side effect of
        # the first call to the mock. Then we create the src dir, thus resolving the lib, on the second call.
        mock_clone.side_effect = lambda url, dst_dir: (
            make_mbed_lib_reference(pathlib.Path(dst_dir), name=lib2.reference_file.name, ref_url="https://valid2"),
            lib2.source_code_path.mkdir(),
        )

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.fetch()

        assert lib.is_resolved()
        assert lib2.is_resolved()

    def test_does_perform_checkout_of_default_repo_branch_if_no_git_ref_exists(
        self, mock_get_repo, mock_checkout, mock_get_default_branch, mock_clone, tmp_path
    ):
        fs_root = pathlib.Path(tmp_path, "foo")
        make_mbed_lib_reference(fs_root, ref_url="https://git", resolved=True)

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.checkout(force=False)

        mock_checkout.assert_called_once_with(mock_get_repo(), mock_get_default_branch(), force=False)

    def test_performs_checkout_if_git_ref_exists(self, mock_get_repo, mock_checkout, mock_clone, tmp_path):
        fs_root = pathlib.Path(tmp_path, "foo")
        lib = make_mbed_lib_reference(fs_root, ref_url="https://git#lajdhalk234", resolved=True)

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.checkout(force=False)

        mock_checkout.assert_called_once_with(mock_get_repo.return_value, lib.get_git_reference().ref, force=False)

    def test_fetch_does_not_perform_checkout_if_no_git_ref_exists(
        self, mock_get_repo, mock_checkout, mock_clone, tmp_path
    ):
        fs_root = pathlib.Path(tmp_path, "foo")
        make_mbed_lib_reference(fs_root, ref_url="https://git")
        mock_clone.side_effect = lambda url, dst_dir: dst_dir.mkdir()

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.fetch()

        mock_checkout.assert_not_called()

    def test_fetch_performs_checkout_if_git_ref_exists(self, mock_get_repo, mock_checkout, mock_clone, tmp_path):
        fs_root = pathlib.Path(tmp_path, "foo")
        lib = make_mbed_lib_reference(fs_root, ref_url="https://git#lajdhalk234")
        mock_clone.side_effect = lambda url, dst_dir: dst_dir.mkdir()

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.fetch()

        mock_checkout.assert_called_once_with(None, lib.get_git_reference().ref)

    def test_does_not_resolve_references_in_ignore_paths(self, mock_get_repo, mock_checkout, mock_clone, tmp_path):
        fs_root = pathlib.Path(tmp_path, "mbed-os")
        make_mbed_lib_reference(fs_root, ref_url="https://git#lajdhalk234")

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.fetch()

        mock_clone.assert_not_called()

    def test_fetches_only_requested_ref(self, mock_repo, tmp_path):
        fs_root = pathlib.Path(tmp_path, "foo")
        fake_ref = "28eeee2b4c169739192600b92e7970dbbcabd8d0"
        make_mbed_lib_reference(fs_root, ref_url=f"https://git#{fake_ref}", resolved=True)

        lib_refs = LibraryReferences(fs_root, ignore_paths=["mbed-os"])
        lib_refs.checkout(force=False)

        mock_repo().git.fetch.assert_called_once_with("origin", fake_ref)
