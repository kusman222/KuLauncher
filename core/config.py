import os
import sys
from pathlib import Path

# Версии Minecraft (по умолчанию)
DEFAULT_MC_VERSION = "1.21.4"
REQUIRED_JAVA_VERSION = 21

# Типы версий для фильтрации
VERSION_TYPES = ["release", "snapshot", "old_beta", "old_alpha"]

# Словарь соответствия версий Minecraft и рекомендуемых версий Java
JAVA_VERSION_REQUIREMENTS = {
    # Старые версии (до 1.17)
    "1.5.2": 8,
    "1.6.4": 8,
    "1.7.10": 8,
    "1.8.9": 8,
    "1.9.4": 8,
    "1.10.2": 8,
    "1.11.2": 8,
    "1.12.2": 8,
    "1.13.2": 8,
    "1.14.4": 8,
    "1.15.2": 8,
    "1.16.5": 8,
    # Версии 1.17-1.18 (требуют Java 16/17)
    "1.17": 17,
    "1.17.1": 17,
    "1.18": 17,
    "1.18.1": 17,
    "1.18.2": 17,
    # Версии 1.19
    "1.19": 17,
    "1.19.1": 17,
    "1.19.2": 17,
    "1.19.3": 17,
    "1.19.4": 17,
    # Версии 1.20+
    "1.20": 21,
    "1.20.1": 21,
    "1.20.2": 21,
    "1.20.3": 21,
    "1.20.4": 21,
    "1.20.5": 21,
    "1.20.6": 21,
    "1.21": 21,
    "1.21.1": 21,
    "1.21.2": 21,
    "1.21.3": 21,
    "1.21.4": 21,
}

# Соответствие версий Java и имен runtime папок
JAVA_RUNTIME_NAMES = {
    8: ["jre-legacy", "java-runtime-alpha"],  # Для Java 8
    11: ["java-runtime-beta"],                # Для Java 11
    16: ["java-runtime-gamma"],                # Для Java 16
    17: ["java-runtime-gamma", "java-runtime-delta", "java-runtime-delta.1", "java-runtime-delta.2"],  # Java 17 использует gamma или delta
    21: ["java-runtime-gamma", "java-runtime-delta", "java-runtime", "jre-delta", "jre-gamma"],  # Для Java 21
}

# Список необходимых ассетов
REQUIRED_ASSETS = [
    "textures/background.jpg",
    "textures/background.png",
    "textures/play.png",
    "textures/settings.png",
    "textures/mods.png",
    "textures/exit.png",
    "icon.ico",
    "mine.ttf",
    "textures/delete.png"
]

# Определяем путь к проекту
def get_project_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

PROJECT_DIR = get_project_dir()



# Путь к папке с Java (в домашней директории пользователя)
JAVA_DIR = Path.home() / "KuLauncher_java"

# Пути к ресурсам
def get_asset_path(filename):
    """Возвращает полный путь к файлу в папке assets"""
    possible_paths = [
        PROJECT_DIR / "assets" / filename,
        PROJECT_DIR / "_internal" / "assets" / filename,
        Path(__file__).parent.parent / "assets" / filename,
        Path.home() / ".pylauncher" / "assets" / filename,
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    user_assets = Path.home() / ".pylauncher" / "assets"
    user_assets.mkdir(parents=True, exist_ok=True)
    return str(user_assets / filename)

ASSETS_DIR = PROJECT_DIR / "assets"

# Путь к директории Minecraft по умолчанию
if os.name == 'nt':
    DEFAULT_MINECRAFT_DIR = Path(os.getenv('APPDATA')) / ".minecraft"
else:
    DEFAULT_MINECRAFT_DIR = Path.home() / ".minecraft"

def ensure_dir_exists(path):
    """Создает директорию, если она не существует"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_recommended_java_version(mc_version):
    """Возвращает рекомендуемую версию Java для указанной версии Minecraft"""
    # Сначала проверяем точное совпадение в словаре
    if mc_version in JAVA_VERSION_REQUIREMENTS:
        return JAVA_VERSION_REQUIREMENTS[mc_version]
    
    # Для версий 1.17.x
    if mc_version.startswith("1.17"):
        return 17
    # Для версий 1.18.x
    elif mc_version.startswith("1.18"):
        return 17
    # Для версий 1.19.x
    elif mc_version.startswith("1.19"):
        return 17
    # Для версий 1.20.x
    elif mc_version.startswith("1.20"):
        return 21
    # Для версий 1.21.x
    elif mc_version.startswith("1.21"):
        return 21
    # Для старых версий (до 1.17)
    else:
        # Парсим версию
        try:
            parts = mc_version.split('.')
            if len(parts) >= 2:
                major = int(parts[0])
                minor = int(parts[1])
                if major == 1 and minor < 17:
                    return 8
        except:
            pass
    
    # По умолчанию возвращаем 21
    return 21

def is_version_installed(version_id, minecraft_dir):
    """Проверяет, установлена ли указанная версия"""
    try:
        import minecraft_launcher_lib
        installed = minecraft_launcher_lib.utils.get_installed_versions(str(minecraft_dir))
        installed_ids = [v["id"] for v in installed]
        return version_id in installed_ids
    except:
        return False

def get_java_runtime_name(version):
    """Возвращает имя runtime папки для указанной версии Java"""
    runtime_names = JAVA_RUNTIME_NAMES.get(version, [])
    return runtime_names[0] if runtime_names else None

def get_all_java_runtime_names(version):
    """Возвращает все возможные имена runtime папок для указанной версии Java"""
    return JAVA_RUNTIME_NAMES.get(version, [])

def get_version_display_name(version_data):
    """Возвращает отображаемое имя версии"""
    return version_data.get("id", "Unknown")

def compare_versions(version1, version2):
    """Сравнивает две версии Minecraft (возвращает True если version1 >= version2)"""
    try:
        def parse_version(v):
            parts = v.split('.')
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return (major, minor, patch)
        
        v1_parts = parse_version(version1)
        v2_parts = parse_version(version2)
        return v1_parts >= v2_parts
    except:
        return False

def is_newer_version(version, than_version):
    """Проверяет, новее ли версия version, чем than_version"""
    return compare_versions(version, than_version) and version != than_version

def get_supported_minecraft_versions():
    """Возвращает список всех поддерживаемых версий Minecraft (из словарей)"""
    versions = set()
    versions.update(JAVA_VERSION_REQUIREMENTS.keys())
    return sorted(list(versions), reverse=True)

def get_java_requirements_for_version(mc_version):
    """Возвращает требования к Java для версии Minecraft"""
    return {
        "recommended": get_recommended_java_version(mc_version),
        "minimum": get_recommended_java_version(mc_version),  # Можно уточнить для разных версий
        "maximum": 21  # Максимальная поддерживаемая Java
    }

def format_file_size(size_bytes):
    """Форматирует размер файла в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_asset_filename(asset_name):
    """Возвращает имя файла ассета (с проверкой существования)"""
    return get_asset_path(asset_name)

def is_windows():
    """Проверяет, является ли ОС Windows"""
    return os.name == 'nt'

def is_linux():
    """Проверяет, является ли ОС Linux"""
    return os.name == 'posix' and sys.platform != 'darwin'

def is_mac():
    """Проверяет, является ли ОС macOS"""
    return sys.platform == 'darwin'

def get_os_name():
    """Возвращает название ОС"""
    if is_windows():
        return "Windows"
    elif is_mac():
        return "macOS"
    elif is_linux():
        return "Linux"
    else:
        return "Unknown"

def get_default_java_executable_name():
    """Возвращает имя исполняемого файла Java для текущей ОС"""
    return "java.exe" if is_windows() else "java"

def get_path_separator():
    """Возвращает разделитель путей для текущей ОС"""
    return ";" if is_windows() else ":"

def get_line_separator():
    """Возвращает разделитель строк для текущей ОС"""
    return "\r\n" if is_windows() else "\n"
