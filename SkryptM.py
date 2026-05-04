import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import random
import re
from statistics import mean

# ================= KONFIGURACJA =================
WEBHOOK_URL = "https://discord.com/api/webhooks/1481322987134259391/4mUkMqKjbjGnssS-gkBYPmwld96Rw1GL2HpSTI7Bp2edVedUA09oaV7l7Sl-nXplUjTq"
OLX_SEARCH_URL = "https://www.olx.pl/elektronika/komputery/laptopy/apple/q-macbook/?search%5Border%5D=created_at%3Adesc"
# ================================================

# ========= SUROWE DANE CENOWE (TWÓJ TEKST) =======

RAW_PRICE_TABLE = """
AIR
A1932 I5 8GB/256GB 1100/900/850/1000/
A1932 I5 8GB/128GB 800/1000/600/1000/850=
A2179 I3 8GB/512GB 1200-
A2179 I3 8GB/256GB 1100/900/1100/850/1000/950*
A2179 I5 16GB/256 1450/1600-
A2179 I5 8GB/512GB 1250/1750/1400
A2179 I5 16GB/512GB 1600/1850/1600
A2337 M1 16GB/512GB 2300/2200/2300/2400/2400=
A2337 M1 8GB/256GB 1640/2000/1800/2000/1700/1900/2100/1850*
A2337 M1 16GB/256GB 2000/2200/2300 
A2337 M1 16GB/1TB 2400-

PRO
A1706 I5 8GB/512GB 1100/900/1250/1000
A1706 I5 8GB/256GB 900/700/900/1000
A1706 I5 16GB/512GB 1200/1000/900/1200/1250/1250/1300/1205/990*
A1706 I7 16GB/1TB 1400/1500-
A1708 I5 8GB/256GB 700/1000/900/850/800/1000/750/900*
A1708 I5 8GB/128GB 1000/800/720/789/800
A1708 I7 16GB/512GB 1200/1300/1400/1300/1350/1000/1200*
A1708 I5 8GB/512GB 1100/900-
A1708 I5 16GB/256GB 800-
A1708 I5 16GB/512GB 1200/1000-1
A1708 I7 16GB/1TB 1500-
A1989 I7 16GB/512GB 1600/1620/1690/1500
A1989 I7 16GB/256GB 1400/1400/1300/1300
A1989 I5 16GB/256GB 1200/1350/1250/1500/1500/1400/1400*
A1989 I5 16GB/512GB 1300/1450/1500
A1989 I5 8GB/256GB 1200/-
A1989 I5 8GB/512GB 1300/-
A1989 I7 16GB/1TB 1800/1900-
A2159 I5 8GB/256GB 1300/1350-
A2159 I5 16GB/128GB 1300/1300/1290
A2159 I5 16GB/256GB 1400/1350/1450/1450
A2159 I5 16GB/512GB 1500 -
A2159 I7 16GB/256GB 1720 -
A2159 I5 8GB/128GB 1200 -
A2289 I5 8GB/256GB 1200/1600/1250/1500
A2289 I5 16GB/256GB 1600/1300/1500/1600
A2251 I5  16GB/512GB 1600/1550/1650/1700/1500/1600/1600/1700/1500/1489*
A2251 I7 16GB/512GB 1600/1550/1650/1750/1600/1900/1690/1789/1682/1800*
A2338 M1/16GB/1TB 2799/2400-
A2338 M1 8GB/512GB 2500/2150/1900/2300
A2338 M1 16GB/256GB 2100/2390/2450/2320/2200/2200/2400*
A2338 M1 16GB/512GB 2500/2600/2600/2700/2750/2500/2700/2750/2800*
A2338 M1 8GB/256GB 2000/2200-
A2338 M2 8GB/256GB 2950/2700-
A2338 M2 8GB/512GB 2750 -
A2338 M2 16GB/256GB 3000 -
"""

RAW_SCREENS = """
MATRYCE
A1932 400/400
A2179 300/679/600
A2337 1000/1200/1200/1400
A1706/A1708 600/600/700
A1989/A2159/A2289/A2251 700/700/700/1200/1100
A2338 1200/1200/1100/1600/1400
"""

RAW_BOARDS = """
PŁYTE GŁOWNE 
A1932 190/379/620/700
A2179 799/700/850
A2179 I5 8G/512GB 849
A2179 I3 8GB/256GB 800/700
A2337 M1 8GB/256GB 689/900/900/1000
A2337 M1 700/900/1000
A1706 400/500/450
A1708 600/700/650/500/600
A1989 700/500/433/420
A2159 720/720/800/750
A2289 900
A2251 1200
A2338 1400
"""
# ================================================

def get_pl_time():
    return datetime.now().strftime("%H:%M:%S")


# =============== PARSOWANIE TABELI CEN ===============

def _extract_numbers(part: str):
    nums = []
    for token in re.split(r"[ /]", part):
        token = token.strip()
        token = token.rstrip("=*")
        if not token:
            continue
        if token.isdigit():
            nums.append(int(token))
    return nums


def build_average_price_dict():
    average_per_config = {}
    model_to_all_prices = {}

    for line in RAW_PRICE_TABLE.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper() in ("AIR", "PRO"):
            continue

        parts = line.split()
        split_idx = None
        for i, p in enumerate(parts):
            if any(ch.isdigit() for ch in p) and "/" in p:
                split_idx = i
                break
        if split_idx is None:
            continue

        config_key = " ".join(parts[:split_idx])
        prices_part = " ".join(parts[split_idx:])

        nums = _extract_numbers(prices_part)
        if not nums:
            continue

        avg_conf = round(mean(nums))
        average_per_config[config_key] = avg_conf

        m = re.search(r"A\d{4}", config_key.upper())
        if m:
            model = m.group(0)
            model_to_all_prices.setdefault(model, []).extend(nums)

    average_per_model = {
        model: round(mean(nums)) for model, nums in model_to_all_prices.items()
    }

    return average_per_config, average_per_model, model_to_all_prices


def build_component_price_dict(raw_block: str):
    avg_result = {}
    lists_result = {}

    for line in raw_block.splitlines():
        line = line.strip()
        if not line or "MATRYCE" in line.upper() or "PŁYTE" in line.upper():
            continue

        parts = line.split()
        if len(parts) < 2:
            continue
        models_part = parts[0]
        prices_part = " ".join(parts[1:])
        nums = _extract_numbers(prices_part)
        if not nums:
            continue

        for model in models_part.split("/"):
            model = model.strip().upper()
            if re.match(r"A\d{4}", model):
                lists_result.setdefault(model, []).extend(nums)

    for model, nums in lists_result.items():
        avg_result[model] = round(mean(nums))

    return avg_result, lists_result


AVERAGE_PER_CONFIG, AVERAGE_PER_MODEL, MODEL_ALL_PRICES = build_average_price_dict()
SCREEN_AVG, SCREEN_PRICE_LISTS = build_component_price_dict(RAW_SCREENS)
BOARD_AVG, BOARD_PRICE_LISTS = build_component_price_dict(RAW_BOARDS)


# =============== WYKRYWANIE USZKODZEŃ =================

SCREEN_DAMAGE_PHRASES = [
    "duszki",
    "duszek",
    "zalana matryca",
    "zalany ekran",
    "zalany wyświetlacz",
    "zalany wyswietlacz",
    "uszkodzona matryca",
    "uszkodzony ekran",
    "uszkodzony wyswietlacz",
    "peknięta matryca",
    "peknieta matryca",
    "peknięty ekran",
    "pekniety ekran",
    "peknięty wyswietlacz",
    "pekniety wyswietlacz",
    "linie na ekranie",
    "linie na matrycy",
    "pasy na ekranie",
    "pasy na matrycy",
    "plamy na matrycy",
    "plamy na ekranie",
    "plama na ekranie",
    "plama na matrycy",
    "martwe piksele",
    "martwy piksel",
    "bad pixel",
]

BOARD_DAMAGE_PHRASES = [
    "zablokowany",
    "blokada icloud",
    "konto icloud",
    "zwarcie",
    "zwarcia",
    "zepsuta płyta",
    "zepsuta plyta",
    "spalona płyta",
    "spalona plyta",
    "spalony układ",
    "spalony uklad",
    "uszkodzona płyta główna",
    "uszkodzona plyta glowna",
    "uszkodzona plyta",
    "nie włącza się",
    "nie wlacza sie",
    "nie uruchamia się",
    "nie uruchamia sie",
    "nie startuje",
    "martwa płyta",
    "martwa plyta",
    "brak obrazu po włączeniu",
    "brak reakcji na przycisk",
    "brak reakcji na zasilacz",
    "ciągłe restarty",
    "ciagle restarty",
]


def normalize_text(text: str) -> str:
    text = text.lower()
    replacements = {
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ź": "z",
        "ż": "z",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def analyze_damage(full_text: str):
    if not full_text:
        return {
            "screen_damage": False,
            "board_damage": False,
            "matched_screen_phrases": [],
            "matched_board_phrases": [],
        }

    norm = normalize_text(full_text)

    matched_screen = [p for p in SCREEN_DAMAGE_PHRASES if normalize_text(p) in norm]
    matched_board = [p for p in BOARD_DAMAGE_PHRASES if normalize_text(p) in norm]

    return {
        "screen_damage": len(matched_screen) > 0,
        "board_damage": len(matched_board) > 0,
        "matched_screen_phrases": matched_screen,
        "matched_board_phrases": matched_board,
    }


# =============== MODELE / ROCZNIKI =================

def detect_model_from_text(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"A\d{4}", text.upper())
    if m:
        return m.group(0)
    return None


def detect_full_config_key(text: str) -> str | None:
    if not text:
        return None

    title_norm = text.upper().replace(",", " ")
    title_norm = re.sub(r"\s+", " ", title_norm)

    possible_keys = list(AVERAGE_PER_CONFIG.keys())
    best_key = None
    best_score = 0

    for key in possible_keys:
        key_norm = key.upper()
        score = 0

        m = re.search(r"A\d{4}", key_norm)
        if not m:
            continue
        model = m.group(0)
        if model not in title_norm:
            continue

        fragments = re.split(r"\s+", key_norm)
        for frag in fragments:
            frag = frag.strip()
            if not frag or frag == model:
                continue
            if frag in title_norm:
                score += 1

        if score > best_score:
            best_score = score
            best_key = key

    if best_score >= 2:
        return best_key
    return None


YEAR_GROUPS = {
    "2017": ["A1706", "A1708"],
    "2018": ["A1932", "A1989"],
    "2019": ["A2159", "A1989"],
    "2020_INTEL": ["A2289", "A2251"],
    "2020_M1": ["A2338"],
}


def detect_year_group(text: str) -> list[str] | None:
    if not text:
        return None
    t = text
    if "2017" in t:
        return YEAR_GROUPS["2017"]
    if "2018" in t:
        return YEAR_GROUPS["2018"]
    if "2019" in t:
        return YEAR_GROUPS["2019"]
    if "2020" in t:
        if "M1" in t.upper():
            return YEAR_GROUPS["2020_M1"]
        else:
            return YEAR_GROUPS["2020_INTEL"]
    if "M1" in t.upper():
        return YEAR_GROUPS["2020_M1"]
    return None


def compute_valuation(model_code: str | None,
                      config_key: str | None,
                      screen_damage: bool,
                      board_damage: bool,
                      full_text_for_matching: str):
    """
    Model hybrydowy:
    - przy uszkodzeniach: pełna logika (matryca/płyta),
    - przy braku uszkodzeń: jeśli mamy średnią z modelu/rocznika -> zwróć samą średnią.
    """
    if model_code == "A1707":
        group_models = ["A1706", "A1708"]
    else:
        group_models = None
        if not model_code:
            group_models = detect_year_group(full_text_for_matching)
        if model_code and model_code not in MODEL_ALL_PRICES:
            maybe_group = detect_year_group(full_text_for_matching)
            if maybe_group:
                group_models = maybe_group

    avg = None
    group_used = None

    if config_key and config_key in AVERAGE_PER_CONFIG:
        avg = AVERAGE_PER_CONFIG[config_key]

    if avg is None and model_code and model_code in AVERAGE_PER_MODEL:
        avg = AVERAGE_PER_MODEL[model_code]

    if avg is None and group_models:
        all_prices = []
        for m in group_models:
            if m in MODEL_ALL_PRICES:
                all_prices.extend(MODEL_ALL_PRICES[m])
        if all_prices:
            avg = round(mean(all_prices))
            group_used = group_models

    def get_component_avg(component_avg_dict, component_lists_dict):
        if model_code and model_code in component_avg_dict:
            return component_avg_dict[model_code], [model_code]
        if group_models:
            nums = []
            used = []
            for m in group_models:
                if m in component_lists_dict:
                    nums.extend(component_lists_dict[m])
                    used.append(m)
            if nums:
                return round(mean(nums)), used
        return None, []

    screen_price, _ = get_component_avg(SCREEN_AVG, SCREEN_PRICE_LISTS)
    board_price, _ = get_component_avg(BOARD_AVG, BOARD_PRICE_LISTS)

    # Brak średniej przy uszkodzeniach
    if avg is None and (screen_damage or board_damage):
        return {
            "has_valuation": False,
            "reason": "Brak średniej ceny rynkowej dla tej konfiguracji/modelu/rocznika.",
        }

    # Uszkodzona tylko matryca
    if screen_damage and not board_damage:
        if screen_price is None or board_price is None or avg is None:
            return {
                "has_valuation": False,
                "reason": "Brak pełnych danych cenowych (matryca/płyta/średnia) dla tej konfiguracji.",
            }
        wartosc_laptopa = avg
        koszt_naprawy = screen_price
        wartosc_odzysku = board_price + int(round(0.15 * avg))

        info = []
        if config_key:
            info.append(f"konfiguracja: {config_key}")
        if model_code:
            info.append(f"model: {model_code}")
        if group_used:
            info.append(f"użyto grupy rocznika: {', '.join(group_used)}")

        return {
            "has_valuation": True,
            "type": "screen_only",
            "model_code": model_code,
            "config_key": config_key,
            "group_used": group_used,
            "wartosc_laptopa": wartosc_laptopa,
            "koszt_naprawy": koszt_naprawy,
            "wartosc_odzysku": wartosc_odzysku,
            "meta": "; ".join(info) if info else "",
        }

    # Uszkodzona tylko płyta
    if board_damage and not screen_damage:
        if board_price is None or screen_price is None:
            return {
                "has_valuation": False,
                "reason": "Brak danych cenowych (matryca/płyta) dla tej konfiguracji.",
            }

        koszt_naprawy = board_price
        wartosc_odzysku = screen_price

        info = []
        if config_key:
            info.append(f"konfiguracja: {config_key}")
        if model_code:
            info.append(f"model: {model_code}")
        if group_used:
            info.append(f"użyto grupy rocznika: {', '.join(group_used)}")

        return {
            "has_valuation": True,
            "type": "board_only",
            "model_code": model_code,
            "config_key": config_key,
            "group_used": group_used,
            "wartosc_laptopa": avg,
            "koszt_naprawy": koszt_naprawy,
            "wartosc_odzysku": wartosc_odzysku,
            "meta": "; ".join(info) if info else "",
        }

    # Obie rzeczy uszkodzone
    if screen_damage and board_damage:
        return {
            "has_valuation": False,
            "reason": "Uszkodzona i matryca, i płyta – wycena złożona, potraktuj indywidualnie.",
        }

    # Brak uszkodzeń – ale jeśli znamy średnią, pokaż ją jako informację
    if avg is not None:
        info = []
        if config_key:
            info.append(f"konfiguracja: {config_key}")
        if model_code:
            info.append(f"model: {model_code}")
        if group_used:
            info.append(f"użyto grupy rocznika: {', '.join(group_used)}")

        return {
            "has_valuation": True,
            "type": "no_damage",
            "model_code": model_code,
            "config_key": config_key,
            "group_used": group_used,
            "wartosc_laptopa": avg,
            "koszt_naprawy": None,
            "wartosc_odzysku": None,
            "meta": "; ".join(info) if info else "",
        }

    # Nic nie znaleziono
    return {
        "has_valuation": False,
        "reason": "Brak wykrytych uszkodzeń i brak średniej ceny.",
    }


# =============== DISCORD =================

def send_to_discord(title, price, link, olx_date, img_url,
                    description_snippet: str | None,
                    damage_info: dict,
                    valuation: dict):
    fields = [
        {"name": "💰 Cena", "value": price or "Brak ceny", "inline": True},
        {"name": "🕒 Czas na OLX", "value": olx_date or "brak danych", "inline": True},
    ]

    if description_snippet:
        fields.append({
            "name": "📄 Opis (fragment)",
            "value": description_snippet[:200] + ("..." if len(description_snippet) > 200 else "")
        })

    screen_damage = damage_info.get("screen_damage", False)
    board_damage = damage_info.get("board_damage", False)

    if screen_damage or board_damage:
        status_parts = []
        if screen_damage:
            status_parts.append("matryca")
        if board_damage:
            status_parts.append("płyta główna")
        status_text = ", ".join(status_parts)
    else:
        status_text = "brak wykrytych uszkodzeń (po słowach kluczowych)"

    fields.append({
        "name": "🛠 Stan (analiza opisu)",
        "value": status_text
    })

    if valuation.get("has_valuation"):
        if valuation["type"] == "screen_only":
            val_text = (
                f"📊 Średnia cena rynkowa: **{valuation['wartosc_laptopa']} zł**\n"
                f"🔧 Koszt naprawy (matryca): **{valuation['koszt_naprawy']} zł**\n"
                f"♻️ Wartość odzysku części: **{valuation['wartosc_odzysku']} zł**"
            )
        elif valuation["type"] == "board_only":
            srednia_txt = (
                f"📊 Średnia cena rynkowa: **{valuation['wartosc_laptopa']} zł**\n"
                if valuation.get("wartosc_laptopa") is not None else ""
            )
            val_text = (
                f"{srednia_txt}"
                f"🔧 Koszt naprawy (płyta): **{valuation['koszt_naprawy']} zł**\n"
                f"♻️ Wartość odzysku części (matryca): **{valuation['wartosc_odzysku']} zł**"
            )
        elif valuation["type"] == "no_damage":
            meta = valuation.get("meta", "")
            meta_txt = f"\n_{meta}_" if meta else ""
            val_text = (
                f"📊 Szacowana średnia cena rynkowa: **{valuation['wartosc_laptopa']} zł**"
                f"{meta_txt}\n"
                f"(brak wykrytych uszkodzeń w opisie)"
            )
        else:
            val_text = valuation.get("reason", "Brak wyceny.")
    else:
        val_text = valuation.get("reason", "Brak wyceny.")

    fields.append({
        "name": "💱 Wycena",
        "value": val_text
    })

    embed = {
        "title": title,
        "url": link,
        "color": 0x00FF00,
        "fields": fields,
        "footer": {"text": f"Złapano o: {get_pl_time()}"},
    }
    if img_url:
        embed["thumbnail"] = {"url": img_url}

    data = {"embeds": [embed]}
    requests.post(WEBHOOK_URL, json=data)


# =============== POBIERANIE OFERT =================

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
})

seen_offers = set()


def get_offers():
    try:
        resp = session.get(OLX_SEARCH_URL, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            offers = soup.find_all('div', attrs={'data-cy': 'l-card'})
            return offers
        else:
            print(f"[{get_pl_time()}] ⚠️ OLX zwrócił błąd: {resp.status_code}")
    except Exception as e:
        print(f"[{get_pl_time()}] ⚠️ Błąd połączenia: {e}")
    return []


def fetch_offer_description(offer_url: str) -> str | None:
    if not offer_url:
        return None
    try:
        resp = session.get(offer_url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        desc_div = soup.find('div', attrs={'data-cy': 'ad_description'})
        if not desc_div:
            desc_div = soup.find('div', class_='css-g5mtbi-Text')
        if not desc_div:
            return None
        text = desc_div.get_text(" ", strip=True)
        return text if text else None
    except Exception as e:
        print(f"[{get_pl_time()}] ⚠️ Błąd pobierania opisu: {e}")
        return None


# =============== GŁÓWNA PĘTLA =================

def main():
    print(f"[{get_pl_time()}] 🚀 Uruchamiam monitor OLX z analizą uszkodzeń i wyceną...")

    initial_offers = get_offers()
    if not initial_offers:
        print("❌ BŁĄD: Nie znaleziono żadnych ofert na start. Sprawdź link!")
        return

    for offer in initial_offers:
        o_id = offer.get('id')
        if o_id:
            seen_offers.add(o_id)

    print(f"[{get_pl_time()}] ✅ Zapisano {len(seen_offers)} początkowych ofert. Monitoruję na żywo...")

    while True:
        sleep_time = random.uniform(25.0, 35.0)
        time.sleep(sleep_time)

        current_offers = get_offers()
        found_new = False

        for offer in current_offers:
            o_id = offer.get('id')
            if not o_id or o_id in seen_offers:
                continue

            date_elem = offer.find('p', attrs={'data-testid': 'location-date'})
            date_text = date_elem.get_text().lower() if date_elem else ""

            if "dzisiaj" not in date_text and "minut" not in date_text:
                seen_offers.add(o_id)
                continue

            try:
                title = "Brak tytułu"
                t_tag = offer.find(['h6', 'h3'])
                if t_tag:
                    title = t_tag.get_text(strip=True)
                else:
                    img_tag = offer.find('img')
                    if img_tag and img_tag.get('alt'):
                        title = img_tag.get('alt')

                p_tag = offer.find('p', attrs={'data-testid': 'ad-price'})
                price = p_tag.get_text(strip=True) if p_tag else "Brak ceny"

                link_tag = offer.find('a')
                link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ""
                if link.startswith('/'):
                    link = "https://www.olx.pl" + link

                img_tag = offer.find('img')
                img_url = img_tag.get('src') if img_tag and img_tag.get('src') else ""

                description = fetch_offer_description(link)
                description_snippet = description if description else None

                full_text_for_analysis = (title or "") + " " + (description or "")

                damage_info = analyze_damage(full_text_for_analysis)

                model_code = detect_model_from_text(full_text_for_analysis)
                config_key = detect_full_config_key(full_text_for_analysis)

                valuation = compute_valuation(
                    model_code=model_code,
                    config_key=config_key,
                    screen_damage=damage_info["screen_damage"],
                    board_damage=damage_info["board_damage"],
                    full_text_for_matching=full_text_for_analysis,
                )

                send_to_discord(
                    title=title,
                    price=price,
                    link=link,
                    olx_date=date_text,
                    img_url=img_url,
                    description_snippet=description_snippet,
                    damage_info=damage_info,
                    valuation=valuation,
                )

                print(f"[{get_pl_time()}] 🔥 STRZAŁ! {title} (model: {model_code}, config: {config_key}, screen={damage_info['screen_damage']}, board={damage_info['board_damage']})")

                seen_offers.add(o_id)
                found_new = True

            except Exception as e:
                print(f"[{get_pl_time()}] ⚠️ Błąd przy przetwarzaniu oferty: {e}")
                continue

        if not found_new:
            print(f"[{get_pl_time()}] Czuwam... (następny skan za {int(sleep_time)}s)")


if __name__ == "__main__":
    main()