import subprocess
import re
import uuid
import os
import json
import shutil
from pathlib import Path
from core.config import ensure_dir_exists, JAVA_RUNTIME_NAMES, REQUIRED_ASSETS, get_asset_path, JAVA_DIR

def verify_assets():
    """Проверяет наличие всех необходимых файлов ассетов"""
    missing_files = []
    
    for filename in REQUIRED_ASSETS:
        file_path = get_asset_path(filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    
    return missing_files

def get_java_major_version(java_path):
    """Определяет мажорную версию Java (УЛУЧШЕНО)"""
    try:
        if not os.path.exists(java_path):
            return 0
            
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        result = subprocess.run(
            [java_path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creation_flags
        )
        output = result.stderr or result.stdout
        
        # Специальная обработка для Java 8 (версия 1.8)
        if 'version "1.8' in output or '1.8.0' in output:
            return 8
        
        # Поиск различных паттернов версий
        patterns = [
            r'version "(\d+)',                     # version "17"
            r'openjdk version "(\d+)',              # openjdk version "17"
            r'(\d+)\.\d+\.\d+',                     # 17.0.8
            r'java version "1\.(\d+)',               # java version "1.8.0_361"
            r'openjdk version "1\.(\d+)',            # openjdk version "1.8.0_362"
            r'\(build (\d+)',                         # (build 17.0.8)
            r'version (\d+)',                         # version 17
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                version_num = int(match.group(1))
                # Для паттернов с 1.x
                if '1\.' in pattern and version_num == 8:
                    return 8
                # Java 17 может определяться как 21 из-за особенностей вывода
                if version_num == 21 and ('17' in output or 'openjdk 17' in output or '17.' in output):
                    print(f"Обнаружена Java 17, но определена как 21 - исправляем")
                    return 17
                return version_num
        
        return 0
    except subprocess.TimeoutExpired:
        print("Java version check timed out")
        return 0
    except Exception as e:
        print(f"Error getting Java version: {e}")
        return 0

def verify_java_installation(version):
    """
    Проверяет, правильно ли установлена Java указанной версии в именованной папке
    Возвращает (bool, path)
    """
    version_folders = {
        8: JAVA_DIR / "Java8",
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    if version not in version_folders:
        return False, None
    
    folder = version_folders[version]
    
    if not folder.exists():
        return False, None
    
    # Проверяем наличие java исполняемого файла
    if os.name == 'nt':
        java_exe = folder / "bin" / "java.exe"
    else:
        java_exe = folder / "bin" / "java"
    
    if not java_exe.exists():
        return False, None
    
    # Проверяем версию
    try:
        ver = get_java_major_version(str(java_exe))
        # Java 17 может определяться как 21
        if ver == version or (version == 17 and ver == 21) or (version == 16 and ver == 17):
            return True, str(java_exe)
        else:
            print(f"Java в папке {folder} имеет версию {ver}, ожидалась {version}")
            return False, None
    except Exception as e:
        print(f"Ошибка проверки Java в {folder}: {e}")
        return False, None

def find_java_by_version(target_version, search_in_system=False):
    """
    Ищет Java указанной версии в папке KuLauncher_java и опционально в системе
    Сначала проверяет именованные папки Java8/, Java17/, Java21/
    """
    # Именованные папки для разных версий Java
    version_folders = {
        8: JAVA_DIR / "Java8",
        16: JAVA_DIR / "Java17",  # Java 16 также ищем в Java17 папке
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    # Сначала проверяем именованные папки
    if target_version in version_folders:
        java_folder = version_folders[target_version]
        if java_folder.exists():
            if os.name == 'nt':
                java_exe = java_folder / "bin" / "java.exe"
            else:
                java_exe = java_folder / "bin" / "java"
            
            if java_exe.exists():
                try:
                    ver = get_java_major_version(str(java_exe))
                    # Java 17 может определяться как 21, Java 16 как 17
                    if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                        print(f"Найдена Java {target_version} в именованной папке: {java_exe}")
                        return str(java_exe)
                except Exception as e:
                    print(f"Ошибка проверки {java_exe}: {e}")
    
    # Если не нашли в именованных папках, ищем рекурсивно во всей папке JAVA_DIR
    if JAVA_DIR.exists():
        print(f"Поиск Java {target_version} во всей папке {JAVA_DIR}")
        
        for root, dirs, files in os.walk(JAVA_DIR):
            for file in files:
                if file.lower() in ["java.exe", "java"]:
                    java_path = Path(root) / file
                    try:
                        ver = get_java_major_version(str(java_path))
                        if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                            print(f"Найдена Java {target_version} в {java_path}")
                            return str(java_path)
                    except Exception as e:
                        print(f"Ошибка проверки {java_path}: {e}")
                        continue
    
    # Если не нашли в своей папке и разрешен поиск в системе
    if search_in_system:
        print(f"Поиск системной Java {target_version}...")
        return find_system_java_by_version(target_version)
    
    print(f"Java {target_version} не найдена")
    return None

def find_system_java_by_version(target_version):
    """Ищет Java указанной версии в системе"""
    if os.name == 'nt':
        # Для Windows ищем в Program Files
        search_paths = [
            "C:/Program Files/Java/",
            "C:/Program Files (x86)/Java/",
            str(Path.home() / ".jdks"),
            str(Path.home() / "AppData/Local/Programs/Java"),
            "C:/Program Files/Eclipse Adoptium/",
            "C:/Program Files/OpenJDK/",
            "C:/Program Files/Amazon Corretto/",
            "C:/Program Files/AdoptOpenJDK/",
        ]
        
        for base_path in search_paths:
            base = Path(base_path)
            if base.exists():
                # Ищем все папки с Java
                for java_dir in base.glob("jdk*"):
                    java_exe = java_dir / "bin" / "java.exe"
                    if java_exe.exists():
                        ver = get_java_major_version(str(java_exe))
                        if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                            return str(java_exe)
                
                for java_dir in base.glob("jre*"):
                    java_exe = java_dir / "bin" / "java.exe"
                    if java_exe.exists():
                        ver = get_java_major_version(str(java_exe))
                        if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                            return str(java_exe)
                
                # Для Eclipse Adoptium и других
                for java_dir in base.glob("*"):
                    if java_dir.is_dir():
                        java_exe = java_dir / "bin" / "java.exe"
                        if java_exe.exists():
                            ver = get_java_major_version(str(java_exe))
                            if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                                return str(java_exe)
    else:
        # Для Linux/Mac
        search_paths = [
            "/usr/lib/jvm/",
            "/usr/java/",
            "/opt/java/",
            str(Path.home() / ".jdks"),
            "/usr/local/",
        ]
        
        for base_path in search_paths:
            base = Path(base_path)
            if base.exists():
                for java_dir in base.glob("*"):
                    java_bin = java_dir / "bin" / "java"
                    if java_bin.exists():
                        ver = get_java_major_version(str(java_bin))
                        if ver == target_version or (target_version == 17 and ver == 21) or (target_version == 16 and ver == 17):
                            return str(java_bin)
    
    return None

def check_java_version(java_path, required_version):
    """Проверяет версию Java"""
    try:
        if not os.path.exists(java_path):
            return False, f"Java не найдена по пути: {java_path}"
        
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        result = subprocess.run(
            [java_path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creation_flags
        )
        output = result.stderr or result.stdout
        
        major_version = get_java_major_version(java_path)
        
        if major_version == 0:
            return False, "Не удалось определить версию Java"
        
        print(f"Detected Java version: {major_version}")
        
        # Для Java 17, которая может определяться как 21
        if required_version == 17 and major_version == 21:
            print(f"Java 17 определилась как 21, но считаем подходящей")
            return True, f"Java 17 (определена как {major_version}) подходит"
        
        # Для Java 16, которая может определяться как 17
        if required_version == 16 and major_version == 17:
            print(f"Java 16 определилась как 17, но считаем подходящей")
            return True, f"Java 16 (определена как {major_version}) подходит"
        
        if major_version < required_version:
            return False, f"Minecraft требует Java {required_version}+, а у вас Java {major_version}"
        
        return True, f"Java {major_version} подходит"
        
    except subprocess.TimeoutExpired:
        return False, "Проверка Java зависла (таймаут 10 сек)"
    except Exception as e:
        print(f"Java version check error: {e}")
        return False, f"Ошибка проверки Java: {str(e)}"

def check_all_java_versions_at_startup(search_in_system=False):
    """
    Проверяет наличие всех необходимых версий Java при запуске
    Возвращает список отсутствующих версий
    """
    required_versions = [8, 17, 21]
    missing_versions = []
    
    for version in required_versions:
        # Проверяем в папке KuLauncher_java (сначала именованные папки)
        java_path = find_java_by_version(version, search_in_system)
        if java_path:
            print(f"Java {version} найдена: {java_path}")
        else:
            print(f"Java {version} не найдена")
            missing_versions.append(version)
    
    return missing_versions

def organize_java_installations():
    """
    Организует установки Java в именованные папки Java8/, Java17/, Java21/
    Запускается при первом старте лаунчера или при обнаружении старых установок
    """
    if not JAVA_DIR.exists():
        JAVA_DIR.mkdir(parents=True, exist_ok=True)
        return
    
    # Создаем именованные папки
    version_folders = {
        8: JAVA_DIR / "Java8",
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    for folder in version_folders.values():
        folder.mkdir(exist_ok=True)
    
    # Ищем все установки Java в корневой папке и перемещаем в именованные папки
    for version, target_folder in version_folders.items():
        # Проверяем, есть ли уже Java в целевой папке
        if os.name == 'nt':
            target_java = target_folder / "bin" / "java.exe"
        else:
            target_java = target_folder / "bin" / "java"
        
        if target_java.exists():
            # Проверяем, что это правильная версия
            try:
                ver = get_java_major_version(str(target_java))
                # Java 17 может определяться как 21
                if ver == version or (version == 17 and ver == 21):
                    print(f"Java {version} уже правильно установлена в {target_folder}")
                    continue
            except:
                pass
        
        # Ищем Java этой версии в корне JAVA_DIR (не в подпапках)
        for item in JAVA_DIR.iterdir():
            if item.is_dir() and item.name not in ["Java8", "Java17", "Java21"]:
                # Проверяем, есть ли там Java
                if os.name == 'nt':
                    possible_java = item / "bin" / "java.exe"
                else:
                    possible_java = item / "bin" / "java"
                
                if possible_java.exists():
                    try:
                        ver = get_java_major_version(str(possible_java))
                        if ver == version or (version == 17 and ver == 21):
                            print(f"Найдена Java {version} в {item}, перемещаем в {target_folder}")
                            
                            # Перемещаем содержимое в целевую папку
                            for sub_item in item.iterdir():
                                dest = target_folder / sub_item.name
                                if sub_item.is_dir():
                                    if dest.exists():
                                        shutil.rmtree(dest)
                                    shutil.copytree(sub_item, dest)
                                else:
                                    shutil.copy2(sub_item, dest)
                            
                            # Удаляем старую папку
                            try:
                                shutil.rmtree(item)
                            except:
                                pass
                            
                            break
                    except Exception as e:
                        print(f"Ошибка при обработке {item}: {e}")
        
        # Если все еще нет Java, ищем во всех подпапках
        if not target_java.exists():
            java_path = find_java_by_version(version, search_in_system=False)
            if java_path and not str(java_path).startswith(str(target_folder)):
                java_path_obj = Path(java_path)
                source_dir = java_path_obj.parent.parent
                
                if source_dir.exists() and source_dir != target_folder:
                    try:
                        print(f"Копируем Java {version} из {source_dir} в {target_folder}")
                        
                        # Очищаем целевую папку
                        if target_folder.exists():
                            for item in target_folder.iterdir():
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                        
                        # Копируем содержимое
                        for item in source_dir.iterdir():
                            dest = target_folder / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest)
                            else:
                                shutil.copy2(item, dest)
                                
                    except Exception as e:
                        print(f"Ошибка копирования Java {version}: {e}")

def cleanup_old_java_installations():
    """
    Удаляет старые, неиспользуемые установки Java
    Оставляет только именованные папки Java8/, Java17/, Java21/
    """
    if not JAVA_DIR.exists():
        return
    
    # Папки, которые нужно сохранить
    keep_folders = ["Java8", "Java17", "Java21"]
    
    # Удаляем все остальные папки в корне JAVA_DIR
    for item in JAVA_DIR.iterdir():
        if item.is_dir() and item.name not in keep_folders:
            try:
                print(f"Удаляем старую папку Java: {item}")
                shutil.rmtree(item)
            except Exception as e:
                print(f"Ошибка удаления {item}: {e}")

def import_system_java_to_named_folder(version, source_java_path=None):
    """
    Импортирует системную Java указанной версии в именованную папку
    Возвращает True если успешно, False если нет
    """
    version_folders = {
        8: JAVA_DIR / "Java8",
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    if version not in version_folders:
        print(f"Неизвестная версия Java: {version}")
        return False
    
    target_folder = version_folders[version]
    
    # Если путь не указан, ищем в системе
    if source_java_path is None:
        source_java_path = find_system_java_by_version(version)
        if not source_java_path:
            # Для версии 16, пробуем найти Java 17
            if version == 16:
                source_java_path = find_system_java_by_version(17)
                if not source_java_path:
                    print(f"Системная Java {version} не найдена")
                    return False
            else:
                print(f"Системная Java {version} не найдена")
                return False
    
    source_java = Path(source_java_path)
    if not source_java.exists():
        print(f"Java по пути {source_java_path} не существует")
        return False
    
    # Проверяем версию
    try:
        ver = get_java_major_version(str(source_java))
        # Java 17 может определяться как 21, Java 16 как 17
        if ver != version and not (version == 17 and ver == 21) and not (version == 16 and ver == 17):
            print(f"Java по пути {source_java_path} имеет версию {ver}, а требуется {version}")
            return False
    except Exception as e:
        print(f"Ошибка проверки версии Java: {e}")
        return False
    
    # Определяем корневую папку Java (содержащую bin)
    source_dir = source_java.parent.parent
    if not source_dir.exists():
        source_dir = source_java.parent
    
    print(f"Импортируем Java {version} из {source_dir} в {target_folder}")
    
    # Создаем целевую папку
    target_folder.mkdir(parents=True, exist_ok=True)
    
    # Очищаем целевую папку перед копированием
    for item in target_folder.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception as e:
            print(f"Ошибка очистки {item}: {e}")
    
    # Копируем содержимое
    try:
        for item in source_dir.iterdir():
            dest = target_folder / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        
        # Проверяем результат
        if os.name == 'nt':
            final_java = target_folder / "bin" / "java.exe"
        else:
            final_java = target_folder / "bin" / "java"
        
        if final_java.exists():
            print(f"Java {version} успешно импортирована в {final_java}")
            return True
        else:
            print(f"Ошибка: Java не найдена после копирования")
            return False
            
    except Exception as e:
        print(f"Ошибка копирования Java: {e}")
        return False

def ensure_java_organized():
    """
    Проверяет и организует установки Java в именованные папки
    Вызывается при запуске лаунчера
    """
    print("Проверка организации Java...")
    
    # Сначала организуем существующие установки в JAVA_DIR
    organize_java_installations()
    
    # Проверяем, какие версии отсутствуют
    missing_versions = []
    version_folders = {
        8: JAVA_DIR / "Java8",
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    for version, folder in version_folders.items():
        installed, path = verify_java_installation(version)
        if installed:
            print(f"Java {version} организована правильно: {path}")
        else:
            print(f"Java {version} отсутствует в {folder}")
            missing_versions.append(version)
    
    # Для отсутствующих версий пытаемся найти в системе и импортировать
    if missing_versions:
        print(f"Отсутствуют версии Java: {missing_versions}")
        print("Пытаемся найти и импортировать из системы...")
        
        for version in missing_versions:
            success = import_system_java_to_named_folder(version)
            if success:
                print(f"Java {version} успешно импортирована из системы")
            else:
                print(f"Не удалось импортировать Java {version} из системы")
    
    # Очищаем старые папки
    cleanup_old_java_installations()
    
    # Финальная проверка
    final_missing = []
    for version, folder in version_folders.items():
        installed, _ = verify_java_installation(version)
        if not installed:
            final_missing.append(version)
    
    if final_missing:
        print(f"После всех проверок все еще отсутствуют: {final_missing}")
    else:
        print("Все необходимые версии Java организованы правильно!")
    
    return final_missing

def generate_offline_uuid(username):
    """Генерирует UUID для офлайн режима"""
    namespace_uuid = uuid.UUID('ba3f5aed-5b9c-11ea-bc55-0242ac130003')
    return str(uuid.uuid3(namespace_uuid, username))

def create_launcher_profiles(minecraft_dir):
    """Создает launcher_profiles.json если его нет"""
    minecraft_dir = Path(minecraft_dir)
    ensure_dir_exists(minecraft_dir)
    
    launcher_profiles_path = minecraft_dir / "launcher_profiles.json"
    
    if not launcher_profiles_path.exists():
        launcher_profiles = {
            "profiles": {},
            "settings": {
                "crashAssistance": True,
                "enableAdvanced": False,
                "enableAnalytics": True,
                "enableHistorical": False,
                "enableReleases": True,
                "enableSnapshots": False,
                "keepLauncherOpen": False,
                "profileSorting": "ByLastPlayed",
                "showGameLog": False,
                "showMenu": True,
                "soundOn": False
            },
            "version": 3,
            "selectedProfile": "",
            "clientToken": str(uuid.uuid4()),
            "authenticationDatabase": {}
        }
        
        try:
            with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(launcher_profiles, f, indent=2)
            print(f"Created launcher_profiles.json at {launcher_profiles_path}")
        except Exception as e:
            print(f"Error creating launcher_profiles.json: {e}")
    else:
        try:
            with open(launcher_profiles_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "version" not in data:
                data["version"] = 3
            
            if "profiles" not in data:
                data["profiles"] = {}
            
            if "clientToken" not in data:
                data["clientToken"] = str(uuid.uuid4())
            
            with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Ошибка чтения launcher_profiles.json: {e}")
            if launcher_profiles_path.exists():
                try:
                    os.remove(launcher_profiles_path)
                except:
                    pass
            create_launcher_profiles(minecraft_dir)

def get_java_path_from_named_folder(version):
    """
    Возвращает путь к Java указанной версии из именованной папки
    Версии: 8, 16, 17, 21
    """
    version_folders = {
        8: JAVA_DIR / "Java8",
        16: JAVA_DIR / "Java17",  # Java 16 ищем в папке Java17
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    if version not in version_folders:
        return None
    
    java_folder = version_folders[version]
    
    if not java_folder.exists():
        return None
    
    if os.name == 'nt':
        java_exe = java_folder / "bin" / "java.exe"
    else:
        java_exe = java_folder / "bin" / "java"
    
    if java_exe.exists():
        return str(java_exe)
    
    return None

def get_all_installed_java_versions():
    
    installed = {}
    version_folders = {
        8: JAVA_DIR / "Java8",
        17: JAVA_DIR / "Java17",
        21: JAVA_DIR / "Java21"
    }
    
    for version, folder in version_folders.items():
        if os.name == 'nt':
            java_exe = folder / "bin" / "java.exe"
        else:
            java_exe = folder / "bin" / "java"
        
        if java_exe.exists():
            try:
                ver = get_java_major_version(str(java_exe))
                # Java 17 может определяться как 21
                if ver == version or (version == 17 and ver == 21):
                    installed[version] = str(java_exe)
            except:
                pass
    
    return installed

def import_all_system_java():
    """
    Импортирует все найденные системные Java в именованные папки
    Возвращает словарь успешно импортированных версий
    """
    required_versions = [8, 17, 21]
    imported = {}
    
    for version in required_versions:
        # Проверяем, есть ли уже в именованной папке
        existing = get_java_path_from_named_folder(version)
        if existing:
            print(f"Java {version} уже есть в именованной папке")
            continue
        
        # Пытаемся найти в системе
        system_java = find_system_java_by_version(version)
        if system_java:
            print(f"Найдена системная Java {version}: {system_java}")
            success = import_system_java_to_named_folder(version, system_java)
            if success:
                imported[version] = system_java
                print(f"Java {version} успешно импортирована")
            else:
                print(f"Не удалось импортировать Java {version}")
        else:
            print(f"Системная Java {version} не найдена")
    
    return imported