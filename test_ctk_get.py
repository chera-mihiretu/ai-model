import customtkinter as ctk
import tkinter as tk

def test_get():
    app = ctk.CTk()
    txt = ctk.CTkTextbox(app)
    txt.pack()
    txt.insert("1.0", "Hello World")
    
    content = txt.get("1.0", "end-1c")
    print(f"Content: '{content}'")
    print(f"Type: {type(content)}")
    
    # Check what inner widget returns
    if hasattr(txt, '_textbox'):
        inner_content = txt._textbox.get("1.0", "end-1c")
        print(f"Inner Content: '{inner_content}'")

    app.quit()

if __name__ == "__main__":
    test_get()
