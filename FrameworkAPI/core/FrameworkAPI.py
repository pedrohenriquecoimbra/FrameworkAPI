import os
import sys
import ast
from string import Template
import yaml
import subprocess
import threading
import logging
import platform
import time
import copy
logger = logging.getLogger(__name__)


class FrameworkAPI:
    """
    FrameworkAPI: A class for managing and executing scripts based on YAML configurations.
    """

    def __init__(self, config_path=None, config=None, log_file=None):
        """
        Initialize the FrameworkAPI with a YAML configuration file or a preloaded configuration.
        Sets up logging if a log file is provided.

        Args:
            config_path (str, optional): Path to the YAML configuration file. Defaults to None.
            config (dict, optional): Preloaded configuration dictionary. Defaults to None.
            log_file (str, optional): Path to the log file for logging errors and debug messages. Defaults to None.

        Raises:
            ValueError: If neither 'config' nor 'config_path' is provided.
        """
        self.config_path = config_path
        
        # Determine configuration source
        if config:
            if isinstance(config, (list, tuple)):
                self = self._load_multiple_frameworks(config=config)
            else:
                self.raw_config = config
        elif config_path:
            if isinstance(config_path, (list, tuple)):
                self = self._load_multiple_frameworks(config_path=config_path)
            else:
                self.raw_config = self._load_config(raw=True)
        elif isinstance(config, dict):
            self.raw_config = config
        else:
            logger.error("Initialization failed: Both 'config' and 'config_path' are missing. "
                         "Provide at least one configuration source.")
            raise ValueError(
                "Configuration source is required: Pass either 'config' or 'config_path'.")
        
        # Resolve references in the configuration
        self.config = self._resolve_references(self.raw_config)

        # Set up logging if a log file is provided
        if log_file:
            self._setup_logging(log_file)

    def _load_multiple_frameworks(self, config_path=[], config=[]):
        try:
            # Load multiple configurations from different sources
            if not config_path and not config:
                raise ValueError("No configurations provided to load.")
            if isinstance(config_path, str):
                config_path = [config_path]
            if isinstance(config, dict):
                config = [config]
            for c in config_path:
                try:
                    merged = FrameworkAPI.merge(
                        self, FrameworkAPI(config_path=c))
                    self.__dict__.update(vars(merged))  # Copy attributes over
                except Exception as e:
                    logger.error(f"Error loading configuration from {c}: {e}")
            for c in config:
                try:
                    merged = FrameworkAPI.merge(self, FrameworkAPI(config=c))
                    self.__dict__.update(vars(merged))  # Copy attributes over
                except Exception as e:
                    logger.error(f"Error loading configuration: {e}")

            self.config = self._resolve_references(self.raw_config)
            logger.info("Multiple configurations loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading multiple configurations: {e}")
        return self

    def _setup_logging(self, log_file):
        """
        Set up the logging configuration.

        Args:
            log_file (str): Path to the log file.
        """
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True
        )
        logger.debug("Logging initialized.")

    def _load_config(self, raw=False):
        """
        Load and parse the YAML configuration file.

        Args:
            raw (bool): If True, return raw YAML configuration without resolving references.

        Returns:
            dict: Parsed configuration as a dictionary.
        """
        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            logger.debug(f"Configuration loaded from {self.config_path}.")
            if raw:
                return raw_config
            else:
                return self._resolve_references(raw_config)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise

    def _resolve_references(self, config):
        """
        Resolve cross-references in the YAML configuration using string templates.

        Args:
            config (dict): The raw YAML configuration.

        Returns:
            dict: Configuration with resolved references.
        """
        config = self._resolve_shortkeys(config)

        try:
            def resolve(obj, context=None):
                if context is None:
                    context = obj
                if isinstance(obj, dict):
                    return {k: resolve(v, context) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [resolve(item, context) for item in obj]
                elif isinstance(obj, str):
                    return Template(obj).safe_substitute(context)
                else:
                    return obj

            return resolve(config)
        except Exception as e:
            logger.error(f"Error resolving references in configuration: {e}")
            raise

    def _resolve_shortkeys(self, config, shortkeys=None):
        """
        Resolve coded references in the YAML configuration using eval of string.

        Args:
            config (dict): The raw YAML configuration.

        Returns:
            dict: Configuration with resolved coded references.
        """
        try:
            def resolve(obj, key=None):
                if isinstance(obj, str) and obj.strip().startswith('eval:'):
                    expr = obj.strip()[5:].strip()

                    try:
                        # Prepare a restricted environment for evaluation
                        allowed_globals = {
                            "__builtins__": {
                                "True": True,
                                "False": False,
                                "None": None,
                                "len": len,
                                "range": range,
                                "str": str,
                                "int": int,
                                "float": float,
                                "print": print,
                                "__import__": __import__,
                            }}
                        allowed_locals = {}

                        # Dynamically import required libraries
                        if 'import ' in expr:
                            for codeline in expr.split(';'):
                                exec(codeline.strip(),
                                     allowed_globals, allowed_locals)
                                value = allowed_locals.get(key, str(obj))
                        else:
                            # Safely evaluate the expression
                            value = ast.literal_eval(expr)

                        # Store the resolved value in the configuration
                        return value
                    except (ValueError, SyntaxError) as e:
                        print(f"Error evaluating expression: {e}")

                else:
                    return obj

            return {k: resolve(v, k) for k, v in config.items()}

        except Exception as e:
            logger.error(f"Error resolving references in configuration: {e}")
            raise

    @staticmethod
    def merge(one, other, overwrite=True):
        """
        Merge configurations from another FrameworkAPI instance.

        Args:
            other (FrameworkAPI): Another FrameworkAPI instance whose config will be merged.
            overwrite (bool): If True, overwrite existing keys with the values from `other`.

        Returns:
            None
        """
        try:
            def recursive_merge(dict1, dict2):
                for key, value in dict2.items():
                    if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                        recursive_merge(dict1[key], value)
                    elif overwrite or key not in dict1:
                        dict1[key] = value
                return dict1

            if isinstance(other, FrameworkAPI):
                out = copy.deepcopy(one)
                out.__dict__.update(recursive_merge(vars(out), vars(other)))
                logger.info("Configurations merged successfully.")
                return out
            else:
                raise TypeError("Argument must be an instance of FrameworkAPI")
        except Exception as e:
            logger.error(f"Error merging configurations: {e}")
            raise

    @staticmethod
    def _run_script(configuration=None, script_path=None, function_name=None, args=None,
                    arg_format=None, **kwargs):
        """
        Execute a script based on configuration or direct parameters.

        Args:
            configuration (dict, optional): Configuration of the script to be run. Defaults to None.
            script_path (str, optional): Direct path to the script file. Required if configuration is not provided.
            function_name (str, optional): Function to execute in the script. Defaults to None.
            args (dict, optional): Arguments to pass to the script or function. Defaults to None.
            arg_format (str, optional): Set the format that the arguments will be passed for direct terminal calls.

        Raises:
            ValueError: If required inputs are missing.
        """
        try:
            # Validate inputs
            if not script_path and configuration:
                script_path = script_path or configuration.get("path")
                function_name = function_name or configuration.get("function")
                args = args or configuration.get("args", {})

            if not script_path:
                raise ValueError(
                    "Script path is required if no configuration is provided.")

            args = args or {}

            # Determine the script command
            command = FrameworkAPI._build_command(
                script_path, function_name, args, arg_format)

            logger.info(f"Executing command: {command}")

            # Execute the command
            return FrameworkAPI._run_command(command=command, **kwargs)
        except Exception as e:
            logger.error(
                f"Error executing script '{script_path}': {e}")
            raise

    def run_script(self, script_name, **kwargs):
        """
        Execute a script defined in the configuration using optional additional parameters.

        Args:
            script_name (str): The name of the script to execute, as defined in the configuration.

        Raises:
            ValueError: If the configuration is missing or improperly defined.
            KeyError: If the specified script is not found in the configuration.
            Exception: Any other exceptions that occur during script execution.

        Returns:
            Any: The result of the script execution.
        """
        if not self.config:
            raise ValueError(
                "Configuration is missing. Please provide a valid configuration.")

        scripts = self.config.get("scripts", {})
        if script_name not in scripts:
            raise KeyError(
                f"Script '{script_name}' is not defined in the configuration.")

        try:
            script_info = scripts[script_name]
            runner = FrameworkAPI._run_script(script_info, **kwargs)
            return runner
        except Exception as e:
            logger.error(
                f"Failed to execute script '{script_name}': {e}", exc_info=True)
            raise

    def run_workflow(self, workflow=None, background=False, delay=0):
        """
        Execute all scripts defined in the workflow in sequence.
        """
        try:
            if not workflow: workflow = self.config.get('workflow', [])
            for script_name in workflow:
                self.run_script(script_name, background=background)
                time.sleep(delay)
            logger.info("Workflow executed successfully.")
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            raise

    @staticmethod
    def _get_interpreter(script_path):
        """
        Determine the interpreter for a given script based on its file extension.

        Args:
            script_path (str): Path to the script.

        Returns:
            str: The interpreter command (e.g., 'python', 'Rscript', 'julia').

        Raises:
            ValueError: If the file extension is unsupported.
        """
        ext = os.path.splitext(script_path)[-1].lower()
        system = platform.system()

        if ext == '.py':
            if system == 'Linux':
                return 'python3'
            elif system == 'Windows':
                return 'python'
            elif system == 'Darwin':  # macOS
                return 'python3'
            else:
                return 'python'
        elif ext == '.r':
            return 'Rscript'
        elif ext == '.jl':
            return 'julia'
        elif ext == '.exe':
            return 'executable'
        elif ext == '.lnk':
            return 'executable'
        elif ext == '.bat':
            return 'executable'
        elif ext == '.sh':
            return 'bash'
        else:
            raise ValueError(
                f"Unsupported script type for file '{script_path}'.")

    @staticmethod
    def _build_command(script_path: str, function_name: str = None, args: dict = {}, arg_format: str = None) -> list:
        """
        Build the command to execute the script.

        Args:
            script_path (str): Path to the script file.
            function_name (str, optional): Function to execute within the script.
            args (dict, optional): Arguments to pass to the function.
            arg_format (str, optional): Set the format that the arguments will be passed for direct terminal calls.

        Returns:
            list: The command to execute the script.

        Raises:
            ValueError: If the script extension is not supported.
        """
        script_path = os.path.abspath(script_path).replace('\\', '/')
        args = args or {}
        interpreter = FrameworkAPI._get_interpreter(script_path)
        ext = os.path.splitext(script_path)[-1].lower()
        system = platform.system()

        if function_name:
            if interpreter in ['executable', 'bash']:
                raise ValueError(
                    f"Cannot handle function name with an executable: {script_path}"
                )
            
            # Build command for a specific function
            module_path = os.path.relpath(
                os.path.abspath(script_path), os.getcwd()).rsplit('.', 1)[0].replace(
                '\\', '.').replace('/', '.')
            formatted_args = ', '.join([f'{k}="{v}"' if isinstance(
                v, str) else f"{k}={v}" for k, v in args.items()])

            if ext == '.py':
                return [interpreter, "-c",
                        f"import {module_path} as f; f.{function_name}({formatted_args})"]
            elif ext == '.r':
                return [
                    interpreter, "-e", f'source("{script_path}"); {function_name}({formatted_args})']
            elif ext == '.jl':
                return [
                    interpreter, "-e", f'include("{script_path}"); {function_name}({formatted_args})']
            else:
                raise ValueError(
                    f"Function execution is not supported for scripts with extension '{ext}'.")
        else:
            # Build command for simple script execution
            if system == 'Linux':
                script_path = script_path.replace('\\', '/')
            elif system == 'Windows':
                script_path = script_path.replace('/', '\\')
            else:
                script_path = script_path.replace('/', '\\')
            command = [interpreter, script_path] if interpreter != 'executable' else [
                script_path]

            if not arg_format:
                if interpreter in ['executable', 'bash']:
                    arg_format = '-k v'
                elif ext in ['.exe', '.lnk']:
                    arg_format = '-k=v'
                else:
                    arg_format = '--k v'

            for key, value in args.items():
                if isinstance(value, str):
                    if ' ' in value:
                        # the string comes with quotes, which have to be removed later
                        value = f'"{value}"'
                elif isinstance(value, (int, float)):
                    value = str(value)
                elif isinstance(value, list):
                    value = " ".join(map(str, value))
                else:
                    value = str(value)

                if arg_format == 'k=v':
                    command.extend([f'{key}={value}'])
                elif arg_format == '-k=v':
                    command.extend([f'-{key}={value}'])
                elif arg_format == '-k v':
                    command.extend([f"-{key}", value])
                elif arg_format == '--k v':
                    command.extend([f"--{key}", value])
                elif arg_format == 'v':
                    command.extend([value])
                else:
                    command.extend([f"--{key}", value])

            if interpreter in ['executable']:
                if system == 'Linux':
                    command = " ".join(
                        [f'"{c}"' if ' ' in c else c for c in command])
                    command = ['bash', '-c', f'echo | {command}']
                elif system == 'Windows':
                    command = ['echo.|'] + command
                else:
                    command = ['echo.|'] + command

            return command

    @staticmethod
    def _run_command(command: list, background: bool = False, ok_code: int = 0, error: str = 'alert', cwd: str = os.getcwd()) -> subprocess.Popen:
        """
        Run a shell command and handle its output and errors.

        Args:
            command (list | str): The command to execute, either as a list of arguments or a single string.
            background (bool): If True, run the command in the background. Defaults to False.

        Returns:
            subprocess.Popen: The process object representing the running command.

        Raises:
            subprocess.SubprocessError: If the command exits with a non-zero return code in foreground mode.
        """
        logger.info(f"Executing command: {command}")

        # Execute the command
        process = subprocess.run(
            command,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,  # Automatically decode byte streams to strings
            bufsize=1,  # Line-buffered output for real-time streaming
            cwd=cwd,    # Set the working directory
            shell=True,  # Execute the command through the shell
        )

        if background:
            logger.info("Running command in the background.")
            return process  # Do not wait for output or process completion in background mode

        # Capture and log output in real-time
        try:
            if process.returncode and process.returncode != ok_code:
                logger.error(
                    f"Script '{command}' exited with code {process.returncode}.")
                raise subprocess.SubprocessError(
                    f"Command '{command}' failed with exit code {process.returncode}."
                )

        except Exception as e:
            if error == 'ignore':
                pass
            if error == 'raise':
                process.terminate()
                logger.error(
                    f"An error occurred while running the command: {e}")
                raise
            else:
                logger.error(
                    f"An error occurred while running the command: {e}")

        return process
