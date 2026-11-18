import os

try:
    import winreg
except ImportError:
    winreg = None


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_FILE = os.path.join(_BASE_DIR, ".env")


def _read_dotenv():
    values = {}
    if not os.path.exists(_ENV_FILE):
        return values

    with open(_ENV_FILE, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
    return values


_DOTENV_VALUES = _read_dotenv()


def _read_windows_env_var(var_name):
    if winreg is None:
        return ""

    key_locations = [
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    ]
    for hive, subkey in key_locations:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                value, _ = winreg.QueryValueEx(key, var_name)
                if value:
                    return str(value)
        except OSError:
            continue
    return ""


def get_config(var_name, default=""):
    value = os.getenv(var_name)
    if value is not None and str(value).strip() != "":
        return str(value).strip()

    if var_name in _DOTENV_VALUES and _DOTENV_VALUES[var_name].strip() != "":
        return _DOTENV_VALUES[var_name].strip()

    fallback = _read_windows_env_var(var_name)
    if fallback:
        return fallback.strip()

    return default
