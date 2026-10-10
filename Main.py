import os, json, threading, contextlib
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
import poster

# বাংলা লিখতে চাইলে রিপোতে bengali.ttf (Noto Sans Bengali) যোগ করুন
FONT = "bengali.ttf" if os.path.exists("bengali.ttf") else "Roboto"

HINT = ('{"facebook":{"page_id":"","token":""},\n'
        '"twitter":{"api_key":"","api_secret":"","access_token":"","access_secret":""},\n'
        '"youtube":{"client_id":"","client_secret":"","refresh_token":"","privacy":"private"},\n'
        '"linkedin":{"token":"","author_urn":"urn:li:person:xxxx"}}')


class Writer:
    def __init__(self, cb): self.cb = cb
    def write(self, s):
        if s.strip():
            Clock.schedule_once(lambda dt: self.cb(s.strip()))
    def flush(self): pass


class PosterApp(App):
    def build(self):
        poster.CFG_PATH = os.path.join(self.user_data_dir, "config.json")
        self.busy = False
        self.ev = None
        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        root.add_widget(Label(text="Excel file path", size_hint_y=None, height=30, font_name=FONT))
        self.path = TextInput(text="/sdcard/Download/posts.xlsx", multiline=False,
                              size_hint_y=None, height=48, font_name=FONT)
        root.add_widget(self.path)

        root.add_widget(Label(text="Accounts config (JSON)", size_hint_y=None, height=30, font_name=FONT))
        self.cfg = TextInput(hint_text=HINT, size_hint_y=0.4, font_size="12sp", font_name=FONT)
        if os.path.exists(poster.CFG_PATH):
            self.cfg.text = open(poster.CFG_PATH).read()
        root.add_widget(self.cfg)

        row = BoxLayout(size_hint_y=None, height=52, spacing=6)
        b1 = Button(text="Save config", font_name=FONT); b1.bind(on_release=self.save_cfg)
        b2 = Button(text="Run now", font_name=FONT); b2.bind(on_release=lambda *_: self.run_posts())
        b3 = ToggleButton(text="Auto (30s)", font_name=FONT); b3.bind(state=self.toggle_auto)
        for b in (b1, b2, b3): row.add_widget(b)
        root.add_widget(row)

        sv = ScrollView()
        self.log = Label(text="Ready.", size_hint_y=None, halign="left", valign="top", font_name=FONT)
        self.log.bind(width=lambda *_: setattr(self.log, "text_size", (self.log.width, None)),
                      texture_size=lambda *_: setattr(self.log, "height", self.log.texture_size[1]))
        sv.add_widget(self.log)
        root.add_widget(sv)
        return root

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        except ImportError:
            pass

    def say(self, s):
        self.log.text += "\n" + s

    def save_cfg(self, *_):
        try:
            json.loads(self.cfg.text)
        except Exception as e:
            return self.say(f"JSON error: {e}")
        with open(poster.CFG_PATH, "w") as f:
            f.write(self.cfg.text)
        self.say("Config saved.")

    def toggle_auto(self, _, state):
        if state == "down":
            self.ev = Clock.schedule_interval(lambda dt: self.run_posts(), 30)
            self.say("Auto ON (keep app open).")
        elif self.ev:
            self.ev.cancel(); self.ev = None
            self.say("Auto OFF.")

    def run_posts(self):
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self._work, daemon=True).start()

    def _work(self):
        try:
            with contextlib.redirect_stdout(Writer(self.say)):
                poster.run_once(self.path.text.strip())
        except SystemExit as e:
            Clock.schedule_once(lambda dt: self.say(str(e)))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.say(f"Error: {e}"))
        finally:
            self.busy = False


if __name__ == "__main__":
    PosterApp().run()
