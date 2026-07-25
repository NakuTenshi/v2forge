# v2forge
<a href="https://github.com/NakuTenshi/v2ray_config_collector/">English</a>

اسکریپت `collect.py` کانفیگ‌های v2ray (vmess/vless/trojan/ss/hysteria/etc.) را از ۸۷ منبع تأیید شده در `raw.githubusercontent.com` جمع‌آوری می‌کند، آن‌ها را با `python_v2ray` پارس می‌کند و سرورهای قابل دسترس را از طریق TCP handshake فیلتر می‌کند. کانفیگ‌های باقی‌مانده در `./configs/configs.txt` ذخیره می‌شوند.

## نحوه استفاده

این ریپو را کلون کنید:

```bash
git clone https://github.com/NakuTenshi/v2ray_config_collector
cd v2ray_config_collector
```

کتابخانه‌های مورد نیاز را نصب کنید:

```bash
pip3 install -r requirements.txt
```

اسکریپت را اجرا کنید:

```bash
python3 collect.py
```

## نحوه کار

1. لینک‌های منابع را از `sources.txt` (۸۷ منبع تأیید شده) می‌خواند
2. برای هر منبع یک thread جداگانه برای دریافت همزمان کانفیگ‌ها ایجاد می‌کند
3. هر خط را با `python_v2ray.config_parser.parse_uri()` پارس می‌کند
4. دسترسی‌پذیری را با TCP handshake (تایم‌اوت ۲ ثانیه) تست می‌کند
5. کانفیگ‌های قابل دسترس را به `./configs/configs.txt` اضافه می‌کند

### پروتکل‌های پشتیبانی شده

`vmess` · `vless` · `trojan` · `shadowsocks` · `socks` · `wireguard` · `hysteria` · `hysteria2` · `hy2`

## نوت

> فایل `sources.txt` باید در کنار فایل `collect.py` باشد

> برای اضافه کردن منابع جدید، لینک را به `sources.txt` اضافه کنید (هر خط یک لینک، باید به یک لیست کانفیگ متنی در `raw.githubusercontent.com` اشاره کند)

> خطاهای پردازنشده thread‌های worker در فایل `errors.log` ثبت می‌شوند

## ریز نکته‌ها

بعد از جمع‌آوری، اگر تعداد کانفیگ‌ها بیشتر از ۱۰۰۰ شد (اضافه کردن به نسخه موبایل سخت می‌شود)، خروجی را تقسیم کنید:

```bash
split -l 1000 -d --additional-suffix=.txt configs/configs.txt config_
```

خروجی:

```text
config_00.txt  config_01.txt  config_02.txt  config_03.txt
```
