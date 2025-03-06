import sys
import os
import json
import keyboard
import pyperclip
import requests
import time
import logging
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction, 
                            QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QLineEdit, 
                            QMainWindow, QTextEdit, QSplitter, QWidget,
                            QListWidget, QListWidgetItem, QFrame, QGridLayout,
                            QActionGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor
import win32gui
import win32con
import win32api
import win32clipboard
from playsound import playsound
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translator_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AITranslator")

class TranslationThread(QThread):
    translation_complete = pyqtSignal(str, str)
    
    def __init__(self, text, source_lang, target_lang, api_config):
        super().__init__()
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_config = api_config
        
    def run(self):
        try:
            # Check API key first
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("API key not found in environment variables. Please check your .env file.")
            
            logger.info(f"Starting translation from {self.source_lang} to {self.target_lang}")
            translated_text = self.translate_text()
            logger.info("Translation completed successfully")
            self.translation_complete.emit(self.text, translated_text)
        except Exception as e:
            logger.error(f"Translation error: {str(e)}", exc_info=True)
            self.translation_complete.emit(self.text, f"Translation error: {str(e)}")
    
    def translate_text(self):
        # Get API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        model = self.api_config["model"]
        
        if not api_key:
            raise ValueError("API key not found in environment variables. Please check your .env file.")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare the prompt for translation with casual, friendly tone
        if self.source_lang == "auto" and self.target_lang == "pt":
            prompt = f"<<INPUT>>{self.text}<<OUTPUT>>"
            system_prompt = "You are a casual translator who speaks like a friend. When you see text between <<INPUT>> and <<OUTPUT>>, translate it to Brazilian Portuguese using informal, everyday language. Use common expressions and slang when appropriate. Just give the translation, nothing else."
        elif self.source_lang == "pt" and self.target_lang == "en":
            prompt = f"<<INPUT>>{self.text}<<OUTPUT>>"
            system_prompt = "You are a casual translator who speaks like a friend. When you see text between <<INPUT>> and <<OUTPUT>>, translate the Portuguese text to casual, everyday English. Use common expressions and slang when appropriate. Just give the translation, nothing else."
        elif self.source_lang == "en" and self.target_lang == "pt":
            prompt = f"<<INPUT>>{self.text}<<OUTPUT>>"
            system_prompt = "You are a casual translator who speaks like a friend. When you see text between <<INPUT>> and <<OUTPUT>>, translate the English text to informal Brazilian Portuguese. Common expressions, and everyday language. Just give the translation, nothing else."
        elif self.source_lang == "ru" and self.target_lang == "pt":
            prompt = f"<<INPUT>>{self.text}<<OUTPUT>>"
            system_prompt = "You are a casual translator who speaks like a friend. When you see text between <<INPUT>> and <<OUTPUT>>, translate the Russian text to informal Brazilian Portuguese. Common expressions, and everyday language. Just give the translation, nothing else."
        elif self.source_lang == "auto" and self.target_lang == "en":
            prompt = f"<<INPUT>>{self.text}<<OUTPUT>>"
            system_prompt = "You are a casual translator who speaks like a friend. When you see text between <<INPUT>> and <<OUTPUT>>, translate the text to casual, everyday English. Use common expressions and slang when appropriate. Just give the translation, nothing else."
        else:
            raise ValueError(f"Unsupported language pair: {self.source_lang} to {self.target_lang}")
        
        logger.debug(f"Translation prompt: {prompt}")
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "<<INPUT>>Hello, how are you doing?<<OUTPUT>>"},
                {"role": "assistant", "content": "Oi, como você tá?"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # Increased temperature for more natural, casual language
            "max_tokens": 1024
        }
        
        logger.debug("Sending request to Groq API")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result["choices"][0]["message"]["content"].strip()
            return translated_text
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("AI Translator Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # API Key status
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Key Status:"))
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            status_label = QLabel("✅ API Key found in environment")
            status_label.setStyleSheet("color: #43B581;")  # Green color
        else:
            status_label = QLabel("❌ API Key not found in environment")
            status_label.setStyleSheet("color: #F04747;")  # Red color
        api_layout.addWidget(status_label)
        layout.addLayout(api_layout)
        
        # Add info label about .env
        env_info = QLabel("API key should be set in the .env file as GROQ_API_KEY")
        env_info.setStyleSheet("color: #B5BAC1; font-size: 11px;")
        layout.addWidget(env_info)
        
        # Language pair selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Default Language:"))
        self.lang_combo = QComboBox()
        
        for pair in self.config["ui"]["language_pairs"]:
            self.lang_combo.addItem(pair["name"])
        
        self.lang_combo.setCurrentIndex(self.config["ui"]["default_language_pair"])
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # Shortcuts
        shortcuts_layout = QGridLayout()
        shortcuts_layout.addWidget(QLabel("Translate and Send:"), 0, 0)
        self.translate_send_shortcut = QLineEdit(self.config["shortcuts"]["translate_and_send"])
        shortcuts_layout.addWidget(self.translate_send_shortcut, 0, 1)
        
        shortcuts_layout.addWidget(QLabel("Translate Selected:"), 1, 0)
        self.translate_selected_shortcut = QLineEdit(self.config["shortcuts"]["translate_selected"])
        shortcuts_layout.addWidget(self.translate_selected_shortcut, 1, 1)
        
        layout.addLayout(shortcuts_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        # Don't save API key, it's managed through environment variables
        self.config["ui"]["default_language_pair"] = self.lang_combo.currentIndex()
        self.config["shortcuts"]["translate_and_send"] = self.translate_send_shortcut.text()
        self.config["shortcuts"]["translate_selected"] = self.translate_selected_shortcut.text()
        
        # Save config without API key
        save_config = self.config.copy()
        save_config["api"]["api_key"] = ""
        
        with open("config.json", "w") as f:
            json.dump(save_config, f, indent=4)
        
        logger.info("Settings saved successfully")
        self.accept()


class MessageItem(QWidget):
    def __init__(self, text, is_original=True, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Create a frame for the message
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        
        # Set different styles for original and translated messages
        if is_original:
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: #313338;
                    border-radius: 8px;
                    padding: 12px;
                }
                QLabel {
                    color: #DBDEE1;
                    font-size: 13px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        else:
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: #383A40;
                    border-radius: 8px;
                    padding: 12px;
                }
                QLabel {
                    color: #DBDEE1;
                    font-size: 13px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        
        # Create layout for the frame
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(8)
        
        # Add message text with better formatting
        self.message_label = QLabel(text)
        self.message_label.setWordWrap(True)
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        frame_layout.addWidget(self.message_label)
        
        # Add the frame to the main layout
        self.layout.addWidget(self.frame)
        
        # Set the layout for this widget
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("AI Translator for Discord")
        self.setMinimumSize(900, 700)  # Slightly larger default size
        
        # Set window style with enhanced modern design
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1F22;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QListWidget {
                background-color: #2B2D31;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                border-radius: 8px;
                padding: 8px;
                margin-bottom: 4px;
            }
            QSplitter::handle {
                background-color: #1E1F22;
                width: 2px;
            }
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QPushButton:pressed {
                background-color: #3C45A5;
            }
            QWidget#column_widget {
                background-color: #2B2D31;
                border-radius: 12px;
                padding: 4px;
            }
            QLabel#header_label {
                color: #FFFFFF;
                font-size: 15px;
                font-weight: bold;
                padding: 12px;
                background-color: #232428;
                border-radius: 8px;
                margin: 4px;
            }
            QLabel#info_label {
                color: #B5BAC1;
                font-size: 12px;
                font-weight: normal;
                padding: 8px;
            }
        """)
        
        # Create central widget with padding
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout with more spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create horizontal splitter
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(2)
        
        # Create sent messages column (CTRL+ALT+T)
        sent_widget = QWidget()
        sent_widget.setObjectName("column_widget")
        sent_layout = QVBoxLayout(sent_widget)
        sent_layout.setContentsMargins(12, 12, 12, 12)
        sent_layout.setSpacing(12)
        
        sent_header = QLabel("✉️ Sent Messages (CTRL+ALT+T)")
        sent_header.setObjectName("header_label")
        sent_header.setAlignment(Qt.AlignCenter)
        sent_layout.addWidget(sent_header)
        
        self.sent_messages_list = QListWidget()
        self.sent_messages_list.setSpacing(8)
        self.sent_messages_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        sent_layout.addWidget(self.sent_messages_list)
        h_splitter.addWidget(sent_widget)
        
        # Create received messages column (CTRL+ALT+R)
        received_widget = QWidget()
        received_widget.setObjectName("column_widget")
        received_layout = QVBoxLayout(received_widget)
        received_layout.setContentsMargins(12, 12, 12, 12)
        received_layout.setSpacing(12)
        
        received_header = QLabel("🔄 Translated Messages (CTRL+ALT+R)")
        received_header.setObjectName("header_label")
        received_header.setAlignment(Qt.AlignCenter)
        received_layout.addWidget(received_header)
        
        self.received_messages_list = QListWidget()
        self.received_messages_list.setSpacing(8)
        self.received_messages_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        received_layout.addWidget(self.received_messages_list)
        h_splitter.addWidget(received_widget)
        
        # Set equal sizes for splitter
        h_splitter.setSizes([1, 1])
        
        main_layout.addWidget(h_splitter)
        
        # Add shortcut info at the bottom with enhanced design
        info_widget = QWidget()
        info_widget.setObjectName("column_widget")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 8, 12, 8)
        
        shortcut_label = QLabel(
            "⌨️ Shortcuts:\n"
            f"• {self.config['shortcuts']['translate_and_send']} - Translate and send message\n"
            f"• {self.config['shortcuts']['translate_selected']} - Translate selected text"
        )
        shortcut_label.setObjectName("info_label")
        shortcut_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(shortcut_label)
        
        main_layout.addWidget(info_widget)
        
        # Create translation thread
        self.translation_thread = None
        
        # Set up system tray
        self.setup_system_tray()
        
        # Register keyboard shortcuts
        self.register_shortcuts()
        
        # Show the window
        self.show()
    
    def setup_system_tray(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set icon
        icon_path = "icon.ico" if os.path.exists("icon.ico") else None
        if icon_path:
            try:
                self.tray_icon.setIcon(QIcon(icon_path))
                self.setWindowIcon(QIcon(icon_path))
            except Exception as e:
                logger.error(f"Failed to set icon: {str(e)}", exc_info=True)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Add Send Translation submenu (CTRL+ALT+T)
        send_menu = tray_menu.addMenu("Send Translation (CTRL+ALT+T)")
        send_group = QActionGroup(self)
        send_group.setExclusive(True)
        
        send_pairs = [
            {"name": "English to Portuguese", "source": "en", "target": "pt"},
            {"name": "Russian to Portuguese", "source": "ru", "target": "pt"},
            {"name": "Auto-detect to Portuguese", "source": "auto", "target": "pt"}
        ]
        
        default_send_pair = self.config["ui"].get("default_send_pair", "English to Portuguese")
        
        for pair in send_pairs:
            action = QAction(pair["name"], self, checkable=True)
            action.setData(pair)
            send_group.addAction(action)
            send_menu.addAction(action)
            if pair["name"] == default_send_pair:
                action.setChecked(True)
        
        send_group.triggered.connect(self.on_send_pair_changed)
        
        # Add Receive Translation submenu (CTRL+ALT+R)
        receive_menu = tray_menu.addMenu("Receive Translation (CTRL+ALT+R)")
        receive_group = QActionGroup(self)
        receive_group.setExclusive(True)
        
        receive_pairs = [
            {"name": "Portuguese to English", "source": "pt", "target": "en"},
            {"name": "Auto-detect to English", "source": "auto", "target": "en"}
        ]
        
        default_receive_pair = self.config["ui"].get("default_receive_pair", "Portuguese to English")
        
        for pair in receive_pairs:
            action = QAction(pair["name"], self, checkable=True)
            action.setData(pair)
            receive_group.addAction(action)
            receive_menu.addAction(action)
            if pair["name"] == default_receive_pair:
                action.setChecked(True)
        
        receive_group.triggered.connect(self.on_receive_pair_changed)
        
        # Add other menu items
        tray_menu.addSeparator()
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(settings_action)
        tray_menu.addAction(about_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def register_shortcuts(self):
        try:
            # Unregister any existing shortcuts
            keyboard.unhook_all()
            
            # Register shortcuts
            keyboard.add_hotkey(
                self.config["shortcuts"]["translate_and_send"],
                self.translate_and_send,
                suppress=True
            )
            
            keyboard.add_hotkey(
                self.config["shortcuts"]["translate_selected"],
                self.translate_selected,
                suppress=True
            )
            
            logger.info("Keyboard shortcuts registered successfully")
        except Exception as e:
            logger.error(f"Failed to register keyboard shortcuts: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to register keyboard shortcuts: {str(e)}\n\nThe application may not work correctly."
            )
    
    def get_selected_text(self):
        logger.info("Getting selected text")
        # Save current clipboard content
        win32clipboard.OpenClipboard()
        try:
            original_clipboard = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            logger.debug(f"Original clipboard content: {original_clipboard[:50]}...")
        except Exception as e:
            logger.warning(f"Could not get original clipboard content: {str(e)}")
            original_clipboard = ""
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        
        # Simulate Ctrl+C to copy selected text
        logger.debug("Simulating Ctrl+C to copy selected text")
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.1)  # Give time for the clipboard to update
        
        # Get the selected text from clipboard
        win32clipboard.OpenClipboard()
        try:
            selected_text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            logger.debug(f"Selected text: {selected_text[:50]}...")
        except Exception as e:
            logger.warning(f"Could not get selected text from clipboard: {str(e)}")
            selected_text = ""
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        
        # Restore original clipboard content
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        if original_clipboard:
            try:
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, original_clipboard)
                logger.debug("Restored original clipboard content")
            except Exception as e:
                logger.warning(f"Could not restore original clipboard content: {str(e)}")
        win32clipboard.CloseClipboard()
        
        return selected_text
    
    def translate_and_send(self):
        logger.info("translate_and_send shortcut triggered")
        # Move to the main thread before getting selected text
        QTimer.singleShot(0, self._translate_and_send)

    def _translate_and_send(self):
        # Get the selected text
        text = self.get_selected_text()
        
        if not text:
            logger.warning("No text selected")
            self.show_notification("Error", "No text selected")
            return
        
        logger.info(f"Translating text: {text[:50]}...")
        
        # Add the original message to the list
        self.add_message(text, True, "sent")  # Added message type
        
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_start"])
                logger.debug("Played translation_start sound")
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Get the current language pair for sending
        for pair in self.tray_icon.contextMenu().actions()[0].menu().actions():
            if pair.isChecked():
                lang_pair = pair.data()
                break
        
        # Start translation in a separate thread
        self.translation_thread = TranslationThread(
            text, 
            lang_pair["source"], 
            lang_pair["target"],
            self.config["api"]
        )
        self.translation_thread.translation_complete.connect(self.on_translate_and_send_complete)
        self.translation_thread.start()
    
    def on_translate_and_send_complete(self, original_text, translated_text):
        logger.info("Translation completed, sending message")
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_complete"])
                logger.debug("Played translation_complete sound")
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Check if the translation contains an error message
        if translated_text.startswith("Translation error:"):
            logger.error(f"Translation error: {translated_text}")
            self.show_notification("Error", translated_text)
            self.add_message(translated_text, False, "sent")  # Added message_type
            return
        
        logger.debug(f"Translated text: {translated_text[:50]}...")
        
        # Add the translated message to the list
        self.add_message(translated_text, False, "sent")  # Added message_type
        
        # Set the translated text to clipboard
        pyperclip.copy(translated_text)
        logger.debug("Copied translated text to clipboard")
        
        # Simulate Ctrl+A to select all text
        logger.debug("Simulating Ctrl+A to select all text")
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.1)
        
        # Simulate Ctrl+V to paste the translated text
        logger.debug("Simulating Ctrl+V to paste translated text")
        keyboard.press_and_release('ctrl+v')
        time.sleep(0.1)
        
        # Simulate Enter to send the message
        logger.debug("Simulating Enter to send message")
        keyboard.press_and_release('enter')
    
    def translate_selected(self):
        logger.info("translate_selected shortcut triggered")
        # Move to the main thread before getting selected text
        QTimer.singleShot(0, self._translate_selected)

    def _translate_selected(self):
        # Get the selected text
        text = self.get_selected_text()
        
        if not text:
            logger.warning("No text selected")
            self.show_notification("Error", "No text selected")
            return
        
        # Add the original message to the list
        self.add_message(text, True, "received")  # Changed message type
        
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_start"])
                logger.debug("Played translation_start sound")
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Get the current language pair for receiving
        for pair in self.tray_icon.contextMenu().actions()[1].menu().actions():
            if pair.isChecked():
                lang_pair = pair.data()
                break
        
        # Start translation in a separate thread
        self.translation_thread = TranslationThread(
            text, 
            lang_pair["source"], 
            lang_pair["target"],
            self.config["api"]
        )
        self.translation_thread.translation_complete.connect(self.on_translate_selected_complete)
        self.translation_thread.start()
        
        # Show the window
        self.show()
        self.activateWindow()
    
    def on_translate_selected_complete(self, original_text, translated_text):
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_complete"])
                logger.debug("Played translation_complete sound")
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Check if the translation contains an error message
        if translated_text.startswith("Translation error:"):
            logger.error(f"Translation error: {translated_text}")
            self.show_notification("Error", translated_text)
            self.add_message(translated_text, False, "received")  # Added message_type
            return
        
        logger.debug(f"Translated text: {translated_text[:50]}...")
        
        # Add the translated message to the list
        self.add_message(translated_text, False, "received")  # Added message_type
        
        # Show notification with translated text
        self.show_notification("Translation", translated_text)
    
    def translate_input(self):
        # Get text from input field
        text = self.text_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter text to translate.")
            return
        
        # Add the original message to the list
        self.add_message(text, True)
        
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_start"])
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Get the current language pair
        lang_pair_index = self.lang_combo.currentIndex()
        lang_pair = self.config["ui"]["language_pairs"][lang_pair_index]
        
        # Start translation in a separate thread
        self.translation_thread = TranslationThread(
            text, 
            lang_pair["source"], 
            lang_pair["target"],
            self.config["api"]
        )
        self.translation_thread.translation_complete.connect(self.on_translate_input_complete)
        self.translation_thread.start()
    
    def on_translate_input_complete(self, original_text, translated_text):
        # Play sound if enabled
        if self.config["sounds"]["enable_sounds"]:
            try:
                playsound(self.config["sounds"]["translation_complete"])
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Check if the translation contains an error message
        if translated_text.startswith("Translation error:"):
            QMessageBox.critical(self, "Error", translated_text)
            self.add_message(translated_text, False)
            return
        
        # Add the translated message to the list
        self.add_message(translated_text, False)
        
        # Clear the input field
        self.clear_input()
    
    def clear_input(self):
        self.text_input.clear()
    
    def add_message(self, text, is_original, message_type="sent"):
        # Create a custom widget for the message
        message_widget = MessageItem(text, is_original)
        
        # Create a list item and set its size
        item = QListWidgetItem()
        item.setSizeHint(message_widget.sizeHint())
        
        # Add to the appropriate list based on message type
        if message_type == "sent":
            self.sent_messages_list.addItem(item)
            self.sent_messages_list.setItemWidget(item, message_widget)
            self.sent_messages_list.scrollToBottom()
        else:
            self.received_messages_list.addItem(item)
            self.received_messages_list.setItemWidget(item, message_widget)
            self.received_messages_list.scrollToBottom()
    
    def show_notification(self, title, message):
        logger.info(f"Showing notification: {title}")
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.Information,
            self.config["ui"]["notification_duration"]
        )
    
    def show_settings(self):
        logger.info("Opening settings dialog")
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the language combo box
            self.lang_combo.setCurrentIndex(self.config["ui"]["default_language_pair"])
            
            # Re-register shortcuts with new configuration
            try:
                self.register_shortcuts()
                logger.info("Re-registered shortcuts after settings change")
            except Exception as e:
                logger.error(f"Failed to re-register shortcuts: {str(e)}", exc_info=True)
                self.show_notification("Error", f"Failed to register shortcuts: {str(e)}")
    
    def show_about(self):
        logger.info("Showing about dialog")
        QMessageBox.about(
            self,
            "About AI Translator",
            "AI Translator for Discord\n\n"
            "A tool to translate messages in Discord using AI.\n\n"
            "Version 1.0.0"
        )
    
    def closeEvent(self, event):
        # Hide the window instead of closing it
        event.ignore()
        self.hide()
        self.show_notification(
            "AI Translator",
            "The application is still running in the system tray."
        )

    def on_send_pair_changed(self, action):
        pair = action.data()
        self.config["ui"]["default_send_pair"] = pair["name"]
        self.save_config()
        self.show_notification("Translation Direction", f"Send translation set to: {pair['name']}")

    def on_receive_pair_changed(self, action):
        pair = action.data()
        self.config["ui"]["default_receive_pair"] = pair["name"]
        self.save_config()
        self.show_notification("Translation Direction", f"Receive translation set to: {pair['name']}")

    def save_config(self):
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")


class AITranslator:
    def __init__(self):
        logger.info("Initializing AI Translator application")
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Load environment variables
        load_dotenv(override=True)  # Add override=True to ensure env vars are reloaded
        
        # Check if API key is available
        if not os.getenv("GROQ_API_KEY"):
            logger.warning("API key not found in environment variables")
            QMessageBox.warning(
                None,
                "Configuration Warning",
                "API key not found in environment variables.\nPlease check your .env file."
            )
        
        # Load configuration
        self.load_config()
        
        # Create directories if they don't exist
        os.makedirs("sounds", exist_ok=True)
        
        # Create default sound files if they don't exist
        self.create_default_sounds()
        
        # Create main window
        self.main_window = MainWindow(self.config)
    
    def load_config(self):
        default_config = {
            "api": {
                "provider": "groq",
                "api_key": os.getenv("GROQ_API_KEY", ""),  # Get API key from environment
                "model": "llama3-70b-8192"
            },
            "shortcuts": {
                "translate_and_send": "ctrl+alt+t",
                "translate_selected": "ctrl+alt+r"
            },
            "sounds": {
                "enable_sounds": True,
                "translation_start": "sounds/start.wav",
                "translation_complete": "sounds/complete.wav"
            },
            "ui": {
                "notification_duration": 5000,
                "default_send_pair": "English to Portuguese",
                "default_receive_pair": "Portuguese to English"
            }
        }

        try:
            logger.info("Loading configuration")
            # Load existing config
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    existing_config = json.load(f)
                
                # Update default config with existing values, but keep API key from environment
                self.config = default_config
                for section in existing_config:
                    if section in self.config:
                        if section == "api":
                            # Don't override API key from environment
                            existing_config[section].pop("api_key", None)
                        self.config[section].update(existing_config[section])
            else:
                self.config = default_config
            
            # Save updated config (without API key)
            save_config = self.config.copy()
            save_config["api"]["api_key"] = ""  # Don't save API key to file
            with open("config.json", "w") as f:
                json.dump(save_config, f, indent=4)
            
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load/save config.json: {str(e)}. Using default configuration.")
            self.config = default_config
    
    def create_default_sounds(self):
        logger.info("Creating default sound files if they don't exist")
        # This is a placeholder. In a real app, you would include actual sound files.
        # For now, we'll just create empty files
        if not os.path.exists(self.config["sounds"]["translation_start"]):
            with open(self.config["sounds"]["translation_start"], "wb") as f:
                pass
        
        if not os.path.exists(self.config["sounds"]["translation_complete"]):
            with open(self.config["sounds"]["translation_complete"], "wb") as f:
                pass
    
    def run(self):
        logger.info("Starting application main loop")
        return self.app.exec_()


if __name__ == "__main__":
    try:
        logger.info("Starting AI Translator application")
        translator = AITranslator()
        exit_code = translator.run()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        QMessageBox.critical(
            None,
            "Critical Error",
            f"An unhandled exception occurred:\n\n{str(e)}\n\nPlease check the log file for details."
        )
        sys.exit(1) 