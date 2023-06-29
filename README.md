# Project Vaccine Distribution

![Demo screenshot](./resource/Dashboard%20Demo.png)

*Link: https://vaccine-distribution-project-g71wyy8zv8m.streamlit.app/*

## How to run the web application (locally)

- Instruction of how to run the web application

1. Clone the repository to your local machine

```
git clone git@version.aalto.fi:phanct1/cs-a-1155-2023-vaccine-distribution-group-2.git
cd cs-a-1155-2023-vaccine-distribution-group-2
```

2. Create a new virtual environment and install the dependencies

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r ./code/requirements.txt
```

3. Run the application

```
streamlit run ./code/app.py
```

## File structure

```bash
.gitignore
README.md
code
   |-- Python_script.py
   |-- SQL_queries.sql
   |-- app.py
   |-- assignment3.py
   |-- requirements.txt
   |-- tablecreation.sql
   |-- utils.py
data
   |-- .gitkeep
   |-- healthstation.csv
   |-- vaccine-distribution-data.xlsx
database
   |-- .gitkeep
doc
   |-- Final Deliverable Package.pdf
   |-- Project Documentation.pdf
resource
   |-- Dashboard Demo.png
```