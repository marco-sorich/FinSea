# Seasonality Chart Analysis

A Jupyter Notebook for analysing the seasonality of a single financial product.

This notebook analyzes the seasonality aspect of stocks, ETFs, crypto token, indices, etc. The anslysis method used is the LOESS regression kernel.
The symbol to analyze can be changed freely.

## Preparation

Following actions have to be executed initially for preparation or each time on update:

### MacOS
* __Install python__

    Download from https://www.python.org/downloads/

* __Download and unzip latest version notebook__

    Download the project as zip file and unzip to a desired location.

* __Open command line terminal__

    Open _terminal_ and change to the directory with unzipped notebook.

* __Setup the system__
    ```zsh
    pip install notebook
    pip install venv
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

### Windows
* __Install python__

    Download from https://www.python.org/downloads/

* __Download and unzip latest version notebook__

    Download the project as zip file and unzip to a desired location.

* __Open command line terminal__

    Open Windows PowerShell and change to the directory with unzipped notebook.

* __Setup the system__
    ```PowerShell
    pip install notebook
    pip install venv
    python -m venv .venv
    .venv\Scripts\activate.ps1
    pip install -r requirements.txt
    ```

### Linux
* __Install python__

    Download from https://www.python.org/downloads/

* __Download and unzip latest version notebook__

    Download the project as zip file and unzip to a desired location.

* __Setup the system__
    ```bash
    pip install notebook
    pip install venv
    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt
    ```

## Open the notebook

Following actions have to be executed always to open the notebook:

### MacOS
* __Open command line terminal__

    Open _terminal_ and change to the directory with unzipped notebook.

* __Open the notebook__
    ```zsh
    source .venv/bin/activate
    jupyter notebook seasonality.ipynb
    ```

### Windows
* __Open command line terminal__

    Open Windows PowerShell and change to the directory with unzipped notebook.

* __Open the notebook__
    ```PowerShell
    .venv\Scripts\activate.bat
    jupyter notebook seasonality.ipynb
    ```


### Linux
* __Open the notebook__
    ```bash
    source .venv/Scripts/activate
    jupyter notebook seasonality.ipynb
    ```


## Using the notebook
…


## Legal
__Seasonality Chart Analysis__ is distributed under the GNU GENERAL PUBLIC LICENSE version 3. See the LICENSE.txt file in the release for details.