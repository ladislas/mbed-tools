#
# Copyright (C) 2020 Arm Mbed. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
import pathlib

from tempfile import TemporaryDirectory
from unittest import mock

import pytest

from mbed_tools.build.build import build_project, generate_build_system
from mbed_tools.build.exceptions import MbedBuildError


@pytest.fixture
def cmake_wrapper():
    with mock.patch("mbed_tools.build.build._cmake_wrapper") as cmake:
        yield cmake


class TestBuildProject:
    def test_invokes_cmake_with_correct_args(self, cmake_wrapper):
        build_project(build_dir="cmake_build", target="install")

        cmake_wrapper.assert_called_once_with("--build", "cmake_build", "--target", "install")

    def test_invokes_cmake_with_correct_args_if_no_target_passed(self, cmake_wrapper):
        build_project(build_dir="cmake_build")

        cmake_wrapper.assert_called_once_with("--build", "cmake_build")

    def test_raises_build_error_if_build_dir_doesnt_exist(self):
        with TemporaryDirectory() as tmp_dir:
            nonexistent_build_dir = pathlib.Path(tmp_dir, "cmake_build")

            with pytest.raises(MbedBuildError):
                build_project(nonexistent_build_dir)


class TestConfigureProject:
    def test_invokes_cmake_with_correct_args(self, cmake_wrapper):
        source_dir = "source_dir"
        build_dir = "cmake_build"
        profile = "debug"

        generate_build_system(source_dir, build_dir, profile)

        cmake_wrapper.assert_called_once_with(
            "-S", source_dir, "-B", build_dir, "-GNinja", f"-DCMAKE_BUILD_TYPE={profile}"
        )
