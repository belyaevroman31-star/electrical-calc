#!/usr/bin/env python3
"""
Проверка цен el.ru для калькулятора электромонтажа.
Запуск: python check_prices.py [--apply]
Исправление URL: откройте prices_cache.json и обновите urls вручную.
"""
import json, re, sys, time
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(r"D:\сайт\калькулятор материалов")
PRICES_FILE = BASE_DIR / "prices_cache.json"
LOG_FILE = BASE_DIR / "price_check_log.txt"
URLS_FILE = BASE_DIR / "product_urls.json"

# Товары с known URL на el.ru
# Формат: ключ → {url, packs_per_unit}
# packs_per_unit: 0.01 = цена за упаковку/100, 1 = цена за шт
PRODUCTS_DEFAULT = {
    "cableVVG_1_5":     {"url": "https://www.el.ru/catalogue/cable/13/643/", "pack": 1, "search": "ВВГнг-LS 3x1.5"},
    "cableVVG_2_5":     {"url": "https://www.el.ru/catalogue/cable/13/644/", "pack": 1, "search": "ВВГнг-LS 3x2.5"},
    "cableVVG_4":       {"url": "https://www.el.ru/catalogue/cable/13/645/", "pack": 1, "search": "ВВГнг-LS 3x4"},
    "cableVVG_6":       {"url": "https://www.el.ru/catalogue/cable/13/646/", "pack": 1, "search": "ВВГнг-LS 3x6"},
    "cableVVG_10":      {"url": "https://www.el.ru/catalogue/cable/13/647/", "pack": 1, "search": "ВВГнг-LS 3x10"},
    "cableOutdoor_2_5": {"url": "https://www.el.ru/catalogue/cable/13/644/", "pack": 1, "search": "ВВГнг-LS 3x2.5 уличн."},
    "cableOutdoor_4":   {"url": "https://www.el.ru/catalogue/cable/13/645/", "pack": 1, "search": "ВВГнг-LS 3x4 уличн."},
    "automat":          {"url": "https://www.el.ru/catalogue/protection-devices/75/491/", "pack": 1, "search": "Schneider Easy9 1P 16"},
    "uzo":              {"url": "https://www.el.ru/catalogue/protection-devices/196/2576/", "pack": 1, "search": "City9 2P 30мА"},
    "junctionBox":      {"url": "https://www.el.ru/catalogue/cable-systems/35/2304/", "pack": 1, "search": "Промрукав IP66"},
    "conduit":          {"url": "https://www.el.ru/catalogue/cable-systems/47/1940/", "pack": 1, "search": "гофра"},
    "cableClip":        {"url": "https://www.el.ru/catalogue/cable-systems/47/1940/", "pack": 0.01, "search": "площадка Промрукав"},
    "cableTie":         {"url": "https://www.el.ru/catalogue/cable-systems/47/862/", "pack": 0.01, "search": "хомут Fortisflex"},
    "lug":              {"url": "https://www.el.ru/catalogue/cable-systems/16/1386/", "pack": 1, "search": "КВТ ГМЛ 6-4"},
    "heatShrink":       {"url": "https://www.el.ru/catalogue/cable-systems/14/959/", "pack": 1, "search": "Rexant 9/3"},
    "voltageRelay":     {"url": "https://www.el.ru/catalogue/control-systems/25/872/", "pack": 1, "search": "Welrok D2 63"},
    "crossModule":      {"url": "https://www.el.ru/catalogue/switchboards/38/198/", "pack": 1, "search": "IEK 4x7"},
    "panel":            {"url": "https://www.el.ru/catalogue/switchboards/38/190/", "pack": 1, "search": "щит DIN"},
}


def load_urls() -> dict:
    if URLS_FILE.exists():
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return PRODUCTS_DEFAULT


def load_cached_prices() -> dict:
    if PRICES_FILE.exists():
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cached_prices(data: dict):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_prices_from_html(html: str) -> list[float]:
    prices = []
    # JSON-LD schema.org
    for m in re.findall(r'"price"\s*:\s*"?(\d+\.?\d*)', html):
        p = float(m)
        if p > 0:
            prices.append(p)
    # itemprop
    for m in re.findall(r'itemprop="price"\s+content="(\d+\.?\d*)"', html):
        prices.append(float(m))
    # data-price
    for m in re.findall(r'data-price="(\d+\.?\d*)"', html):
        prices.append(float(m))
    # Числа с ₽
    for m in re.findall(r'(\d[\d\s]*[,.]?\d*)\s*₽', html):
        cleaned = re.sub(r'[^\d,.]', '', m.replace(' ', '')).replace(',', '.')
        try:
            p = float(cleaned)
            if 5 < p < 200000:
                prices.append(p)
        except ValueError:
            pass
    return prices


def check_prices() -> dict:
    products = load_urls()
    old_prices = load_cached_prices()
    new_prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }

    for key, info in products.items():
        url = info["url"]
        pack = info["pack"]
        search_term = info.get("search", "")
        print(f"  {key}: ", end="", flush=True)

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}", end=" ")
                if key in old_prices:
                    new_prices[key] = old_prices[key]
                    print(f"(оставляем {old_prices[key]})")
                continue

            html = resp.text
            all_prices = extract_prices_from_html(html)

            if all_prices:
                # Берём медиану (среднее от 2-го и предпоследнего)
                all_prices.sort()
                if len(all_prices) >= 2:
                    raw = (all_prices[len(all_prices)//2] + all_prices[len(all_prices)//2 - 1]) / 2
                else:
                    raw = all_prices[0]

                unit_price = round(raw * pack, 2) if pack < 1 else raw
                new_prices[key] = unit_price
                print(f"{unit_price} руб (найдено {len(all_prices)} цен)")
            else:
                print("цены не найдены", end=" ")
                if key in old_prices:
                    new_prices[key] = old_prices[key]
                    print(f"(оставляем {old_prices[key]})")
                else:
                    print("(нет старой цены!)")

            time.sleep(1)

        except Exception as e:
            print(f"ошибка: {e}", end=" ")
            if key in old_prices:
                new_prices[key] = old_prices[key]
                print(f"(оставляем {old_prices[key]})")

    return new_prices


def update_calculator_files(old_prices: dict, new_prices: dict, apply: bool) -> list[str]:
    changes = []
    files = [BASE_DIR / "calculator.html", BASE_DIR / "calculator-house.html"]

    for key, new_price in new_prices.items():
        old_price = old_prices.get(key)
        if old_price is not None and old_price != new_price:
            changes.append(f"{key}: {old_price} -> {new_price}")

    if not changes or not apply:
        return changes

    for fpath in files:
        if not fpath.exists():
            continue
        content = fpath.read_text(encoding="utf-8")
        for key, new_price in new_prices.items():
            old_price = old_prices.get(key)
            if old_price is not None and old_price != new_price:
                content = re.sub(
                    rf'({re.escape(key)}\s*:\s*)(\d+\.?\d*)',
                    rf'\g<1>{new_price}',
                    content
                )
        fpath.write_text(content, encoding="utf-8")

    return changes


def log_check(changes, new_prices):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n[{now}] Проверка цен\n")
        for c in (changes or []):
            f.write(f"  {c}\n")
        if not changes:
            f.write("  Изменений нет\n")
        f.write(f"  Цены: {json.dumps(new_prices, ensure_ascii=False)}\n")


def main():
    apply_mode = "--apply" in sys.argv

    print(f"{'='*60}")
    print(f"Проверка цен — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"Режим: {'обновление' if apply_mode else 'только проверка'}")
    print(f"{'='*60}")

    new_prices = check_prices()

    print(f"\n{'='*60}")
    old_prices = load_cached_prices()
    changes = update_calculator_files(old_prices, new_prices, apply_mode)
    if changes:
        print("ИЗМЕНЕНИЯ:")
        for c in changes:
            print(f"  {c}")
    else:
        print("Изменений нет")

    save_cached_prices(new_prices)
    log_check(changes, new_prices)
    print(f"Кэш: {PRICES_FILE}")
    print(f"Лог: {LOG_FILE}")


if __name__ == "__main__":
    main()
