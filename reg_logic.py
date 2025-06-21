import os
import winreg

def parse_reg_file(file_path):
    """
    Analisa um arquivo .reg e extrai as chaves e valores.
    """
    registry_settings = {}
    current_path = ""
    try:
        with open(file_path, 'r', encoding='utf-16') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Não foi possível ler o arquivo: {e}")
    except Exception as e:
        raise IOError(f"Não foi possível ler o arquivo: {e}")

    lines = content.splitlines()
    if not lines or "Windows Registry Editor Version 5.00" not in lines[0]:
        raise ValueError("Formato de arquivo .reg inválido ou não suportado.")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('[') and line.endswith(']'):
            current_path = line[1:-1]
            registry_settings[current_path] = {}
        elif current_path and '=' in line:
            try:
                key, value = line.split('=', 1)
                key = key.strip().strip('"')
                registry_settings[current_path][key] = value.strip()
            except ValueError:
                pass 
    return registry_settings

def get_current_registry_value(full_key_path, log_callback):
    """
    Obtém o valor atual de uma chave específica no registro do Windows.
    """
    if os.name != 'nt':
        return "N/A (Não está no Windows)", "not_windows"

    try:
        parts = full_key_path.split('\\')
        root_key_str = parts[0]
        sub_key_path = '\\'.join(parts[1:-1])
        key_name = parts[-1]

        root_key_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }

        root_key = root_key_map.get(root_key_str)
        if not root_key:
            log_callback(f"Aviso: Chave raiz desconhecida: {root_key_str}")
            return f"Chave raiz desconhecida: {root_key_str}", "error"

        try:
            with winreg.OpenKey(root_key, sub_key_path, 0, winreg.KEY_READ) as key_handle:
                value, reg_type = winreg.QueryValueEx(key_handle, key_name)
                
                if reg_type == winreg.REG_SZ:
                    return f'"{value}"', "found"
                elif reg_type == winreg.REG_EXPAND_SZ:
                    hex_value = value.encode('utf-16-le').hex(',') + ',00,00'
                    return f'hex(2):{hex_value}', "found"
                elif reg_type == winreg.REG_DWORD:
                    return f'dword:{value:08x}', "found"
                elif reg_type == winreg.REG_QWORD:
                    return f'hex(b):{value:016x}', "found"
                elif reg_type == winreg.REG_BINARY:
                    hex_value = ''.join([f'{b:02x},' for b in value]).rstrip(',')
                    return f'hex:{hex_value}', "found"
                elif reg_type == winreg.REG_MULTI_SZ:
                    hex_data = ','.join(s.encode('utf-16-le').hex(',') for s in value) + ',00,00'
                    return f'hex(7):{hex_data}', "found"
                else:
                    return f'{value} (Tipo: {reg_type})', "found"
        except FileNotFoundError:
            return "❌ CHAVE/VALOR NÃO ENCONTRADO", "not_found"
        except Exception as e:
            log_callback(f"Erro ao consultar o valor {key_name} em {full_key_path}: {e}")
            return f"❌ ERRO: {e}", "error"
    except Exception as e:
        log_callback(f"Erro ao processar o caminho da chave {full_key_path}: {e}")
        return f"❌ ERRO: {e}", "error"

def compare_values(file_value, system_value, system_status):
    """
    Compara o valor do arquivo .reg com o valor do sistema.
    """
    if system_status == "not_found":
        return "missing", file_value, "❌ CHAVE/VALOR NÃO ENCONTRADO"
    elif system_status == "error":
        return "error", file_value, system_value
    elif system_status == "not_windows":
        return "not_windows", file_value, system_value
    else:
        if file_value.strip() == system_value.strip():
            return "match", f"✅ {file_value}", f"✅ {system_value}"
        else:
            return "different", f"📄 {file_value}", f"🖥️ {system_value}"

def get_current_registry_values_for_backup(parsed_settings, log_callback):
    """
    Obtém os valores atuais do registro para criar um arquivo de backup.
    """
    current_values = {}
    if os.name != 'nt':
        log_callback("Aviso: Este script não está rodando no Windows. O backup conterá apenas entradas de exclusão.")
        return {}

    for path, keys in parsed_settings.items():
        try:
            root_key_str, sub_key_path = path.split('\\', 1)
        except ValueError:
            log_callback(f"Aviso: Caminho de chave inválido ignorado: {path}")
            continue

        root_key_map = {
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        }

        root_key = root_key_map.get(root_key_str)
        if not root_key:
            log_callback(f"Aviso: Chave raiz desconhecida ignorada: {root_key_str}")
            continue

        try:
            with winreg.OpenKey(root_key, sub_key_path, 0, winreg.KEY_READ) as key_handle:
                for key_name in keys.keys():
                    full_key_path = f'{path}\\{key_name}'
                    try:
                        value, reg_type = winreg.QueryValueEx(key_handle, key_name)
                        
                        if reg_type == winreg.REG_SZ:
                            current_values[full_key_path] = f'"{key_name}"="{value}"\r\n'
                        elif reg_type == winreg.REG_EXPAND_SZ:
                            hex_value = value.encode('utf-16-le').hex(',') + ',00,00'
                            current_values[full_key_path] = f'"{key_name}"=hex(2):{hex_value}\r\n'
                        elif reg_type == winreg.REG_DWORD:
                            current_values[full_key_path] = f'"{key_name}"=dword:{value:08x}\r\n'
                        elif reg_type == winreg.REG_QWORD:
                            current_values[full_key_path] = f'"{key_name}"=hex(b):{value:016x}\r\n'
                        elif reg_type == winreg.REG_BINARY:
                            hex_value = ''.join([f'{b:02x},' for b in value]).rstrip(',')
                            current_values[full_key_path] = f'"{key_name}"=hex:{hex_value}\r\n'
                        elif reg_type == winreg.REG_MULTI_SZ:
                            hex_data = ','.join(s.encode('utf-16-le').hex(',') for s in value) + ',00,00'
                            current_values[full_key_path] = f'"{key_name}"=hex(7):{hex_data}\r\n'
                        
                    except FileNotFoundError:
                        pass
                    except Exception as e:
                        log_callback(f"Erro ao consultar o valor {key_name} em {path}: {e}")
        except FileNotFoundError:
            pass
        except Exception as e:
            log_callback(f"Erro ao abrir a chave {path}: {e}")

    return current_values

def generate_backup_reg(parsed_settings, current_values, output_file_path):
    """
    Gera o conteúdo do arquivo .reg de backup.
    """
    with open(output_file_path, 'w', encoding='utf-16') as f:
        f.write('Windows Registry Editor Version 5.00\r\n\r\n')

        for path, keys in parsed_settings.items():
            f.write(f'[{path}]\r\n')
            for key_name in keys.keys():
                full_key_path = f'{path}\\{key_name}'
                if full_key_path in current_values:
                    f.write(current_values[full_key_path])
                else:
                    # Se a chave não existe no sistema, o backup a removerá
                    f.write(f'"{key_name}"=-\r\n')
            f.write('\r\n')