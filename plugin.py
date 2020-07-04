import os
import shutil
import subprocess

import sublime
from LSP.plugin import AbstractPlugin
from LSP.plugin.core.typing import Any, Dict, Optional, List


class PalantirPyls(AbstractPlugin):
    @classmethod
    def global_executable_requirements(cls) -> Optional[List[str]]:
        # TODO: Make this do something
        return [cls.python_exe()]

    @classmethod
    def name(cls) -> str:
        return "palantir-pyls"

    @classmethod
    def additional_variables(cls) -> Optional[Dict[str, str]]:
        variables = {}
        variables["sublime_py_files_dir"] = os.path.dirname(sublime.__file__)
        variables["sublime_packages_dir"] = sublime.packages_path()
        return variables

    @classmethod
    def basedir(cls) -> str:
        return os.path.join(sublime.cache_path(), "LSP-palantir-pyls")

    @classmethod
    def bindir(cls) -> str:
        return os.path.join(cls.basedir(), "bin")

    @classmethod
    def server_exe(cls) -> str:
        return os.path.join(cls.bindir(), "pyls")

    @classmethod
    def pip_exe(cls) -> str:
        return os.path.join(cls.bindir(), "pip")

    @classmethod
    def pyls_version_str(cls) -> str:
        settings = sublime.load_settings("LSP-palantir-pyls.sublime-settings")
        return str(settings.get("pyls_version"))

    @classmethod
    def black_version_str(cls) -> str:
        settings = sublime.load_settings("LSP-palantir-pyls.sublime-settings")
        return str(settings.get("pyls_black_version"))

    @classmethod
    def python_exe(cls) -> str:
        return "python" if sublime.platform() == "windows" else "python3"

    @classmethod
    def run(cls, *args: Any, **kwargs: Any) -> bytes:
        if sublime.platform() == "windows":
            startupinfo = subprocess.STARTUPINFO()  # type: ignore
            flag = subprocess.STARTF_USESHOWWINDOW  # type: ignore
            startupinfo.dwFlags |= flag
        else:
            startupinfo = None
        return subprocess.check_output(
            args=args, cwd=kwargs.get("cwd"), startupinfo=startupinfo)

    @classmethod
    def needs_update_or_installation(cls) -> bool:
        if os.path.exists(cls.server_exe()):
            if os.path.exists(cls.pip_exe()):
                pyls_needs_update = True
                black_needs_update = True
                for line in cls.run(
                        cls.pip_exe(), "list").decode("ascii").splitlines():
                    if line.startswith("python-language-server "):
                        length = len("python-language-server ")
                        stored_version_str = line[length:].strip()
                        if stored_version_str == cls.pyls_version_str():
                            pyls_needs_update = False
                    elif line.startswith("pyls-black "):
                        stored_version_str = line[len("pyls-black "):].strip()
                        if stored_version_str == cls.black_version_str():
                            black_needs_update = False
                return pyls_needs_update or black_needs_update
        return True

    @classmethod
    def install_or_update(cls) -> None:
        shutil.rmtree(cls.basedir(), ignore_errors=True)
        try:
            os.makedirs(cls.basedir(), exist_ok=True)
            cls.run(cls.python_exe(), "-m", "venv", "LSP-palantir-pyls",
                    cwd=sublime.cache_path())
            pyls = "python-language-server[all]=={}".format(
                cls.pyls_version_str())
            black = "pyls-black=={}".format(cls.black_version_str())
            mypy = "git+https://github.com/tomv564/pyls-mypy.git"
            cls.run(cls.pip_exe(), "install", pyls, black, mypy)
        except Exception:
            shutil.rmtree(cls.basedir(), ignore_errors=True)
            raise
