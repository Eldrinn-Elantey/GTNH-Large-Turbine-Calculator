import customtkinter as ctk

class SteamGenTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        ctk.CTkLabel(self, text="Steam Generation - coming soon").pack(pady=20)
