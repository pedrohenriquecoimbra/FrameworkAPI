# FrameworkAPI, a Modular Framework Runner

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="logo.png">
  <img alt="Shows an illustrated sun in light mode and a moon with stars in dark mode." src="https://user-images.githubusercontent.com/25423296/163456779-a8556205-d0a5-45e2-ac17-42d089e3c3f8.png" height="200px">
</picture>

A Python module for creating fully modular and extensible workflows by combining scripts in different languages, managing YAML-based configurations, and offering an API for seamless integration.

---

## Features

### 🚀 **Script Runner**
Easily run scripts written in Python, R, or Julia with dynamic argument support.
- **Automatic Language Detection**: Identify script type and invoke the appropriate runtime (e.g., `python`, `Rscript`, `julia`).
- **Flexible Argument Passing**: Pass command-line arguments directly to scripts for parameterized execution.
- **Robust Error Handling**: Logs and handles errors during script execution.

### 📜 **YAML Configuration Handler**
Effortlessly parse, validate, and manage YAML files with cross-references.
- **Dynamic Parsing**: Load YAML configurations into Python objects.
- **Cross-Reference Resolution**: Automatically resolve dependencies between keys within a single file or across multiple files.
- **Flexible Configuration Management**: Merge or extend YAML files to build modular workflows.

### 🛠 **High-Level API for Script Execution**
A simple API to link scripts and configurations for easy execution.
- **Script Discovery**: Fetch script paths and parameters from the YAML configuration.
- **Workflow Automation**: Execute scripts dynamically based on configuration settings.
- **Extensibility**: Add hooks for pre- and post-processing or extend functionality as needed.

---

## Installation

```bash
pip install FrameworkAPI
```

---

## Quickstart

### 1️⃣ Define Your Configuration (`config.yaml`)

```yaml
scripts:
  preprocess:
    path: "scripts/preprocess.py"
    args:
      input_file: "data/raw.csv"
      output_file: "data/processed.csv"
  analyze:
    path: "scripts/analyze.R"
    args:
      input_file: "data/processed.csv"
      report_file: "results/report.html"

workflow:
  - preprocess
  - analyze
```

---

### 2️⃣ Run Scripts Using the API

```python
from FrameworkAPI import FrameworkAPI

# Load configuration
framework = FrameworkAPI("config.yaml")

# Execute the entire workflow
framework.run_workflow()

# Or execute a single script by name
framework.run_script("preprocess")
```

---

### 3️⃣ Seamlessly Handle Multiple Languages

The module automatically detects the script type and runs the appropriate interpreter:
- `.py` → `python`
- `.R` → `Rscript`
- `.jl` → `julia`

---

## Directory Structure

```plaintext
project/
├── config.yaml          # Your YAML configuration file
├── scripts/             # Directory for scripts
│   ├── preprocess.py    # Python script
│   ├── analyze.R        # R script
├── results/             # Output directory
└── main.py              # Main Python script
```

---

## Advanced Features

- **Cross-References in YAML**: Use references to reuse values across the configuration.
  ```yaml
  data_dir: "data/"
  scripts:
    preprocess:
      input_file: "${data_dir}raw.csv"
      output_file: "${data_dir}processed.csv"
  ```
  
- **Custom Hooks**: Add pre- or post-processing logic in Python for additional control.

---

## Contributing

We welcome contributions! Please submit a pull request or open an issue for bug reports, feature requests, or questions.

---

## License

This project is licensed under the MIT License.

---

## Contact

Feel free to reach out for support or collaboration:
- **Email**: pedro-henrique.herig-coimbra@inrae.com
- **GitHub**: [GitHub Repository](https://github.com/pedrohenriquecoimbra/FrameworkAPI)

--- 

Happy scripting! ✨
