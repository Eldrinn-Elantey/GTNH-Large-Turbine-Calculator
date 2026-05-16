import customtkinter as ctk

class FuelsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        ctk.CTkLabel(self, text="Fuels Reference - coming soon").pack(pady=20)
