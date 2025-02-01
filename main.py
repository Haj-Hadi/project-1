import threading
import requests as rq
from bs4 import BeautifulSoup as bs
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from bidi.algorithm import get_display
import arabic_reshaper

# تنظیم فونت Vazir به عنوان فونت پیش‌فرض
from kivy.core.text import LabelBase
LabelBase.register(name='Vazir', fn_regular='vazir.ttf')  # مطمئن شوید vazir.ttf در همان دایرکتوری وجود دارد

class CurrencyApp(App):
    def build(self):
        self.dark_mode = False  # وضعیت اولیه: حالت لایت
        root = FloatLayout()

        # تعریف رنگ پس‌زمینه و مستطیل
        with root.canvas.before:
            self.bg_color = Color(1, 1, 1, 1)  # رنگ سفید (پیش‌فرض)
            self.rect = Rectangle(size=root.size, pos=root.pos)

        root.bind(size=self._update_rect, pos=self._update_rect)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.previous_prices = {}
        self.labels = {}

        # اضافه کردن لیبل‌ها با فونت Vazir
        for name in ['دلار', 'طلا ۱۸ عیار', 'طلا ۲۴ عیار', 'تتر', 'نات کوین', 'تون کوین', 'بیت کوین']:
            label = Label(
                text=self.format_persian_text(f'قیمت {name}: در حال دریافت...'),
                font_size='20sp',
                color=(0, 0, 0, 1),  # رنگ مشکی (پیش‌فرض)
                font_name='Vazir'
            )
            self.layout.add_widget(label)
            self.labels[name] = label

        # اضافه کردن دکمه به‌روزرسانی
        self.update_button = Button(
            text=self.format_persian_text('به‌روزرسانی'),
            font_size='18sp',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 1, 1),  # رنگ آبی
            font_name='Vazir'
        )
        self.update_button.bind(on_press=self.on_update_button_click)  # وصل کردن تابع به دکمه
        self.layout.add_widget(self.update_button)

        # اضافه کردن دکمه حالت دارک/لایت
        self.mode_button = Button(
            text=self.format_persian_text('حالت دارک'),
            font_size='14sp',
            size_hint=(None, None),
            size=(100, 30),
            pos_hint={'top': 1, 'right': 1},  # قرار دادن در بالا سمت راست
            background_color=(0.5, 0.5, 0.5, 1),  # رنگ خاکستری
            font_name='Vazir'
        )
        self.mode_button.bind(on_press=self.toggle_dark_mode)  # وصل کردن تابع به دکمه
        root.add_widget(self.mode_button)

        root.add_widget(self.layout)
        Clock.schedule_once(lambda dt: self.update_prices(), 0)  # به‌روزرسانی یک بار در ورود به برنامه
        return root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def format_persian_text(self, text):
        """ مرتب کردن و جهت‌دهی متن فارسی """
        reshaped_text = arabic_reshaper.reshape(text)  # مرتب کردن حروف
        bidi_text = get_display(reshaped_text)  # جهت‌دهی
        return bidi_text

    def toggle_dark_mode(self, instance):
        """ تابع تغییر حالت دارک/لایت """
        self.dark_mode = not self.dark_mode  # معکوس کردن وضعیت حالت دارک
        if self.dark_mode:
            self.bg_color.rgba = (0, 0, 0, 1)  # رنگ پس‌زمینه سیاه
            self.mode_button.text = self.format_persian_text('حالت لایت')
            self.mode_button.background_color = (0.3, 0.3, 0.3, 1)  # رنگ دکمه در حالت دارک
            self.update_button.background_color = (0.1, 0.4, 0.6, 1)  # رنگ دکمه به‌روزرسانی در حالت دارک
            for label in self.labels.values():
                label.color = (1, 1, 1, 1)  # رنگ متن سفید
        else:
            self.bg_color.rgba = (1, 1, 1, 1)  # رنگ پس‌زمینه سفید
            self.mode_button.text = self.format_persian_text('حالت دارک')
            self.mode_button.background_color = (0.5, 0.5, 0.5, 1)  # رنگ دکمه در حالت لایت
            self.update_button.background_color = (0.2, 0.6, 1, 1)  # رنگ دکمه به‌روزرسانی در حالت لایت
            for label in self.labels.values():
                label.color = (0, 0, 0, 1)  # رنگ متن سیاه

    def get_dollar_price(self):
        url = 'https://www.tgju.org/profile/price_dollar_rl'
        result = rq.get(url)
        soup = bs(result.text, 'html.parser')
        price = soup.find('span', {'data-col': 'info.last_trade.PDrCotVal'}).text.replace(',', '')
        return int(price) // 10  # تبدیل ریال به تومان

    def get_gold_price(self, type_):
        url = f'https://www.tgju.org/profile/geram{type_}'
        result = rq.get(url)
        soup = bs(result.text, 'html.parser')
        price = soup.find('span', {'data-col': 'info.last_trade.PDrCotVal'}).text.replace(',', '')
        return int(price) // 10  # تبدیل ریال به تومان

    def fetch_price(self, name, url, dollar_price):
        try:
            result = rq.get(url)
            soup = bs(result.text, 'html.parser')
            price = soup.find('span', {'data-test': 'text-cdp-price-display'}).text
            price = re.sub(r'[\$,]', '', price)  # حذف $ و کاما
            price = int(float(price) * dollar_price)  # تبدیل به تومان
            Clock.schedule_once(lambda dt: self.update_ui(name, price), 0)
        except Exception as e:
            print(f"خطا در دریافت قیمت {name}: {e}")
            Clock.schedule_once(lambda dt: self.update_ui(name, "خطا در دریافت"), 0)

    def update_ui(self, name, price):
        previous_price = self.previous_prices.get(name, None)
        self.previous_prices[name] = price
        if name in self.labels:
            if isinstance(price, int):
                if previous_price is not None and isinstance(previous_price, int):
                    if price > previous_price:
                        text = f'قیمت {name}: {price:,} تومان (▲)'
                        color = (0, 1, 0, 1) if not self.dark_mode else (0, 0.8, 0, 1)  # سبز
                    elif price < previous_price:
                        text = f'قیمت {name}: {price:,} تومان (▼)'
                        color = (1, 0, 0, 1) if not self.dark_mode else (0.8, 0, 0, 1)  # قرمز
                    else:
                        text = f'قیمت {name}: {price:,} تومان'
                        color = (0, 0, 0, 1) if not self.dark_mode else (1, 1, 1, 1)  # سیاه یا سفید
                else:
                    text = f'قیمت {name}: {price:,} تومان'
                    color = (0, 0, 0, 1) if not self.dark_mode else (1, 1, 1, 1)
            else:
                text = f'قیمت {name}: {price}'
                color = (1, 0, 0, 1) if not self.dark_mode else (1, 0.5, 0.5, 1)

            # اعمال جهت‌دهی و مرتب‌سازی برای متن فارسی
            formatted_text = self.format_persian_text(text)
            self.labels[name].text = formatted_text
            self.labels[name].color = color

    def update_prices(self, dt=None):
        dollar_price = self.get_dollar_price()
        self.update_ui('دلار', dollar_price)
        self.update_ui('طلا ۱۸ عیار', self.get_gold_price(18))
        self.update_ui('طلا ۲۴ عیار', self.get_gold_price(24))
        urls = {
            'تتر': 'https://coinmarketcap.com/currencies/tether/',
            'نات کوین': 'https://coinmarketcap.com/currencies/notcoin/',
            'تون کوین': 'https://coinmarketcap.com/currencies/toncoin/',
            'بیت کوین': 'https://coinmarketcap.com/currencies/bitcoin/'
        }
        for name, url in urls.items():
            thread = threading.Thread(target=self.fetch_price, args=(name, url, dollar_price), daemon=True)
            thread.start()

    def on_update_button_click(self, instance):
        """ تابعی که با کلیک روی دکمه فراخوانی می‌شود """
        self.update_prices()

if __name__ == '__main__':
    CurrencyApp().run()