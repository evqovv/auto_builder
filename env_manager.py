import os
import config


class env_manager:
	def update_permanent(self) -> None:
		self.update_path()
		self.update_ld_library_path()

	def update_temporary(self) -> None:
		pass

	def update_bashrc_path(self, bin: str) -> None:
		self.update_bashrc("export PATH=", self.update(
			config.env[config.name.env_path], [bin]))

	def update_bashrc_ld_library_path(self, libs: list[str]) -> None:
		self.update_bashrc("export LD_LIBRARY_PATH=", self.update(
			config.env[config.name.env_ld_library_path], libs))

	def update_bashrc(self, startswith: str, new_content: str) -> None:
		with open(config.bashrc_path, "r", encoding="utf-8") as f:
			lines = f.readlines()

		s: int = -1
		e: int = -1
		is_in_block: bool = False
		for i in range(len(lines)):
			line = lines[i]
			stripped = line.strip()

			if not is_in_block:
				if stripped.startswith(startswith):
					s = i
					is_in_block = True
					if not stripped.endswith("\\"):
						e = i
						break
			else:
				if not stripped.endswith("\\"):
					e = i
					break

		if is_in_block and e == -1:
			e = len(lines) - 1

		if s == -1:
			lines.append(f'{startswith}"{new_content}"\n')
		else:
			lines[s: e + 1] = [f'{startswith}"{new_content}"\n']

		with open(config.bashrc_path, "w", encoding="utf-8") as f:
			f.writelines(lines)

	def update_path(self, bin: str) -> None:
		config.name[config.name.env_path] = self.update(
			config.env[config.name.env_path], [bin])

	def update_ld_library_path(self, libs: list[str]) -> None:
		config.name[config.name.env_ld_library_path] = self.update(
			config.env[config.name.env_ld_library_path], libs)

	def update(self, orig: str, paths: list[str]) -> str:
		for p in [p + ":" for p in paths]:
			if not p in orig:
				orig = f"{p}{orig}"

		return orig
