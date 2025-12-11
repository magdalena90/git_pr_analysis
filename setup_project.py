"""Set up your project."""

import os
import pathlib

import rich.prompt


def guess_project_name():
    """Guess the project name from the current directory."""
    current_path = os.getcwd()
    return current_path.split("/")[-1]


def set_root_dir_env_var():
    """Set the SI_ROOT_DIR environment variable in the conda environment.

    Implements https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#macos-and-linux
    for persistent env vars.
    """
    activate_script = os.path.join(os.environ["CONDA_PREFIX"], "etc/conda/activate.d", "env_var.sh")
    deactivate_script = os.path.join(os.environ["CONDA_PREFIX"], "etc/conda/deactivate.d", "env_var.sh")
    root_dir = os.getcwd()

    pathlib.Path(activate_script).touch()
    with open(activate_script) as file:
        file_data = file.readlines()
    overwrite = False
    for lineno, line in enumerate(file_data):
        if "export SI_ROOT_DIR=" in line:
            overwrite = True
            break
        if overwrite:
            file_data[lineno] = f"export SI_ROOT_DIR={root_dir}"
        else:
            file_data.append(f"export SI_ROOT_DIR={root_dir}")
    with open(activate_script, "w") as file:
        file.writelines(file_data)

    pathlib.Path(deactivate_script).touch()
    with open(deactivate_script) as file:
        file_data = file.readlines()
    done = False
    for line in file_data:
        if "unset SI_ROOT_DIR" in line:
            done = True
    if not done:
        file_data.append("unset SI_ROOT_DIR")
    with open(deactivate_script, "w") as file:
        file.writelines(file_data)
    print("Set the SI_ROOT_DIR environment variable. Re-activate your conda environment when this script finishes.")
    os.environ["SI_ROOT_DIR"] = root_dir


def main():
    """Set up your project."""
    # Get & confirm project name
    project_name = guess_project_name()
    project_name = rich.prompt.Prompt.ask("Project name?", default=project_name)
    # Confirm we're in our conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    if not conda_env:
        raise OSError("You should only run this from within a conda environment. Exiting.")
    if conda_env != project_name:
        go_on = rich.prompt.Confirm.ask(
            f"Your project name is [bold red]{project_name}[/bold red], "
            f"and your conda environment is [bold red]{conda_env}[/bold red]. These are different, "
            f"are you sure you want to continue? "
            f"(This script will set project-specific environment variables in "
            f"your conda environment.)"
        )
        if not go_on:
            exit(0)
    set_root_dir_env_var()


if __name__ == "__main__":
    main()
