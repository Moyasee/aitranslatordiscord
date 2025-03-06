# AI Translator for Discord

A Windows application that helps translate messages in Discord using AI.

## Features

- Modern user interface that shows your original messages and translations
- Translate your messages before sending with CTRL+ALT+T
- Translate other users' messages with CTRL+ALT+R
- Translate text directly in the application
- Specialized support for Portuguese-English translations
- Uses Groq AI API for high-quality translations
- Provides audio feedback when operations are completed
- Runs in the background as a system tray application

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone or download this repository
3. Copy `.env.example` to `.env` and add your Groq API key:
   ```bash
   cp .env.example .env
   ```
4. Edit `.env` and replace `your_api_key_here` with your actual Groq API key
5. Run the setup script:
   ```bash
   setup.bat
   ```
   This will:
   - Install all required dependencies
   - Generate notification sounds
   - Create an application icon
   - Start the application

⚠️ **Important**: Never commit your `.env` file containing real API keys to git!

## Usage

### Setting Up

1. After starting the application, you'll see the main window with a translation interface
2. Click on "Settings" in the system tray icon menu to configure the application
3. Enter your Groq API key (you can get one from https://console.groq.com/)
4. Select your default language pair (Portuguese to English is set as default)
5. Click "Save"

### Using the Application Interface

1. Type or paste text in the input field at the bottom of the window
2. Select the desired language pair from the dropdown
3. Click "Translate" to translate the text
4. The original text and translation will appear in the message history

### Translating Your Messages in Discord

1. In Discord, type a message you want to translate
2. Select the text
3. Press CTRL+ALT+T
4. The text will be translated and automatically sent
5. The original and translated messages will also appear in the application window

### Translating Other Users' Messages in Discord

1. In Discord, select someone else's message
2. Press CTRL+ALT+R
3. A notification will appear with the translated text
4. The original and translated messages will also appear in the application window

## Language Support

The application is configured with the following language pairs:
- Portuguese to English (default)
- English to Portuguese
- Auto-detect to Portuguese
- Auto-detect to English
- English to Spanish
- English to French
- English to German
- English to Russian

## Building the Executable

To build the standalone .exe file:

1. Run the build script:
   ```
   python build.py
   ```
2. The executable will be in the `dist` folder

## Configuration

Edit the `config.json` file to change:
- API keys
- Keyboard shortcuts
- Sound settings
- Language pairs

## Troubleshooting

If you're experiencing issues with the application:

1. **Run with administrator privileges**: Some keyboard shortcuts may require admin rights
   ```
   run_as_admin.bat
   ```

2. **Run the diagnostics tool**: This will check for common issues
   ```
   debug.bat
   ```

3. **Check the log file**: The application creates a log file at `translator_debug.log`

4. **Common issues**:
   - **No icon in system tray**: Make sure the icon.ico file was created correctly
   - **No sound**: Check if the sound files were generated in the sounds directory
   - **Translation errors**: Verify your API key and internet connection
   - **Keyboard shortcuts not working**: Make sure no other application is using the same shortcuts and try running as administrator
   - **Window not appearing**: Right-click the system tray icon and select "Show Window"

## License

This project is open source and available under the MIT License. 