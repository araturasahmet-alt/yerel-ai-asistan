import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import ollama
import threading
from PyPDF2 import PdfReader
from PIL import Image
import pyttsx3

# Görsel Temayı Modern Koyu Mod Olarak Ayarla
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AIChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Yerel Yapay Zeka Asistanı")
        self.geometry("850x650")
        self.minsize(700, 500)

        # Temel Değişkenler
        self.pdf_context = ""
        self.current_image_path = None
        self.last_ai_response = ""
        
        # Türkçe Ses Motoru
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 165)

        # Ana Izgara Yapısı
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ================= 1. ÜST BİLGİ VE MOD SEÇİM BARU =================
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self.top_frame.grid_columnconfigure(1, weight=1)

        # Başlık
        self.title_label = ctk.CTkLabel(self.top_frame, text="🤖 Yerel Asistan", font=("Segoe UI", 18, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")

        # Durum Bilgisi
        self.status_label = ctk.CTkLabel(self.top_frame, text="Durum: Hazır 🟢", font=("Segoe UI", 12), text_color="#81c784")
        self.status_label.grid(row=0, column=1, sticky="e", padx=(0, 15))

        # Asistan Modı Seçici
        self.persona_option = ctk.CTkOptionMenu(
            self.top_frame, 
            values=["🤖 Genel Asistan", "💻 Yazılım Yardımcısı", "📝 Özetleme Uzmanı"],
            width=160
        )
        self.persona_option.grid(row=0, column=2, sticky="e")

        # ================= 2. SOHBET EKRANI =================
        self.chat_history = ctk.CTkTextbox(
            self, state="disabled", wrap="word", 
            font=("Segoe UI", 13), corner_radius=12
        )
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # ================= 3. YÜKLENEN DOSYA BİLGİ BARU =================
        self.file_status_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 11), text_color="#ffb74d")
        self.file_status_label.grid(row=2, column=0, sticky="w", padx=25, pady=(0, 5))

        # ================= 4. ALT ARAÇ VE MESAJA GİRİŞ ALANI =================
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Metin Giriş Kutusu
        self.entry = ctk.CTkEntry(
            self.bottom_frame, 
            placeholder_text="Mesajınızı veya sorunuzu buraya yazın...", 
            font=("Segoe UI", 13), height=45, corner_radius=10
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda event: self.start_send_thread())

        # Gönder Butonu
        self.send_button = ctk.CTkButton(
            self.bottom_frame, text="Gönder 🚀", 
            command=self.start_send_thread, font=("Segoe UI", 13, "bold"), 
            height=45, width=110, corner_radius=10
        )
        self.send_button.grid(row=0, column=1)

        # Eklenti ve İşlem Butonları Çubuğu
        self.actions_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.actions_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Butonlar
        ctk.CTkButton(self.actions_frame, text="📄 Belge Ekle", command=self.load_pdf, width=100, height=32, fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=(0, 5))
        ctk.CTkButton(self.actions_frame, text="📷 Fotoğraf Ekle", command=self.load_image, width=110, height=32, fg_color="#d84315", hover_color="#bf360c").pack(side="left", padx=5)
        ctk.CTkButton(self.actions_frame, text="🔊 Sesli Oku", command=self.speak_last_response, width=95, height=32, fg_color="#0288d1", hover_color="#01579b").pack(side="left", padx=5)
        ctk.CTkButton(self.actions_frame, text="💾 Kaydet", command=self.save_chat, width=80, height=32, fg_color="#37474f", hover_color="#263238").pack(side="left", padx=5)
        ctk.CTkButton(self.actions_frame, text="🗑️ Temizle", command=self.clear_chat, width=85, height=32, fg_color="#c62828", hover_color="#b71c1c").pack(side="left", padx=5)

        # Hoş geldin Mesajı
        self.append_message("Sistem", "Merhaba! Size nasıl yardımcı olabilirim? Aşağıdan belge veya fotoğraf ekleyebilir, doğrudan soru sorabilirsiniz.")

    def load_pdf(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Belgeler", "*.pdf *.txt")])
        if file_paths:
            try:
                combined_text = ""
                for file_path in file_paths:
                    if file_path.endswith(".pdf"):
                        reader = PdfReader(file_path)
                        for page in reader.pages:
                            combined_text += page.extract_text() or ""
                    elif file_path.endswith(".txt"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            combined_text += f.read()

                self.pdf_context = combined_text[:15000]
                self.current_image_path = None
                
                filenames = ", ".join([f.split('/')[-1] for f in file_paths])
                self.file_status_label.configure(text=f"📌 Yüklenen Belge: {filenames}")
                self.append_message("Sistem", f"✅ Belge içeriği öğrenildi ({len(file_paths)} dosya). Sorunuzu sorabilirsiniz.")
            except Exception as e:
                self.append_message("Sistem", f"❌ Belge okunurken hata oluştu: {e}")

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Görseller", "*.jpg *.png *.jpeg *.bmp")])
        if file_path:
            try:
                self.current_image_path = file_path
                self.pdf_context = ""
                filename = file_path.split('/')[-1]
                self.file_status_label.configure(text=f"📌 Yüklenen Görsel: {filename}")
                self.append_message("Sistem", f"✅ Görsel yüklendi ({filename}). Görsel hakkında soru sorabilirsiniz.")
            except Exception as e:
                self.append_message("Sistem", f"❌ Görsel yükleme hatası: {e}")

    def start_send_thread(self):
        user_text = self.entry.get().strip()
        if not user_text and not self.current_image_path:
            return

        self.append_message("Siz", user_text)
        self.entry.delete(0, tk.END)
        self.send_button.configure(state="disabled")
        self.status_label.configure(text="Durum: Düşünüyor... 🟡", text_color="#ffb74d")

        threading.Thread(target=self.get_ai_response, args=(user_text,), daemon=True).start()

    def get_ai_response(self, user_text):
        try:
            current_model = 'llama3'
            selected_persona = self.persona_option.get()

            # Sadece Türkçe Konuşma Şartı İçeren Sistem Talimatı
            system_prompt = "Sen yardımsever bir yapay zeka asistanısın. Bütün yanıtlarını SADECE TÜRKÇE olarak ver. Asla başka dil kullanma."
            
            if "Yazılım" in selected_persona:
                system_prompt += " Yazılım ve kodlama konularında uzman yanıtlar sağla."
            elif "Özetleme" in selected_persona:
                system_prompt += " Metinleri kısa, net ve maddeler halinde Türkçe özetle."

            messages = [{'role': 'system', 'content': system_prompt}]

            if self.current_image_path:
                current_model = 'llama3-vision'
                messages.append({
                    'role': 'user',
                    'content': (user_text or "Bu görselde ne var? Türkçe açıkla.") + "\n(Lütfen cevabı sadece Türkçe ver.)",
                    'images': [self.current_image_path]
                })
            elif self.pdf_context:
                full_prompt = f"Aşağıdaki belgeye dayanarak cevabı SADECE TÜRKÇE ver:\n\n--- BELGE ---\n{self.pdf_context}\n------------\n\nSoru: {user_text}"
                messages.append({'role': 'user', 'content': full_prompt})
            else:
                messages.append({'role': 'user', 'content': user_text})

            response = ollama.chat(model=current_model, messages=messages)
            bot_reply = response['message']['content']
            
            self.last_ai_response = bot_reply
            self.append_message("Asistan", bot_reply)

        except Exception as e:
            self.append_message("Hata", f"İşlem sırasında bir hata oluştu. Bağlantıyı kontrol edin. ({e})")
        finally:
            self.send_button.configure(state="normal")
            self.status_label.configure(text="Durum: Hazır 🟢", text_color="#81c784")

    def speak_last_response(self):
        if self.last_ai_response:
            threading.Thread(target=lambda: self.tts_engine.say(self.last_ai_response) or self.tts_engine.runAndWait(), daemon=True).start()
        else:
            messagebox.showinfo("Bilgi", "Seslendirilecek bir yanıt bulunmuyor.")

    def append_message(self, sender, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert(tk.END, f"[{sender}]\n{text}\n\n" + "─"*50 + "\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.yview(tk.END)

    def clear_chat(self):
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state="disabled")
        self.pdf_context = ""
        self.current_image_path = None
        self.last_ai_response = ""
        self.file_status_label.configure(text="")
        self.append_message("Sistem", "Sohbet ekranı ve hafıza temizlendi.")

    def save_chat(self):
        chat_content = self.chat_history.get("1.0", tk.END).strip()
        if not chat_content:
            messagebox.showinfo("Bilgi", "Kaydedilecek sohbet geçmişi yok.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Metin Dosyası", "*.txt")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(chat_content)
            messagebox.showinfo("Başarılı", "Sohbet kaydı başarıyla oluşturuldu!")

if __name__ == "__main__":
    app = AIChatApp()
    app.mainloop()
