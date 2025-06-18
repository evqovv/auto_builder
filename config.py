import os
from pathlib import Path
from typing import Dict, Any, List

git_dir: Path = None
build_dir: Path = None
install_dir: Path = None

host: str = None
target: str = None

with_lib32: bool = None

clean_git: bool = None
clean_build: bool = None

update_env: bool = None

configure: Dict[str, Path] = {}

bashrc_path: Path = Path(os.path.expanduser("~")) / ".bashrc"

package_downloaders: Dict[str, List[str]] = {
    "apt": ["sudo", "apt", "install", "-y"],
    "pacman": ["sudo", "pacman", "-S", "--needed", "--noconfirm"],
    "dnf":  ["sudo", "dnf", "install", "-y"],
    "yum": ["sudo", "yum", "install", "-y"],
}


class name:
    x86_64_linux_gnu: str = "x86_64-linux-gnu"
    x86_64_w64_mingw32: str = "x86_64-w64-mingw32"
    binutils_gdb: str = "binutils-gdb"
    gcc: str = "gcc"
    mingw_w64: str = "mingw-w64"
    mingw_w64_headers: str = "mingw-w64-headers"
    mingw_w64_crt: str = "mingw-w64-crt"
    env_path: str = "PATH"
    env_ld_library_path: str = "LD_LIBRARY_PATH"
    gmp: str = "gmp"
    mpfr: str = "mpfr"
    mpc: str = "mpc"
    isl: str = "isl"
    gettext: str = "gettext"


git_module_path: Dict[str, List[str]] = {
    name.binutils_gdb: [name.binutils_gdb],
    name.gcc: [name.gcc],
    name.mingw_w64_headers: [name.mingw_w64, name.mingw_w64_headers],
    name.mingw_w64_crt: [name.mingw_w64, name.mingw_w64_crt],
}

env: Dict[str, str] = os.environ.copy()

cwd: Path = Path(os.getcwd())

build_cwd: Dict[str, Path] = {}

install_path: Dict[str, Path] = {}

is_cross_compiling: bool = None
is_canadian_compiling: bool = None

apt_required_pkgs: List[str] = [
    "build-essential",
    "libgmp-dev",
    "libmpc-dev",
    "libmpfr-dev",
    "libisl-dev",
    "git",
    "flex",
    "bison",
    "texinfo",
]

pacman_required_pkgs: List[str] = [
    "base-devel",
    "gmp",
    "libmpc",
    "mpfr",
    "isl",
    "git",
]

yum_required_pkgs: List[str] = [
    "gcc",
    "g++",
    "make",
    "gmp-devel",
    "libmpc-devel",
    "mpfr-devel",
    "isl-devel",
    "git",
    "flex",
    "bison",
    "texinfo",
]

dnf_required_pkgs: List[str] = yum_required_pkgs

required_pkgs: Dict[str, List[str]] = {
    "apt": apt_required_pkgs,
    "pacman": pacman_required_pkgs,
    "dnf": dnf_required_pkgs,
    "yum": yum_required_pkgs,
}

repos: Dict[str, str] = {
    name.binutils_gdb: "git://sourceware.org/git/binutils-gdb.git",
    name.gcc: "git://gcc.gnu.org/git/gcc.git",
    name.mingw_w64: "https://git.code.sf.net/p/mingw-w64/mingw-w64",
}

canadian_required_pkgs: Dict[str, str] = {
    name.gmp: "https://ftp.gnu.org/gnu/gmp/gmp-6.2.1.tar.bz2",
    name.mpfr: "https://ftp.gnu.org/gnu/mpfr/mpfr-4.1.0.tar.bz2",
    name.mpc: "https://ftp.gnu.org/gnu/mpc/mpc-1.2.1.tar.gz",
    name.isl: "https://gcc.gnu.org/pub/gcc/infrastructure/isl-0.24.tar.bz2",
    name.gettext: "https://ftp.gnu.org/gnu/gettext/gettext-0.22.tar.gz",
}

max_retries: int = 10
retry_delay: int = 5

build: str = "x86_64-linux-gnu"
host: str = ""
target: str = ""


class default_args:
    host: str = "x86_64-linux-gnu"
    target: str = "x86_64-linux-gnu"


arguments: Dict[str, Dict[str, Any]] = {
    "git-dir": {
        "type": Path,
        "help": "Path to the git source directory."
    },

    "build-dir": {
        "type": Path,
        "help": "Path to the build directory."
    },

    "install-dir": {
        "type": Path,
        "help": "Path to the installation directory."
    },

   	"cwd": {
        "type": Path,
        "help": "Path to the current working directory."
    },

    "host": {
        "type": str,
        "default": default_args.host,
        "choices": ["x86_64-linux-gnu", "x86_64-w64-mingw32"],
        "help": "The host system of the toolchain."
    },

    "target": {
        "type": str,
        "default": default_args.target,
        "choices": ["x86_64-linux-gnu", "x86_64-w64-mingw32"],
        "help": "The target system of the toolchain."
    },

    "binutils-gdb-git-repo-url": {
        "type": str,
        "help": "Specify the Git repository URL for binutils-gdb."
    },

    "gcc-git-repo-url": {
        "type": str,
        "help": "Specify the Git repository URL for GCC."
    },

    "mingw-w64-git-repo-url": {
        "type": str,
        "help": "Specify the Git repository URL for mingw-w64."
    },

    "with-lib32": {
        "action": "store_true",
        "help": "Enable multilib, with lib32."
    },

    "clean-git": {
        "action": "store_true",
        "help": "Delete the git directory after building. If not created by this program, only related subdirectories will be removed."
    },

    "clean-build": {
        "action": "store_true",
        "help": "Delete the build directory after building. If not created by this progrm, only related subdirectories will be removed."
    },

    "update-env": {
        "action": "store_true",
        "help": "Update the environment variables automatically after building."
    },
}
