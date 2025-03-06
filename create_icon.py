from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple icon for the application."""
    # Create a new image with a white background
    size = (256, 256)
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a circle
    circle_center = (128, 128)
    circle_radius = 120
    draw.ellipse(
        (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ),
        fill=(65, 105, 225, 255)  # Royal Blue
    )
    
    # Draw a smaller circle
    small_circle_radius = 100
    draw.ellipse(
        (
            circle_center[0] - small_circle_radius,
            circle_center[1] - small_circle_radius,
            circle_center[0] + small_circle_radius,
            circle_center[1] + small_circle_radius
        ),
        fill=(30, 144, 255, 255)  # Dodger Blue
    )
    
    # Try to draw text "AI" in the center
    try:
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 100)
        except:
            font = ImageFont.load_default()
        
        # Draw the text
        text = "AI"
        text_width, text_height = draw.textsize(text, font=font)
        text_position = (
            circle_center[0] - text_width // 2,
            circle_center[1] - text_height // 2
        )
        draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)
    except Exception as e:
        print(f"Could not add text to icon: {e}")
    
    # Save as .ico file
    try:
        image.save("icon.ico", format="ICO")
        print("Icon created: icon.ico")
    except Exception as e:
        print(f"Could not save icon: {e}")
        # Try to save as PNG instead
        try:
            image.save("icon.png", format="PNG")
            print("Icon created as PNG instead: icon.png")
            print("You'll need to convert this to .ico format manually.")
        except:
            print("Could not create icon at all.")

if __name__ == "__main__":
    print("Creating application icon...")
    try:
        from PIL import Image, ImageDraw, ImageFont
        create_icon()
    except ImportError:
        print("Pillow library not found. Installing...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageDraw, ImageFont
        create_icon()
    print("Done!") 