import sys
import asyncio
import discord
import random
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


from dotenv import load_dotenv

load_dotenv()  

TOKEN = os.getenv("DISCORD_TOKEN")
CANAL_ID = os.getenv("CANAL_ID")



class DiscordBotThread(QThread):
    nova_mensagem = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.messages = True

        self.client = discord.Client(intents=intents)
        self.loop = None
        self.channel = None

        @self.client.event
        async def on_ready():
            try:
                self.channel = self.client.get_channel(CANAL_ID) or await self.client.fetch_channel(CANAL_ID)
                print(f"[OK] Logado como {self.client.user} e com canal pronto.")
            except Exception as e:
                print(f"[ERRO] Não foi possível obter o canal: {e}")

        @self.client.event
        async def on_message(message):
            import re

            if message.author.bot and message.author.id != self.client.user.id:
                return

            if message.content.startswith("!moeda"):
                resultado = random.choice(["cara", "coroa"])
                await message.channel.send(f"🪙 A moeda caiu em **{resultado}**!")
                return

            if message.content.startswith("!dado"):
                padrao = r"(\d+)d(\d+)"
                match = re.search(padrao, message.content)
                if match:
                    qtd = int(match.group(1))
                    faces = int(match.group(2))
                    if qtd <= 0 or faces <= 0:
                        await message.channel.send("❌ Quantidade e faces precisam ser maiores que zero.")
                    elif qtd > 20 or faces > 1000:
                        await message.channel.send("⚠️ Limite ultrapassado. Máximo: 20 dados de até 1000 faces.")
                    else:
                        resultados = [random.randint(1, faces) for _ in range(qtd)]
                        total = sum(resultados)
                        rolagem = ", ".join(str(r) for r in resultados)
                        await message.channel.send(f"🎲 Você rolou: {rolagem} \n🔢 Total: **{total}**")
                else:
                    await message.channel.send("❓ Sintaxe inválida. Use `!dado XdY`")
                return

            if getattr(message.channel, 'id', None) != CANAL_ID:
                return

            if message.attachments:
                for att in message.attachments:
                    self.nova_mensagem.emit(f"📎 Anexo: {att.filename}")
                return

            texto = f"{message.author.display_name}: {message.content}"
            self.nova_mensagem.emit(texto)

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.client.start(TOKEN))
        try:
            self.loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop=self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.close()

    def stop(self):
        if self.loop and self.loop.is_running():
            async def _close():
                try:
                    await self.client.close()
                except:
                    pass
                self.loop.stop()
            asyncio.run_coroutine_threadsafe(_close(), self.loop)

    def send_message(self, content: str):
        if not content.strip():
            return
        async def _send():
            await self.client.wait_until_ready()
            chan = self.channel or await self.client.fetch_channel(CANAL_ID)
            await chan.send(content)
        asyncio.run_coroutine_threadsafe(_send(), self.loop)

    def send_file(self, file_path: str, description: str = None):
        async def _send():
            await self.client.wait_until_ready()
            chan = self.channel or await self.client.fetch_channel(CANAL_ID)
            try:
                await chan.send(content=description or "", file=discord.File(file_path))
            except Exception as e:
                print(f"[ERRO] Falha ao enviar arquivo: {e}")
        asyncio.run_coroutine_threadsafe(_send(), self.loop)


class ChatOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord Overlay")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(340, 280)
        self.move(1000, 500)

        self.messages = []

        # Layout principal
        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 8)
        self.setLayout(root)

        # Layout de mensagens dentro de um container
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setSpacing(4)
        self.messages_layout.addStretch(1)

        # Container para mensagens
        messages_widget = QWidget()
        messages_widget.setLayout(self.messages_layout)

        # Área de rolagem
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(messages_widget)
        self.scroll_area.setStyleSheet(
            "background-color: rgba(0,0,0,0.45); border-radius: 6px;"
        )
        self.scroll_area.setFixedHeight(200)  # altura fixa
        root.addWidget(self.scroll_area, 1)

        # Linha de entrada de texto + botões
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Digite e pressione Enter…")
        self.input_edit.setStyleSheet(
            "QLineEdit { color: white; background-color: rgba(0,0,0,0.55);"
            " padding: 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.15); }"
        )
        self.send_btn = QPushButton("Enviar")
        self.send_btn.setStyleSheet(
            "QPushButton { color: white; background-color: rgba(30,144,255,0.8);"
            " padding: 6px 10px; border-radius: 4px; }"
        )
        self.searchbutton = QPushButton("+")
        self.searchbutton.setStyleSheet(
            "QPushButton { color: white; background-color: rgba(30,144,255,0.8);"
            " padding: 6px 10px; border-radius:4px; }"
        )

        input_row.addWidget(self.searchbutton, 0)
        input_row.addWidget(self.input_edit, 2)
        input_row.addWidget(self.send_btn, 0)

        input_container = QWidget()
        input_container.setLayout(input_row)
        root.addWidget(input_container, 0)

        self.send_btn.clicked.connect(self._on_send_clicked)
        self.input_edit.returnPressed.connect(self._on_send_clicked)
        self.searchbutton.clicked.connect(self._on_attach_clicked)

        self.bot_thread = DiscordBotThread()
        self.bot_thread.nova_mensagem.connect(self.add_message)
        self.bot_thread.start()

        self._drag_pos = None

    def add_message(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > 8:  # mantém só 8 no histórico
            self.messages.pop(0)
        self.update_messages()

        # Rola para o final
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def update_messages(self):
        for i in reversed(range(self.messages_layout.count() - 1)):  # deixa o stretch
            w = self.messages_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        for msg in self.messages:
            label = QLabel(msg)
            label.setWordWrap(True)
            label.setStyleSheet(
                "color: white; background-color: rgba(0,0,0,0.5); padding: 4px;"
                "border-radius: 4px;"
            )
            self.messages_layout.insertWidget(self.messages_layout.count() - 1, label)

    def _on_send_clicked(self):
        text = self.input_edit.text().strip()
        if text:
            self.bot_thread.send_message(text)
            self.input_edit.clear()

    def _on_attach_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione um arquivo",
            "",
            "Todos os arquivos (*.*)"
        )
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        self.add_message(f"📎 Anexo: {file_name}")
        self.bot_thread.send_file(file_path, description=f"📎 Anexo: {file_name}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def closeEvent(self, event):
        try:
            self.bot_thread.stop()
            self.bot_thread.wait(2000)
        except:
            pass
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatOverlay()
    window.show()
    sys.exit(app.exec_())
