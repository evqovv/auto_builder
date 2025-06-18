import os
import subprocess
import argparse
import config
import shutil
import re
from time import sleep
from collections.abc import Callable
from typing import Dict, List, Any
from typing import Tuple
from pathlib import Path


def install_required_pkgs() -> None:
	for mgr, install_cmd in config.package_downloaders.items():
		if shutil.which(mgr):
			cmd = install_cmd + config.required_pkgs[mgr]
			subprocess.run(cmd, check=True, env=config.env)
			return

	raise RuntimeError(
		"No supported package manager (apt, pacman, dnf, yum) found.")


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser("auto_builder")
	for key, value in config.arguments.items():
		parser.add_argument(f"--{key}", **value)

	return parser


def parse_args() -> argparse.Namespace:
	parser = build_parser()
	return parser.parse_args()


def do_git_clone(repo_name: str, repo_url: str,
                 max_retries: int = config.max_retries,
                 retry_delay: int = config.retry_delay) -> None:
	for attempt in range(1, max_retries + 1):
		ret = subprocess.run(["git", "clone", "--depth=1",
	                       repo_url, repo_name], cwd=config.git_dir, check=False, env=config.env)

		if ret.returncode == 0:
			return

		print(
			f"Warning: Git clone failed (attempt {attempt}/{max_retries}). Retrying in {retry_delay} seconds...")

		sleep(retry_delay)

	raise RuntimeError(
		"Error: Git failed the maximum number of times. Please check if your network is working properly.")


def do_git_pull(repo_name: str) -> subprocess.CalledProcessError:
	return subprocess.run(["git", "-C", repo_name, "pull", "--ff-only"], cwd=config.git_dir, check=False, env=config.env)


def do_git(repo_name: str, repo_url: str) -> None:
	path: Path = config.git_dir / repo_name

	if not Path(path).exists():
		do_git_clone(repo_name, repo_url)
	elif Path(path).is_dir():
		do_git_pull(repo_name)
	else:
		raise RuntimeError("File name conflict.")


def git_repos(repos: Dict[str, str]) -> None:
	for name, url in repos.items():
		do_git(name, url)


def is_withlib32() -> List[str]:
	if config.with_lib32:
		return ["--enable-multilib", "--with-multilib-list=m64,m32"]
	else:
	   return ["--disable-multilib"]


def binutils_gdb_configure() -> List[str]:
	ret: List[str] = [
		config.configure[config.name.binutils_gdb],
		f"--prefix={config.install_dir}",
		f"--build={config.build}",
		f"--host={config.host}",
		f"--target={config.target}",
		"--disable-nls",
		"--disable-werror",
		*(["--enable-gold"] if config.target == config.name.x86_64_linux_gnu else []),
		*(["--with-python3"] if (config.host == config.name.x86_64_linux_gnu) or (config.host == config.name.x86_64_w64_mingw32 and config.with_python3) else [])
	]

	ret.extend(is_withlib32())

	return ret


def gcc_configure() -> List[str]:
	ret: List[str] = [
		config.configure[config.name.gcc],
		f"--prefix={config.install_dir}",
		f"--build={config.build}",
		f"--host={config.host}",
		f"--target={config.target}",
		"--disable-nls",
		"--disable-werror",
		"--disable-libstdcxx-verbose",
		"--disable-bootstrap",
		"--enable-languages=c,c++",
		*(["--disable-sjlj-exceptions"] if config.target == config.name.x86_64_w64_mingw32 else [])
	]

	ret.extend(is_withlib32())

	return ret


def mingw32_headers_configure() -> List[str]:
	ret: List[str] = [
		config.configure[config.name.mingw_w64_headers],
		f"--prefix={config.install_dir / config.target}",
		f"--build={config.build}",
		f"--host={config.name.x86_64_w64_mingw32}",
		f"--targe={config.name.x86_64_w64_mingw32}",
	]

	return ret


def mingw32_crt_configure() -> List[str]:
	ret: List[str] = [
		config.configure[config.name.mingw_w64_crt],
		f"--prefix={config.install_dir / config.target}",
		f"--build={config.build}",
		f"--host={config.name.x86_64_w64_mingw32}",
		f"--targe={config.name.x86_64_w64_mingw32}",
	]

	return ret


def do_make(cwd: Path, target: str = None) -> None:
	subprocess.run([
		"make",
		*([target] if target else []),
		"-j",
		f"{os.cpu_count()}",
	], cwd=cwd, check=True, env=config.env)


def build_mingw32_headers() -> None:
	cwd = config.build_cwd[config.name.mingw_w64_headers]
	subprocess.run(mingw32_headers_configure(), cwd=cwd, env=config.env)

	do_make(cwd)
	do_make(cwd, "install-strip")


def build_mingw32_crt() -> None:
	cwd = config.build_cwd[config.name.mingw_w64_crt]
	subprocess.run(mingw32_crt_configure(), cwd=cwd, env=config.env)

	do_make(cwd)
	do_make(cwd, "install-strip")


def create_symbolic_links() -> None:
	for name, url in config.canadian_required_pkgs.items():
		basename: str = os.path.basename(url)
		os.symlink(config.git_dir / basename, config.git_dir / config.name.binutils_gdb / name)


def build_binutils_gdb() -> None:
	if config.is_canadian_compiling:
		create_symbolic_links()

	cwd = config.build_cwd[config.name.binutils_gdb]
	subprocess.run(binutils_gdb_configure(), cwd=cwd, env=config.env)

	do_make(cwd)
	do_make(cwd, "install-strip")


def build_gcc_compiler_part(cwd: Path) -> None:
	do_make(cwd, "all-gcc")
	do_make(cwd, "install-strip-gcc")

	update_temporary_env_var_path()


def build_gcc() -> None:
	cwd = config.build_cwd[config.name.gcc]
	subprocess.run(gcc_configure(), cwd=cwd, env=config.env)

	if config.is_cross_compiling:
		build_gcc_compiler_part(cwd)
		build_mingw32_headers()
		build_mingw32_crt()

	do_make(cwd)
	do_make(cwd, "install-strip")


def safe_mkdir(path: Path) -> None:
	if path.exists():
		if not path.is_dir():
			raise RuntimeError(f"Path '{path}' exists but is not a directory.")
	else:
		path.mkdir(parents=True, exist_ok=True)


def update_paths(git: Path, build: Path, install: Path) -> Tuple[Path, Path, Path]:
	git = git or config.cwd
	build = build or config.cwd / "build" / config.host / config.target
	install = install or config.cwd / \
		config.host / config.target

	return git, build, install


def join_path(base: Path, components: List[str], leaf: str = ""):
	path: Path = base.joinpath(*components)
	return path / leaf if leaf else path


def update_configure_file() -> None:
	for name, path_parts in config.git_module_path.items():
		config.configure[name] = join_path(
			config.git_dir, path_parts, "configure")


def update_build_cwd() -> None:
	for name, path_parts in config.git_module_path.items():
		config.build_cwd[name] = join_path(config.build_dir, path_parts)


def create_neccessary_dirs() -> None:
	for dir in [config.git_dir, config.install_dir, *config.build_cwd.values()]:
		safe_mkdir(dir)


def update_config(args: argparse.Namespace) -> None:
	if args.cwd:
		config.cwd = args.cwd

	config.host = args.host
	config.target = args.target

	config.git_dir, config.build_dir, config.install_dir = update_paths(args.git_dir,
                                                                     args.build_dir,
                                                                     args.install_dir)

	config.with_lib32 = args.with_lib32
	config.clean_git = args.clean_git
	config.clean_build = args.clean_build
	config.update_env = args.update_env

	if args.binutils_gdb_git_repo_url:
		config.repos[config.name.binutils_gdb] = args.binutils_gdb_git_repo_url

	if args.gcc_git_repo_url:
		config.repos[config.name.gcc] = args.gcc_git_repo_url

	if args.mingw_w64_git_repo_url:
		config.repos[config.name.mingw_w64] = args.mingw_w64_git_repo_url

	update_configure_file()
	update_build_cwd()

	if config.host != config.target:
		config.is_cross_compiling = True

	if config.build != config.host:
		config.is_canadian_compiling = True


def pre() -> None:
	update_config(parse_args())

	create_neccessary_dirs()


def get_neccessary_repos() -> Dict[str, str]:
	if config.is_cross_compiling or config.is_canadian_compiling:
		return config.repos
	else:
		return {k: v for k, v in config.repos.items() if k != "mingw-w64"}


def extract_line(startswith: str) -> str:
	with open(config.bashrc_path, "r", encoding="utf-8") as f:
		lines = f.readlines()

	in_block: bool = False
	ret: str = ""

	for line in lines:
		stripped = line.strip()

		if not in_block:
			if stripped.startswith(startswith):
				in_block = True
				ret += stripped.rstrip("\\").rstrip()
				if not stripped.endswith("\\"):
					break
		else:
			ret += stripped.rstrip("\\").rstrip()
			if not stripped.endswith("\\"):
				break

	return ret


def extract_path() -> str:
	return extract_line("export PATH=")


def extract_ld_library_path() -> None:
	return extract_line("export LD_LIBRARY_PATH=")


def update_bashrc_path(path: Path) -> str:
	path_line: str = extract_path()

	if path in path_line:
		return
	else:
		path_line.find("")


def get_updated_path(new: str, orig: str) -> str:
	return orig if new in orig else re.sub(r'(=)("?)(.*?)', lambda m: f'{m.group(1)}{m.group(2)}{new}:{m.group(3)}', orig)


def update_temporary_env_var_path() -> None:
	bin: str = config.install_dir / "bin"
	path: str = config.env[config.name.env_path]
	if not bin in path:
		config.env[config.name.env_path] = bin + ":" + path


def update_temporary_env_var_ld_library_path() -> None:
	libs: List[str] = [
		*([config.install_dir / "lib32"] if config.is_withlib32 else []),
		config.install_dir / "lib64",
		config.install_dir / "lib"
	]

	path: str = config.env[config.name.env_ld_library_path]
	for lib in libs.reverse:
		if not lib in path:
			config.env[config.name.env_ld_library_path] = lib + ":" + path


def update_bashrc_ld_library_path() -> None:
	pass


def update_env() -> None:
	bin: Path = config.install_dir / "bin"
	libs: Path = [config.install_dir / "lib",
               config.install_dir / "lib64",
               *([config.install_dir / "lib32"] if config.is_withlib32 else [])]


def install_canadian_required_pkgs() -> None:
	for name, url in config.canadian_required_pkgs.items():
		subprocess.run(["wget",
	                 f"--tries={config.max_retries}",
	                 f"--waitretry={config.retry_delay}",
	                 url], check=True, env=config.env, cwd=config.git_dir)
		
		subprocess.run(["tar", "-zxvf", os.path.basename(url)])
		


def main() -> None:
	pre()

	install_required_pkgs()

	git_repos(get_neccessary_repos())

	build_binutils_gdb()
	build_gcc()


if __name__ == "__main__":
	main()
