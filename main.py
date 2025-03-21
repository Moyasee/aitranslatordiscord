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
                            QActionGroup, QShortcut)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QKeySequence, QCursor
import win32gui
import win32con
import win32api
import win32clipboard
from playsound import playsound
from dotenv import load_dotenv
from langdetect import detect
from PyQt5.QtCore import QPropertyAnimation

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
        retries = 3
        while retries > 0:
            try:
                return self._try_translation()
            except Exception as e:
                retries -= 1
                if retries == 0:
                    # Try fallback translation service
                    try:
                        return self._fallback_translation()
                    except:
                        raise e
                time.sleep(1)  # Wait before retry
                
    def _fallback_translation(self):
        """Fallback to a different translation service"""
        # Implement alternative translation service
        # Could use a different API or local model
        pass

    def _try_translation(self):
        """Attempt to translate text using Groq API"""
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
        self.layout.setSpacing(4)
        
        # Create a frame for the message
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        
        # Set different styles for original and translated messages
        if is_original:
            self.frame.setStyleSheet("""
                QFrame {
                    background-color: #36393F;
                    border: 2px solid #2F3136;
                    border-radius: 12px;
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
                    background-color: #3B4C72;
                    border: 2px solid #2F3136;
                    border-radius: 12px;
                    padding: 12px;
                }
                QLabel {
                    color: #FFFFFF;
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
        
        # Set up context menu
        self.setup_context_menu()
        
        # Set the layout for this widget
        self.setLayout(self.layout)

        # Add language indicator
        self.add_language_indicator()

    def add_language_indicator(self, detected_lang=None):
        if detected_lang:
            lang_label = QLabel(f"Detected: {detected_lang}")
            lang_label.setStyleSheet("""
                QLabel {
                    color: #72767D;
                    font-size: 11px;
                    padding: 2px 6px;
                    background: #2F3136;
                    border-radius: 4px;
                }
            """)
            self.layout.addWidget(lang_label)

    def setup_context_menu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        menu = QMenu()
        
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(lambda: pyperclip.copy(self.message_label.text()))
        
        resend_action = menu.addAction("Translate Again")
        resend_action.triggered.connect(lambda: self.parent().retranslate_message(self.message_label.text()))
        
        menu.exec_(self.mapToGlobal(position))


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("AI Translator")
        self.setMinimumSize(1000, 700)  # Slightly larger default size
        
        # Enhanced modern design with better colors and spacing
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1B1E;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 500;
                padding: 5px;
            }
            QListWidget {
                background-color: #2B2D31;
                border: none;
                border-radius: 12px;
                padding: 12px;
            }
            QListWidget::item {
                border-radius: 8px;
                padding: 8px;
                margin: 4px 2px;
            }
            QSplitter::handle {
                background-color: #2B2D31;
                width: 2px;
            }
            QPushButton {
                background-color: #5865F2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
            QPushButton:pressed {
                background-color: #3C45A5;
            }
            QLineEdit {
                background-color: #2B2D31;
                border: 2px solid #1E1F22;
                border-radius: 8px;
                padding: 8px 12px;
                color: #FFFFFF;
                font-size: 13px;
                margin: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #5865F2;
            }
            QLineEdit::placeholder {
                color: #72767D;
            }
            QWidget#column_widget {
                background-color: #2B2D31;
                border-radius: 16px;
                padding: 8px;
                margin: 4px;
            }
            QLabel#header_label {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
                padding: 16px;
                background-color: #1E1F22;
                border-radius: 10px;
                margin: 4px 4px 12px 4px;
            }
        """)
        
        # Create central widget with padding
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout with more spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create search bars with improved design
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        self.sent_search = QLineEdit()
        self.sent_search.setPlaceholderText("🔍 Search sent messages...")
        self.sent_search.textChanged.connect(self.filter_sent_messages)
        
        self.received_search = QLineEdit()
        self.received_search.setPlaceholderText("🔍 Search received messages...")
        self.received_search.textChanged.connect(self.filter_received_messages)
        
        search_layout.addWidget(self.sent_search)
        search_layout.addWidget(self.received_search)
        
        main_layout.addLayout(search_layout)
        
        # Create horizontal splitter
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(2)
        
        # Create sent messages column
        sent_widget = QWidget()
        sent_widget.setObjectName("column_widget")
        sent_layout = QVBoxLayout(sent_widget)
        sent_layout.setContentsMargins(12, 12, 12, 12)
        sent_layout.setSpacing(12)
        
        sent_header = QLabel("✉️ Original Messages")
        sent_header.setObjectName("header_label")
        sent_header.setAlignment(Qt.AlignCenter)
        sent_layout.addWidget(sent_header)
        
        self.sent_messages_list = QListWidget()
        self.sent_messages_list.setSpacing(8)
        self.sent_messages_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        sent_layout.addWidget(self.sent_messages_list)
        h_splitter.addWidget(sent_widget)
        
        # Create received messages column
        received_widget = QWidget()
        received_widget.setObjectName("column_widget")
        received_layout = QVBoxLayout(received_widget)
        received_layout.setContentsMargins(12, 12, 12, 12)
        received_layout.setSpacing(12)
        
        received_header = QLabel("🔄 Translated Messages")
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
        
        # Create translation thread
        self.translation_thread = None
        
        # Set up system tray
        self.setup_system_tray()
        
        # Register keyboard shortcuts
        self.register_shortcuts()
        
        # Create translation popup
        self.translation_popup = TranslationPopup()
        
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
        logger.info("Getting selected text using multiple methods")
        
        # Try different methods to get text
        text = None
        
        # Method 1: Try getting text from active window directly
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_class = win32gui.GetClassName(hwnd)
            
            # Special handling for Discord
            if "discord" in window_class.lower():
                text = self.get_discord_selected_text()
                if text:
                    logger.info("Successfully got text from Discord")
                    return text
        except Exception as e:
            logger.debug(f"Discord-specific method failed: {e}")

        # Method 2: Try Windows clipboard method
        text = self.get_text_via_clipboard()
        if text:
            logger.info("Successfully got text via clipboard")
            return text
        
        # Method 3: Try OCR if text is still not found
        text = self.get_text_via_ocr()
        if text:
            logger.info("Successfully got text via OCR")
            return text
        
        logger.warning("Failed to get text using all methods")
        return None

    def get_discord_selected_text(self):
        """Attempt to get selected text directly from Discord"""
        # Send Discord's copy shortcut (Ctrl+C)
        keyboard.send('ctrl+c')
        time.sleep(0.1)
        
        try:
            win32clipboard.OpenClipboard()
            text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return text
        except:
            return None

    def get_text_via_ocr(self):
        """Use OCR to get text from screen selection"""
        # This would require adding pytesseract and PIL to requirements.txt
        try:
            # Take screenshot of selected area
            import pytesseract
            from PIL import ImageGrab
            
            # Get screen coordinates (would need to implement selection UI)
            screenshot = ImageGrab.grab(bbox=None)  # bbox would be selection coordinates
            text = pytesseract.image_to_string(screenshot)
            return text.strip()
        except:
            return None
    
    def get_text_via_clipboard(self):
        """Get text using clipboard method"""
        logger.info("Attempting to get text via clipboard")
        
        # Store original clipboard content
        original_clipboard = None
        try:
            original_clipboard = pyperclip.paste()
            logger.debug(f"Original clipboard content: {original_clipboard[:50]}...")
        except Exception as e:
            logger.warning(f"Could not get original clipboard content: {str(e)}")
        
        # Copy selected text
        keyboard.send('ctrl+c')
        time.sleep(0.2)  # Increased delay to ensure clipboard updates
        
        # Get text from clipboard
        try:
            text = pyperclip.paste()
            if text and text != original_clipboard:
                logger.debug(f"Got selected text: {text[:50]}...")
                # Restore original clipboard content
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
                return text
        except Exception as e:
            logger.warning(f"Could not get text from clipboard: {str(e)}")
        
        return None
    
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
        # Preserve formatting
        translated_text = self.preserve_formatting(original_text, translated_text)
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
        
        logger.info(f"Translating text: {text[:50]}...")
        
        # Add the original message to the list
        self.add_message(text, True, "received")  # Changed to "received"
        
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
            except Exception as e:
                logger.warning(f"Could not play sound: {str(e)}")
        
        # Check for errors
        if translated_text.startswith("Translation error:"):
            self.show_notification("Error", translated_text)
            return
        
        # Show translation in popup near cursor
        cursor_pos = QCursor.pos()
        self.translation_popup.show_translation(original_text, translated_text, cursor_pos)
        
        # Still add to history
        self.add_message(original_text, True, "received")
        self.add_message(translated_text, False, "received")
    
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
    
    def add_message(self, text, is_original, message_type="sent", detected_lang=None):
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
        
        # Add language indicator
        message_widget.add_language_indicator(detected_lang)

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

    def setup_language_toggle(self):
        keyboard.add_hotkey('ctrl+alt+l', self.toggle_language_pair)

    def toggle_language_pair(self):
        # Toggle between most common pairs
        send_menu = self.tray_icon.contextMenu().actions()[0].menu()
        receive_menu = self.tray_icon.contextMenu().actions()[1].menu()
        
        # Find current active pairs
        current_send = None
        current_receive = None
        for action in send_menu.actions():
            if action.isChecked():
                current_send = action
        for action in receive_menu.actions():
            if action.isChecked():
                current_receive = action
        
        # Toggle pairs
        if current_send.data()["source"] == "en":
            # Switch to Portuguese to English
            for action in send_menu.actions():
                if action.data()["source"] == "pt":
                    action.trigger()
                    break
        else:
            # Switch to English to Portuguese
            for action in send_menu.actions():
                if action.data()["source"] == "en":
                    action.trigger()
                    break

    def setup_search(self):
        # Create search bars
        search_layout = QHBoxLayout()
        
        self.sent_search = QLineEdit()
        self.sent_search.setPlaceholderText("Search sent messages...")
        self.sent_search.textChanged.connect(self.filter_sent_messages)
        
        self.received_search = QLineEdit()
        self.received_search.setPlaceholderText("Search received messages...")
        self.received_search.textChanged.connect(self.filter_received_messages)
        
        search_layout.addWidget(self.sent_search)
        search_layout.addWidget(self.received_search)
        
        # Add search layout before the splitter
        main_layout.insertLayout(0, search_layout)

    def filter_messages(self, text, list_widget):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            message = widget.message_label.text()
            item.setHidden(text.lower() not in message.lower())

    def filter_sent_messages(self, text):
        self.filter_messages(text, self.sent_messages_list)

    def filter_received_messages(self, text):
        self.filter_messages(text, self.received_messages_list)

    def setup_navigation_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Up"), self, self.select_previous_message)
        QShortcut(QKeySequence("Ctrl+Down"), self, self.select_next_message)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_selected_message)

    def select_previous_message(self):
        current_list = self.focusWidget()
        if isinstance(current_list, QListWidget):
            current_row = current_list.currentRow()
            if current_row > 0:
                current_list.setCurrentRow(current_row - 1)

    def select_next_message(self):
        current_list = self.focusWidget()
        if isinstance(current_list, QListWidget):
            current_row = current_list.currentRow()
            if current_row < current_list.count() - 1:
                current_list.setCurrentRow(current_row + 1)

    def copy_selected_message(self):
        current_list = self.focusWidget()
        if isinstance(current_list, QListWidget):
            current_row = current_list.currentRow()
            if current_row >= 0 and current_row < current_list.count():
                item = current_list.item(current_row)
                if item:
                    widget = current_list.itemWidget(item)
                    if isinstance(widget, MessageItem):
                        pyperclip.copy(widget.message_label.text())

    def detect_language(self, text):
        """Detect the language of input text"""
        try:
            detected = detect(text)
            logger.info(f"Detected language: {detected}")
            return detected
        except:
            logger.warning("Could not detect language")
            return None

    def translate_text(self):
        # Get the text
        text = self.get_selected_text()
        
        # Detect language if using auto-detect
        if self.current_source_lang == "auto":
            detected_lang = self.detect_language(text)
            if detected_lang:
                self.show_notification("Language Detected", f"Detected {detected_lang}")
                # Update UI to show detected language
                self.add_message(text, True, detected_lang=detected_lang)

    def preserve_formatting(self, original_text, translated_text):
        """Preserve original text formatting in translation"""
        # Check for capitalization
        if original_text.isupper():
            translated_text = translated_text.upper()
        elif original_text[0].isupper():
            translated_text = translated_text[0].upper() + translated_text[1:]
        
        # Check for ending punctuation
        if original_text[-1] in '.!?':
            if not translated_text[-1] in '.!?':
                translated_text += original_text[-1]
            
        return translated_text


class TranslationQueue:
    def __init__(self):
        self.queue = []
        self.processing = False
        
    def add_translation(self, text, source_lang, target_lang, callback):
        """Add translation request to queue"""
        self.queue.append({
            'text': text,
            'source': source_lang,
            'target': target_lang,
            'callback': callback
        })
        
        if not self.processing:
            self.process_next()
    
    def process_next(self):
        """Process next translation in queue"""
        if not self.queue:
            self.processing = False
            return
            
        self.processing = True
        request = self.queue.pop(0)
        
        # Start translation thread
        thread = TranslationThread(
            request['text'],
            request['source'],
            request['target']
        )
        thread.translation_complete.connect(request['callback'])
        thread.start()


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


# Add this new class for the floating translation window
class TranslationPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Add Qt.Popup to window flags to handle click-away behavior
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Set background to be semi-transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Create frame for better visuals
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(43, 45, 49, 245);
                border: 1px solid #1E1F22;
                border-radius: 8px;
            }
            QLabel {
                color: #DBDEE1;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: transparent;
            }
        """)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        
        # Add labels for original and translated text
        self.original_label = QLabel()
        self.original_label.setWordWrap(True)
        self.original_label.setStyleSheet("color: #72767D;")
        frame_layout.addWidget(self.original_label)
        
        self.translated_label = QLabel()
        self.translated_label.setWordWrap(True)
        frame_layout.addWidget(self.translated_label)
        
        layout.addWidget(self.frame)
        
        # Add close timer with longer duration
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.start_fade_out)
        
        # Add fade animations
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.finished.connect(self.on_fade_finished)
        
        # Track if we're fading out
        self.is_fading_out = False
    
    def show_translation(self, original_text, translated_text, pos):
        # Reset fade out flag
        self.is_fading_out = False
        
        # Set text
        self.original_label.setText(original_text)
        self.translated_label.setText(translated_text)
        
        # Calculate size
        self.adjustSize()
        width = min(400, self.sizeHint().width())
        self.setFixedWidth(width)
        
        # Position window near cursor but ensure it's visible
        screen = QApplication.screenAt(pos)
        if screen:
            screen_geometry = screen.geometry()
            x = min(pos.x(), screen_geometry.right() - width - 20)
            y = min(pos.y() + 20, screen_geometry.bottom() - self.height() - 20)
            self.move(x, y)
        
        # Show with fade in
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()  # Ensure window is on top
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
        # Start close timer with longer duration
        self.close_timer.start(8000)  # Show for 8 seconds
    
    def start_fade_out(self):
        if not self.is_fading_out:
            self.is_fading_out = True
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.start()
    
    def on_fade_finished(self):
        if self.is_fading_out:
            self.hide()
            self.is_fading_out = False
    
    def enterEvent(self, event):
        if not self.is_fading_out:
            self.close_timer.stop()
            # Ensure full opacity when mouse enters
            self.fade_animation.stop()
            self.setWindowOpacity(1.0)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if not self.is_fading_out:
            self.close_timer.start(3000)  # Hide 3 seconds after mouse leaves
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # Hide popup when clicked
        self.start_fade_out()
        super().mousePressEvent(event)
    
    def focusOutEvent(self, event):
        # Hide popup when focus is lost (clicking outside)
        self.start_fade_out()
        super().focusOutEvent(event)


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