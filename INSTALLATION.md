# OR Course – Installation Guide

This guide explains how to set up the computational environment for the course.

------------------------------------------------------------

## 1. Clone the Repository

Open a terminal and run:

    git clone <REPOSITORY_URL>
    cd or-course

Replace <REPOSITORY_URL> with the GitHub repository link provided in class.

------------------------------------------------------------

## 2. Check Python Version

We recommend Python 3.11 (3.10–3.12 also acceptable).

Check your version:

    python3 --version

If Python is not installed, install it from:

https://www.python.org

------------------------------------------------------------

## 3. Create a Virtual Environment

From inside the repository folder:

    python3 -m venv .venv

Activate it:

### macOS / Linux

    source .venv/bin/activate

### Windows (PowerShell)

    .venv\Scripts\Activate.ps1

After activation, your prompt should show:

    (.venv)

------------------------------------------------------------

## 4. Install Required Packages

With the virtual environment activated:

    pip install -r requirements.txt
    pip install -e .

The first command installs external libraries.
The second installs the course modeling package.

------------------------------------------------------------

## 5. Install Linear Programming Solver (GLPK)

We use GLPK as the solver.

### macOS (Homebrew)

If you do not have Homebrew:

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

Then install GLPK:

    brew install glpk

### Ubuntu / Debian

    sudo apt update
    sudo apt install glpk-utils

### Windows

1. Download GLPK binaries (e.g., from winglpk).
2. Add the folder containing `glpsol.exe` to your PATH environment variable.
3. Restart terminal.

Verify installation:

    glpsol --version

You should see the solver version printed.

------------------------------------------------------------

## 6. Using VS Code

1. Open VS Code.
2. Select File → Open Folder and open the `or-course` directory.
3. Open Command Palette (Ctrl+Shift+P or Cmd+Shift+P).
4. Choose "Python: Select Interpreter".
5. Select the interpreter inside `.venv`.

To work with notebooks:

    jupyter lab

------------------------------------------------------------

## 7. Running Python

Start interactive Python:

    python

Run a script:

    python filename.py

------------------------------------------------------------

# Common Problems & Fixes

------------------------------------------------------------

### Problem 1: "ModuleNotFoundError: orlab"

Cause:
The editable install was not completed.

Fix:

    pip install -e .

Make sure you run this inside the activated `.venv`.

------------------------------------------------------------

### Problem 2: "No executable found for solver 'glpk'"

Cause:
GLPK is not installed or not in PATH.

Fix:
1. Run:

       glpsol --version

2. If command not found, install GLPK (see section above).
3. Restart terminal after installation.

------------------------------------------------------------

### Problem 3: Wrong Python Interpreter in VS Code

Cause:
VS Code is using system Python instead of `.venv`.

Fix:
Use "Python: Select Interpreter" and choose the one inside `.venv`.

You can verify in terminal:

    which python        (macOS/Linux)
    where python        (Windows)

It should point to:

    or-course/.venv/

------------------------------------------------------------

### Problem 4: Permission Errors (macOS/Linux)

If pip fails due to permissions:

    pip install --upgrade pip

Make sure the virtual environment is activated before installing.

------------------------------------------------------------

### Problem 5: Solver Works in Terminal but Not in VS Code

Cause:
PATH variable differs.

Fix:
Restart VS Code after installing GLPK.
Open a new integrated terminal.
Check:

    glpsol --version

------------------------------------------------------------

## Important Rules

• Always activate `.venv` before working.
• Never commit `.venv` to Git.
• If something fails, first check:
  - Is `.venv` activated?
  - Is GLPK installed?
  - Is the correct interpreter selected?

------------------------------------------------------------

The environment is now ready for modeling linear and integer programming problems.
