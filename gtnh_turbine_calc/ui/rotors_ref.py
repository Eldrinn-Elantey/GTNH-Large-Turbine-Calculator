import customtkinter as ctk

class RotorsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        ctk.CTkLabel(self, text="Rotors Reference - coming soon").pack(pady=20)
