import socket
import subprocess
import os
import time
import threading
import sqlite3
import keyboard
import ctypes
import sys

DATABASE_PATH = 'server_data.db'

def run_as_admin():
    """Перезапускает скрипт с правами администратора."""
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def is_admin():
    """Проверяет, запущен ли скрипт с правами администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def press_tab_space():
    time.sleep(0.8)
    keyboard.press_and_release('tab')
    time.sleep(0.1)
    keyboard.press_and_release('space')
    print("Нажаты клавиши Tab и Пробел")

def handle_client_command(command, conn):
    command = command.decode()
    if command == "RESTART_NVDA":
        subprocess.run([r"C:\Program Files (x86)\NVDA\nvda_slave.exe", "launchNVDA", "-r"])
        conn.sendall(b"NVDA restarted\n")
    elif command.startswith("START_REMOTE_SESSION"):
        address, key = command.split()[1], command.split()[2]
        os.startfile(f"nvdaremote://{address}?key={key}&mode=slave")

        threading.Thread(target=press_tab_space).start()

        conn.sendall(b"Remote session started\n")
    elif command.startswith("SET_MASTER_PASSWORD"):
        new_password = command.split()[1]
        change_password(new_password)
        conn.sendall(b"Master password changed\n")
    else:
        conn.sendall(b"Unknown command\n")

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password TEXT NOT NULL
                    )''')
    conn.commit()
    conn.close()

def initialize_database(password):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (password) VALUES (?)", (password,))
    conn.commit()
    conn.close()

def check_password(entered_password):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE id = 1")
    result = c.fetchone()
    conn.close()
    if result is not None:
        return result[0] == entered_password
    return False

def change_password(new_password):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE id = 1", (new_password,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if not is_admin():
        print("Запрашиваю права администратора...")
        run_as_admin()
        sys.exit()  # Завершаем текущий процесс

    port = int(input("Введите порт: "))
    create_database()

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        password = input("База данных пуста. Введите пароль для инициализации: ")
        initialize_database(password)
        print("Пароль успешно сохранён.")
    conn.close()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)

    print(f"Сервер слушает порт {port}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Новое подключение от {addr}")

        conn.sendall("Введите пароль:".encode())
        received_password = conn.recv(1024).decode()

        if check_password(received_password):
            conn.sendall("Успешная аутентификация!".encode())
            print(f"Успешная аутентификация с {addr}")
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    handle_client_command(data, conn)
                except ConnectionResetError:
                    print(f"Соединение с {addr} разорвано.")
                    break
            conn.close()
        else:
            conn.sendall("Неверный пароль!".encode())
            conn.close()

