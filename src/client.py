import wx
import socket

class RemoteHelperClient(wx.Frame):
    def __init__(self, parent, title):
        super(RemoteHelperClient, self).__init__(parent, title=title, size=(400, 300))

        self.server_address = None
        self.server_port = None
        self.connected = False

        self.InitUI()
        self.Centre()
        self.Show()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.connect_button = wx.Button(panel, label='Подключиться')
        self.remote_session_button = wx.Button(panel, label='Запустить сессию NVDARemote')
        self.restart_nvda_button = wx.Button(panel, label='Перезапустить NVDA')
        self.change_master_password_button = wx.Button(panel, label='Сменить мастер пароль')

        vbox.Add(self.connect_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.remote_session_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.restart_nvda_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.change_master_password_button, flag=wx.EXPAND | wx.ALL, border=10)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)
        self.Bind(wx.EVT_BUTTON, self.OnRemoteSessionButton, self.remote_session_button)
        self.Bind(wx.EVT_BUTTON, self.OnRestartNVDAButton, self.restart_nvda_button)
        self.Bind(wx.EVT_BUTTON, self.OnChangeMasterPasswordButton, self.change_master_password_button)

    def OnConnect(self, event):
        if not self.connected: 
            dlg = ConnectionDialog(self, title="Подключение к серверу")
            if dlg.ShowModal() == wx.ID_OK:
                self.server_address = dlg.address_text.GetValue()
                self.server_port = int(dlg.port_text.GetValue())

                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.server_address, self.server_port))
                    response = self.sock.recv(1024).decode()

                    if response == "Введите пароль:":
                        dlg = wx.PasswordEntryDialog(self, 'Введите пароль:', 'Подключение к серверу')
                        if dlg.ShowModal() == wx.ID_OK:
                            password = dlg.GetValue()
                            self.sock.sendall(password.encode())
                            response = self.sock.recv(1024).decode()
                            if response == "Успешная аутентификация!":
                                wx.MessageBox('Успешная аутентификация!', 'Успех', wx.OK | wx.ICON_INFORMATION)
                                self.connected = True
                                self.connect_button.Disable() 
                            else:
                                wx.MessageBox('Неверный пароль!', 'Ошибка', wx.OK | wx.ICON_ERROR)
                                self.sock.close()
                        dlg.Destroy()
                    else:
                        wx.MessageBox(f"Ошибка: {response}", 'Ошибка', wx.OK | wx.ICON_ERROR)
                        self.sock.close()
                except Exception as e:
                    wx.MessageBox(f"Ошибка соединения: {e}", 'Ошибка', wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox('Вы уже подключены к серверу.', 'Информация', wx.OK | wx.ICON_INFORMATION)


    def OnRemoteSessionButton(self, event):
        remote_session_dialog = RemoteSessionDialog(self, title="Запустить сессию NVDARemote")
        remote_session_dialog.ShowModal()
        remote_session_dialog.Destroy()

    def OnRestartNVDAButton(self, event):
        self.SendCommand("RESTART_NVDA")

    def OnChangeMasterPasswordButton(self, event):
        change_password_dialog = ChangePasswordDialog(self, title="Сменить мастер пароль")
        change_password_dialog.ShowModal()
        change_password_dialog.Destroy()

    def SendCommand(self, command):
        if not self.connected:
            wx.MessageBox("Сначала подключитесь к серверу.", 'Ошибка', wx.OK | wx.ICON_ERROR)
            return

        try:
            self.sock.sendall(command.encode())
            response = self.sock.recv(1024)
            wx.MessageBox(response.decode(), 'Response', wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Ошибка отправки команды: {e}", 'Ошибка', wx.OK | wx.ICON_ERROR)
            self.connected = False
            self.connect_button.Enable() 

class ConnectionDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(ConnectionDialog, self).__init__(*args, **kw)

        self.InitUI()
        self.SetSize((300, 200))

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.address_label = wx.StaticText(self, label="Введите адрес:")
        self.address_text = wx.TextCtrl(self)
        self.port_label = wx.StaticText(self, label="Введите порт:")
        self.port_text = wx.TextCtrl(self)
        self.ok_button = wx.Button(self, label='OK')
        self.cancel_button = wx.Button(self, label='Отмена')

        vbox.Add(self.address_label, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.address_text, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.port_label, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.port_text, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.cancel_button, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnOK, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)

    def OnOK(self, event):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

class RemoteSessionDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(RemoteSessionDialog, self).__init__(*args, **kw)

        self.InitUI()
        self.SetSize((300, 200))

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.address_label = wx.StaticText(self, label="Введите адрес и порт:")
        self.address_text = wx.TextCtrl(self)
        self.key_label = wx.StaticText(self, label="Введите ключ:")
        self.key_text = wx.TextCtrl(self)
        self.ok_button = wx.Button(self, label='OK')
        self.cancel_button = wx.Button(self, label='Отмена')

        vbox.Add(self.address_label, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.address_text, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.key_label, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.key_text, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.cancel_button, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnOK, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)

    def OnOK(self, event):
        address = self.address_text.GetValue()
        key = self.key_text.GetValue()
        command = f"START_REMOTE_SESSION {address} {key}"
        self.GetParent().SendCommand(command)
        self.Close()

    def OnCancel(self, event):
        self.Close()

class ChangePasswordDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(ChangePasswordDialog, self).__init__(*args, **kw)

        self.InitUI()
        self.SetSize((300, 200))

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.password_label = wx.StaticText(self, label="Введите новый мастер пароль:")
        self.password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.ok_button = wx.Button(self, label='OK')
        self.cancel_button = wx.Button(self, label='Отмена')

        vbox.Add(self.password_label, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.password_text, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.ok_button, flag=wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.cancel_button, flag=wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnOK, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.cancel_button)

    def OnOK(self, event):
        password = self.password_text.GetValue()
        command = f"SET_MASTER_PASSWORD {password}"
        self.GetParent().SendCommand(command)
        self.Close()

    def OnCancel(self, event):
        self.Close()

if __name__ == '__main__':
    app = wx.App()
    RemoteHelperClient(None, title='NvdaRemote assistent')
    app.MainLoop()
