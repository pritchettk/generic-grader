# Generic Grader

A collection of generic tests for grading programming assignments.

**This project is still in very early development.  Expect breaking changes.**

## Installation

``` bash
pip install generic-grader
```

## Usage

1. Name the reference solution `reference.py`, and place it in a `tests`
   subdirectory of the directory containing the student's code.

2. Add a configuration file for the assignment in the `tests` subdirectory (e.g.
   `tests/config.py`).  It might look something like this:

   ``` python
   from parameterized import param
   from generic_grader.style import comments # Import the tests you want to use
   from generic_grader.utils.options import Options

   # Create tests by calling each test type's build method.
   # They should all start with the word `test_` to be discovered by unittest.
   # Adding a number after `test_` can be used to control the run order.
   # The argument is a list of `param` objects, each with an `Options` object.
   # See the Options class for more information on the available options.
   test_01_TestCommentLength = comments.build(
      [
         param(
             Options(
                 sub_module="hello_user",
                 hint="Check the volume of comments in your code.",
                 entries=("Tim the Enchanter",),
             ),
         ),
         param(
             Options(
                 sub_module="hello_user",
                 hint="Check the volume of comments in your code.",
                 entries=("King Arthur",),
             ),
         ),
      ]
   )
   ```

3. Run the tests.

   ``` bash
   python -m unittest tests/config.py
   ```

## MATLAB Usage

MATLAB support runs through MATLAB Engine for Python.

### 1. Install MATLAB Engine for Python

From your MATLAB installation, run the engine installer in your grader
environment. The exact path depends on your MATLAB version, but typically:

``` bash
cd "<MATLABROOT>/extern/engines/python"
python -m pip install .
```

Then verify:

``` bash
python -c "import matlab.engine; print('ok')"
```

### 2. Configure Options for MATLAB

- Set `language="matlab"` for explicit MATLAB execution.
- `language="auto"` is also supported and detects `.m` files.
- If both `.py` and `.m` are discovered, language detection is ambiguous and
   the grader requires an explicit `language`.

Example:

``` python
from generic_grader.function import function_return_values_match_reference
from generic_grader.output import output_lines_match_reference
from generic_grader.utils.options import Options

test_01_output = output_lines_match_reference.build(
      Options(
            language="matlab",
            sub_module="submission",
            ref_module="reference",
            obj_name="main",
            weight=1,
      )
)

test_02_return = function_return_values_match_reference.build(
      Options(
            language="matlab",
            sub_module="submission",
            ref_module="reference",
            obj_name="main",
            execution_config={"nargout": 1},
            weight=1,
      )
)
```

### 3. MATLAB source naming rules

- `sub_module` / `ref_module` should point to `.m` file stems
   (for example, `submission` -> `submission.m`).
- If `obj_name` also maps to an existing `.m` file, that function name is used.
- Otherwise, the module stem is used as the MATLAB callable name.

### 4. Current MATLAB limitations

- Interactive input replay (`entries`) is not supported for MATLAB yet.
- Keyword arguments (`kwargs`) are not supported for MATLAB calls.
- Python-specific static/style checks are skipped for MATLAB with explicit
   skip messaging.
- For return-value checks, set `execution_config={"nargout": <n>}` when
   you need MATLAB outputs returned to Python for comparison.

### 5. Python-only checks (auto skipped on MATLAB)

The following check families are currently Python-specific and skip when
`language` resolves to MATLAB:

- `function.static_loop_depth`
- `function.random_function_calls`
- `style.comments`
- `style.docstring`
- `style.program_length`
- `class_.*`
- `file.file_closed`
- `image.plot_prop_matches_reference`

See MATLAB examples in [docs/example/matlab/config_matlab.py](docs/example/matlab/config_matlab.py).

### Excel check notes

- Excel checks use the workbook's first worksheet by default.
- Set `sheet="..."` (or `kwargs={"sheet": "..."}`) to target a specific sheet.
- `data_series_match_reference` is the canonical data-series check. Use
   `range_matches_reference=True` for same-cell comparison, or
   `range_matches_reference=False` to search the selected worksheet.
- `formulas_exist` and `formulas_match_reference` also support
   `range_matches_reference=False` to search the selected worksheet for a
   same-sized matching region.


## Contributing

1. Clone the repo onto your machine.

   - HTTPS

     ``` bash
     git clone https://github.com/Purdue-EBEC/generic-grader.git
     ```

   - SSH

     ``` bash
     git clone git@github.com:Purdue-EBEC/generic-grader.git
     ```

2. Set up a new virtual environment in the cloned repo.

   ``` bash
   cd generic-grader
   python3.12 -m venv .env3.12
   ```

3. Activate the virtual environment.  If you are using VS Code, there may be a
   pop-up to do this automatically when working from this directory.

   - Linux/macOS

      ``` bash
      source .env3.12/bin/activate
      ```

   - Windows

     ``` bash
     .env3.12\Scripts\activate
     ```

4. Install tesseract-ocr

   - on Linux

     ``` bash
     sudo apt install tesseract-ocr
     ```

   - on macOS

     ``` bash
     brew install tesseract
     ```

   - on Windows, download the latest installers from https://github.com/UB-Mannheim/tesseract/wiki

5. Install ghostscript

   - on Linux

     ``` bash
     sudo apt install ghostscript
     ```

   - on macOS

     ``` bash
     brew install ghostscript
     ```

   - on Windows, download the latest installers from https://ghostscript.com/releases/gsdnld.html

6. Install the package.  Note that this installs the package as editable, so
   edits will be automatically reflected in the installed package.

   ``` bash
   pip install -e .[dev]
   ```
   or

   ``` bash
   uv sync --extra dev
   ```

7. Install the pre-commit hooks.

   ``` bash
   pre-commit install
   ```

8. Run the tests.

   ``` bash
   pytest
   ```

9. Make changes ...

10. Deactivate the virtual environment.

   ``` bash
   deactivate
   ```
