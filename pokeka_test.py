import requests
import json
from bs4 import BeautifulSoup
import os
# ポケモンのタイプ対応表
type_dict = {
    "icon-none": "無色",
    "icon-fighting": "闘",
    "icon-grass": "草",
    "icon-fire": "炎",
    "icon-water": "水",
    "icon-electric": "雷",
    "icon-psychic": "超",
    "icon-dragon": "ドラゴン",
    "icon-steel": "鋼",
    "icon-dark": "悪"
}

#同じカードのidを記録する
def find_same_card(pokemon_data_list,flag):
    for i, card_i in enumerate(pokemon_data_list):
        for j, card_j in enumerate(pokemon_data_list):
            if i != j:
                if(flag):
                    if (
                        card_i["カード名"] == card_j["カード名"] and
                        card_i["ポケモンのタイプ"] == card_j["ポケモンのタイプ"] and
                        card_i["HP"] == card_j["HP"]
                    ):
                        # ワザ名が一致するか確認
                        attacks_i = set(attack["名前"] for attack in card_i["ワザ"])
                        attacks_j = set(attack["名前"] for attack in card_j["ワザ"])
                        if attacks_i == attacks_j:
                            # 同じカードのidを追加
                            if "同じカードid" not in card_i:
                                card_i["同じカードid"] = []  # 初期化
                            card_i["同じカードid"].append(card_j["id"])
                else:
                    # ポケモンでないカードの場合
                    if card_i["カテゴリ"] != "ポケモン" and card_i["カード名"] == card_j["カード名"]:
                        if "同じカードid" not in card_i:
                            card_i["同じカードid"] = []  # 初期化
                        card_i["同じカードid"].append(card_j["id"])


def add_evolution_chain_ids(pokemon_data_list):
    for i, card_i in enumerate(pokemon_data_list):
        for j, card_j in enumerate(pokemon_data_list):
            if i != j:
                if (card_j["カード名"] in card_i["進化"]):
                        # 進化系統カードのidを追加
                        if "進化系統カードid" not in card_i:
                            card_i["進化系統カードid"] = []  # 初期化
                        card_i["進化系統カードid"].append(card_j["id"])


# ポケモンのタイプを取得する関数
def get_pokemon_type(detail_soup):
    """
    ポケモンの詳細ページからタイプを取得する。
    """
    hp_type_element = detail_soup.find("span", class_="hp-type")
    if hp_type_element:
        type_icon = hp_type_element.find_next("span", class_="icon")
        if type_icon:
            for class_name in type_icon["class"]:
                if class_name in type_dict:
                    return type_dict[class_name]
    return "なし"


# ポケモンの特性を取得する関数
def get_abilities(detail_soup):
    """
    ポケモンの詳細ページから特性を取得する。
    """
    abilities = []
    ability_header = detail_soup.find("h2", class_="mt20", string="特性")
    if ability_header:
        ability_name_tag = ability_header.find_next("h4")
        ability_effect_tag = ability_name_tag.find_next("p") if ability_name_tag else None
        if ability_name_tag and ability_effect_tag:
            abilities.append({
                "名前": ability_name_tag.text.strip(),
                "効果": ability_effect_tag.text.strip()
            })
    return abilities


# ポケモンの技を取得する関数
def get_attacks(detail_soup):
    """
    ポケモンの詳細ページから技を取得する。
    """
    attacks = []
    for h4 in detail_soup.find_all("h4"):
        if h4.find("span", class_="icon"):
            attack_name = h4.get_text(strip=True)
            if not attack_name:
                attack_name = "不明"
            attack_types = []
            for icon in h4.find_all("span", class_="icon"):
                for class_name in icon["class"]:
                    if class_name in type_dict:
                        attack_types.append(type_dict[class_name])
            attack_damage_tag = h4.find("span", class_="f_right")
            attack_damage = attack_damage_tag.text.strip() if attack_damage_tag else "なし"
            attack_effect_tag = h4.find_next_sibling("p")
            attack_effect = attack_effect_tag.text.strip() if attack_effect_tag else "なし"
            attacks.append({
                "名前": attack_name,
                "必要エネルギー": attack_types,
                "ダメージ": attack_damage,
                "効果": attack_effect
            })
    return attacks


# ポケモンの弱点と抵抗を取得する関数
def get_weakness_and_resistance(detail_soup):
    """
    ポケモンの詳細ページから弱点と抵抗を取得する。
    """
    weakness, resistance = "なし", "なし"
    table_row = detail_soup.find("th", string="弱点")
    if table_row:
        row = table_row.find_parent("tr").find_next_sibling("tr")
        if row:
            cells = row.find_all("td")
            if len(cells) >= 2:
                weakness_icon = cells[0].find("span", class_="icon")
                if weakness_icon and "×2" in cells[0].text:
                    for class_name in weakness_icon["class"]:
                        if class_name in type_dict:
                            weakness = type_dict[class_name]
                resistance_icon = cells[1].find("span", class_="icon")
                if resistance_icon and "－30" in cells[1].text:
                    for class_name in resistance_icon["class"]:
                        if class_name in type_dict:
                            resistance = type_dict[class_name]
    return weakness, resistance


# 逃げるために必要なエネルギー数を取得する関数
def get_escape_energy(detail_soup):
    """
    ポケモンの詳細ページから逃げるために必要なエネルギー数を取得する。
    """
    escape_cell = detail_soup.find("th", string="にげる")
    if escape_cell:
        energy_icons = escape_cell.find_next("td", class_="escape").find_all("span", class_="icon")
        return len(energy_icons)
    return 0


# 収録パック名を取得する関数
def get_pack_name(detail_soup):
    """
    ポケモンの詳細ページから収録パック名を取得する。
    """
    section = detail_soup.find("section", class_="SubSection")
    if section:
        pack_link = section.find("a", class_="Link Link-arrow")
        if pack_link:
            return pack_link.text.strip()
    return "不明"


# カードの詳細情報を取得する関数
def get_card_details(card_id, headers):
    """
    カード詳細ページ取得。403 が返ったら例外を投げる。
    """
    detail_url = f"https://www.pokemon-card.com/card-search/details.php/card/{card_id}/"
    resp = requests.get(detail_url, headers=headers)
    if resp.status_code == 403:
        raise RuntimeError(f"カード詳細取得で403エラー: card_id={card_id}")
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# ポケモンカードかどうかを判定する関数
def is_pokemon_card(category_text):
    """
    カテゴリーテキストがポケモンカードであるかどうかを判定する。
    """
    # ポケモン以外のカテゴリリスト
    non_pokemon_categories = {"グッズ", "サポート", "スタジアム", "特殊エネルギー", "ポケモンのどうぐ"}
    return category_text not in non_pokemon_categories


# 非ポケモンカード情報を取得する関数
def get_non_pokemon_card_info(detail_soup, card_id, category_text, image_url, regulation, card_number, illustrator, pack_name, card_rarity):
    """
    非ポケモンカードの詳細情報を取得する。
    """
    effects = [p.text.strip() for p in detail_soup.find_all("p") if p.text.strip()]
    del effects[-1]
    del effects[-1]
    return {
        "id": card_id,
        "カード名": detail_soup.find("h1", class_="Heading1").text.strip(),
        "カテゴリ": category_text,
        "画像": image_url,
        "レギュレーション": regulation,
        "カード番号": card_number,
        "レアリティ": card_rarity,
        "イラストレーター": illustrator,
        "効果": effects,
        "収録パック": pack_name
    }


# ポケモンカード情報を取得する関数
def get_pokemon_card_info(detail_soup, card_id, pack_name, image_url, regulation, card_number, illustrator, card_rarity):
    """
    ポケモンカードの詳細情報を取得する。
    """
    pokemons_rule = "ex" if "ex" in detail_soup.find("h1", class_="Heading1").text else None
    card_type = detail_soup.find("span", class_="type").text.strip()
    hp = detail_soup.find("span", class_="hp-num").text.strip()
    pokemon_type = get_pokemon_type(detail_soup)
    weakness_type, resistance_type = get_weakness_and_resistance(detail_soup)
    escape_energy = get_escape_energy(detail_soup)
    evolution = [a.text.strip() for a in detail_soup.find_all("a", href=lambda x: x and "pokemon=" in x)]
    abilities = get_abilities(detail_soup)
    attacks = get_attacks(detail_soup)

    return {
        "id": card_id,
        "カード名": detail_soup.find("h1", class_="Heading1").text.strip(),
        "カテゴリ": "ポケモン",
        "HP": hp,
        "特別なルール": pokemons_rule,
        "画像": image_url,
        "レギュレーション": regulation,
        "カード番号": card_number,
        "レアリティ": card_rarity,
        "イラストレーター": illustrator,
        "ポケモンのタイプ": pokemon_type,
        "特性": abilities,
        "ワザ": attacks,
        "弱点": weakness_type,
        "抵抗": resistance_type,
        "逃げるために必要なエネルギー": escape_energy,
        "進化": evolution,
        "収録パック": pack_name
    }




def load_existing_ids():
    """
    pokemon_cards.json / non_pokemon_cards.json の中から
    実際に取得されたカードの ID を全部セットで返す。
    """
    ids = set()

    for path in ["pokemon_cards.json", "non_pokemon_cards.json"]:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "cards" in data:
            cards = data["cards"]
        elif isinstance(data, list):
            cards = data
        else:
            continue
        ids.update(int(card["id"]) for card in cards if "id" in card)

    return ids


# 既存 JSON から「開始id」を読み込むユーティリティ
def load_last_end_id(path="スクレイピング.json"):
    """
    'スクレイピング.json' から
    ポケモンと非ポケモンの終了idの大きい方を取得する。
    どちらも存在しなければ None を返す。
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pokemon_meta = data.get("pokemon", {})
    non_pokemon_meta = data.get("non_pokemon", {})

    end_id_pokemon = pokemon_meta.get("終了id", None)
    end_id_non_pokemon = non_pokemon_meta.get("終了id", None)

    # どちらか片方しか存在しない場合も考慮
    ids = []
    if end_id_pokemon is not None:
        ids.append(int(end_id_pokemon))
    if end_id_non_pokemon is not None:
        ids.append(int(end_id_non_pokemon))

    if not ids:
        return None

    return max(ids)

def get_basic_energy_info(detail_soup, card_id, image_url, pack_name):
    """
    基本エネルギーカードの情報を取得する（シンプル構成）。
    """
    return {
        "id": card_id,
        "カード名": detail_soup.find("h1", class_="Heading1").text.strip(),
        "画像": image_url,
        "収録パック": pack_name
    }


def update_scraping_json(new_pokemon_cards, new_non_pokemon_cards, path="スクレイピング.json"):
    """
    既存のスクレイピング.jsonを読み込み、
    新しいカードリストとマージして、開始id・終了idを更新する。
    """
    # 既存を読み込む
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        meta = {
            "pokemon": {"開始id": None, "終了id": None},
            "non_pokemon": {"開始id": None, "終了id": None}
        }

    # 現在のメタ情報
    current_pokemon_start = int(meta["pokemon"]["開始id"]) if meta["pokemon"]["開始id"] else None
    current_pokemon_end   = int(meta["pokemon"]["終了id"]) if meta["pokemon"]["終了id"] else None
    current_non_pokemon_start = int(meta["non_pokemon"]["開始id"]) if meta["non_pokemon"]["開始id"] else None
    current_non_pokemon_end   = int(meta["non_pokemon"]["終了id"]) if meta["non_pokemon"]["終了id"] else None

    # 新しいデータから開始id・終了idを取り出す
    if new_pokemon_cards:
        new_pokemon_start = int(new_pokemon_cards[0]["id"])
        new_pokemon_end   = int(new_pokemon_cards[-1]["id"])
    else:
        new_pokemon_start = new_pokemon_end = None

    if new_non_pokemon_cards:
        new_non_pokemon_start = int(new_non_pokemon_cards[0]["id"])
        new_non_pokemon_end   = int(new_non_pokemon_cards[-1]["id"])
    else:
        new_non_pokemon_start = new_non_pokemon_end = None

    # 開始id: 小さい方、終了id: 大きい方を選ぶ
    def merge_start(old, new):
        if old is None:
            return new
        if new is None:
            return old
        return min(old, new)

    def merge_end(old, new):
        if old is None:
            return new
        if new is None:
            return old
        return max(old, new)

    meta["pokemon"]["開始id"] = str(merge_start(current_pokemon_start, new_pokemon_start))
    meta["pokemon"]["終了id"] = str(merge_end(current_pokemon_end, new_pokemon_end))
    meta["non_pokemon"]["開始id"] = str(merge_start(current_non_pokemon_start, new_non_pokemon_start))
    meta["non_pokemon"]["終了id"] = str(merge_end(current_non_pokemon_end, new_non_pokemon_end))

    # 保存
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)

    print("▶ スクレイピング.jsonを更新しました")


# fetch_pokemon_data に threshold 引数を追加
def fetch_pokemon_data(base_url, max_page, headers, pack_flag=False, threshold=None, start_page=1):
    """
    threshold より小さい cardID のみをスクレイピングし、
    start_page から開始。403 エラーで中断。
    """
    exit_loop = False
    pokemon_cards = []
    non_pokemon_cards = []
    basic_energy_cards = []
    special_energy_cards = []
    for page in range(start_page, max_page + 1):
        # ページ取得＋403チェック
        try:
            resp = requests.get(base_url.format(page), headers=headers)
            if resp.status_code == 403:
                print(f"[ERROR] ページ{page}で403エラー。スクレイピングを中断します。")
                break
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"[WARN] ページ{page}の取得失敗 ({e})。次ページへ。")
            continue
        except ValueError as e:
            print(f"[WARN] ページ{page}のJSONパース失敗 ({e})。次ページへ。")
            continue

        card_list = data.get("cardList", [])

        # threshold が設定されていればページ先頭IDで全体中断判定
        if threshold is not None and card_list:
            first_id = int(card_list[0]["cardID"])
            if first_id >= threshold:
                print(f"[INFO] ページ{page}: 全て取得済み (first_id={first_id} >= threshold={threshold}) → 中断")
                break

        for card in card_list:
            cid = int(card["cardID"])
            # すでに取得済みならスキップ
            # threshold チェック
            if threshold is not None and cid >= threshold:
                continue

            # カード詳細取得＋エラー処理
            try:
                detail_soup = get_card_details(cid, headers)
                if not detail_soup:
                    continue
            except RuntimeError as e:
                print(f"[ERROR] {e} → 全体中断")
                exit_loop = True
                break
            except requests.exceptions.RequestException as e:
                print(f"[WARN] card_id={cid}の詳細取得失敗 ({e}) → スキップ")
                continue

            # 共通情報取得
            category_header = detail_soup.find("h2", class_="mt20")
            category_text = category_header.text.strip() if category_header else ""
            image_url = "https://www.pokemon-card.com/" + detail_soup.find("img", class_="fit")["src"]
            #regulation = detail_soup.find("img", class_="img-regulation")["alt"]
            #card_number = detail_soup.find("div", class_="subtext").text.strip().split()[0]
            subtext_div = detail_soup.find("div", class_="subtext")
            if subtext_div:
                text_parts = subtext_div.text.strip().split()
                if text_parts:
                    card_number = text_parts[0]
                else:
                    card_number = "不明"
                    card_name = detail_soup.find("h1", class_="Heading1")
                    print("⚠️ subtextにカード番号が含まれていません")
                    print(f"  ▶ カード名: {card_name.text.strip() if card_name else '不明'}")
                    print(f"  ▶ ページURL: https://www.pokemon-card.com/card-search/details.php/card/{cid}/")
            else:
                card_number = "不明"
                card_name = detail_soup.find("h1", class_="Heading1")
                print("⚠️ <div class='subtext'> が見つかりません")
                print(f"  ▶ カード名: {card_name.text.strip() if card_name else '不明'}")
                print(f"  ▶ ページURL: https://www.pokemon-card.com/card-search/details.php/card/{cid}/")

            illustrator_tag = detail_soup.find("a", href=lambda x: x and "regulation_illust" in x)
            illustrator = illustrator_tag.text.strip() if illustrator_tag else "なし"
            pack_name = get_pack_name(detail_soup)
            rarity_img = detail_soup.find("img", src=lambda x: x and "/assets/images/card/rarity/" in x)
            card_rarity = rarity_img["src"].split("ic_rare_")[-1].split(".")[0] if rarity_img else "なし"

            regulation_img = detail_soup.find("img", class_="img-regulation")
            if regulation_img:
                regulation = regulation_img["alt"]
            else:
                regulation = "なし"
                # どのカードでエラーになるか知るための出力（カテゴリ名・画像URL・ページURL）
                card_name = detail_soup.find("h1", class_="Heading1").text.strip() if detail_soup.find("h1", class_="Heading1") else "不明"
                print("⚠️ <img class='img-regulation'> が見つかりませんでした")
                print(f"  ▶ カード名: {card_name}")
                print(f"  ▶ カテゴリ: {category_text}")
                print(f"  ▶ ページURL: https://www.pokemon-card.com/card-search/details.php/card/{cid}/")


            # Pokémon or Non‑Pokémon で分岐
            if is_pokemon_card(category_text):
                pokemon_cards.append(get_pokemon_card_info(
                    detail_soup, str(cid), pack_name, image_url, regulation, card_number, illustrator, card_rarity
                ))
                print(pokemon_cards[-1]["カード名"])
            elif category_text == "特殊エネルギー":
                effects = [p.text.strip() for p in detail_soup.find_all("p") if p.text.strip()]
                if len(effects) <= 2:  # 説明がないなら「基本」
                    basic_energy_cards.append(get_basic_energy_info(
                        detail_soup, str(cid), image_url, pack_name
                    ))
                    print(f"[基本エネルギー] {basic_energy_cards[-1]['カード名']}")
                else:
                    special_energy_cards.append(get_non_pokemon_card_info(
                        detail_soup, str(cid), category_text, image_url, regulation, card_number, illustrator, pack_name, card_rarity
                    ))
                    print(f"[特殊エネルギー] {special_energy_cards[-1]['カード名']}")
            else:
                non_pokemon_cards.append(get_non_pokemon_card_info(
                    detail_soup, str(cid), category_text, image_url, regulation, card_number, illustrator, pack_name, card_rarity
                ))
                print(non_pokemon_cards[-1]["カード名"])

            # pack_flag が True のときのループ中断ロジック
            if pack_flag and len(pokemon_cards) >= 2:
                current = pokemon_cards[-1]
                previous = pokemon_cards[-2]
                if current["収録パック"] != previous["収録パック"] or current["id"] == previous["id"]:
                    pokemon_cards.pop()
                    print("収録パックが変わった or 同じカードが続く → 中断")
                    exit_loop = True
                    break

        if exit_loop:
            break

    return pokemon_cards, non_pokemon_cards, basic_energy_cards, special_energy_cards


# データをJSONとして保存する関数
def save_to_json(pokemon_cards, non_pokemon_cards, basic_energy_cards, special_energy_cards):
    # ポケモンカード
    with open("pokemon_cards.json", "w", encoding="utf-8") as f:
        json.dump({
            "開始id": pokemon_cards[0]["id"] if pokemon_cards else None,
            "終了id": pokemon_cards[-1]["id"] if pokemon_cards else None,
            "cards": pokemon_cards
        }, f, ensure_ascii=False, indent=4)

    # 非ポケモンカード
    with open("non_pokemon_cards.json", "w", encoding="utf-8") as f:
        json.dump({
            "開始id": non_pokemon_cards[0]["id"] if non_pokemon_cards else None,
            "終了id": non_pokemon_cards[-1]["id"] if non_pokemon_cards else None,
            "cards": non_pokemon_cards
        }, f, ensure_ascii=False, indent=4)

    # 基本エネルギー
    with open("basic_energy_cards.json", "w", encoding="utf-8") as f:
        json.dump({
            "cards": basic_energy_cards
        }, f, ensure_ascii=False, indent=4)

    # 特殊エネルギー
    with open("special_energy_cards.json", "w", encoding="utf-8") as f:
        json.dump({
            "cards": special_energy_cards
        }, f, ensure_ascii=False, indent=4)

    print(f"✅ ポケモン: {len(pokemon_cards)}枚")
    print(f"✅ 非ポケモン: {len(non_pokemon_cards)}枚")
    print(f"✅ 基本エネルギー: {len(basic_energy_cards)}枚")
    print(f"✅ 特殊エネルギー: {len(special_energy_cards)}枚")


def find_resume_page(existing_ids, max_page, base_url, headers):
    """
    既に取得済みのIDセット(existing_ids)に基づき、
    スクレイピング再開すべきページを探索する。
    最終的には low の1ページ前から再確認して確実に未取得ページを探す。
    """
    low, high = 1, max_page
    step = 0
    print(f"✅ 既存IDの例（最大10個）: {sorted(list(existing_ids))[:10]} ...")

    while low <= high:
        mid = (low + high) // 2
        print(f"[STEP {step}] low={low}, high={high}, mid={mid}")
        step += 1

        resp = requests.get(base_url.format(mid), headers=headers)
        resp.raise_for_status()
        data = resp.json()
        card_list = data.get("cardList", [])
        if not card_list:
            print(f"  → ページ{mid}はカードなし。highを{mid-1}に更新")
            high = mid - 1
            continue

        page_card_ids = {int(card["cardID"]) for card in card_list}
        intersection = page_card_ids & existing_ids

        if intersection:
            print(f"  → ページ{mid}に既存ID {sorted(list(intersection))[:5]} ... を検出 → lowを{mid+1}に更新")
            low = mid + 1
        else:
            print(f"  → ページ{mid}に既存IDなし → highを{mid-1}に更新")
            high = mid - 1

    # 💡 lowページ自体には既存IDがなかったが、直前ページにあった可能性がある
    final_resume_page = max(1, low - 1)
    print(f"✅ 探索終了 → 再確認含め、再開ページは {final_resume_page} から")

    return final_resume_page





# メイン処理
def main():
    """
    メイン処理:
    - スクレイピング済みIDセットから再開ページを決定
    - データを取得して分類（ポケモン・非ポケモン・基本エネルギー・特殊エネルギー）
    - 各JSONファイルへ保存
    """
    base_url = "https://www.pokemon-card.com/card-search/resultAPI.php?page={}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # 最大ページ数を取得

    try:
        resp = requests.get(base_url.format(1), headers=headers)
        if resp.status_code == 403:
            print("⚠️ 接続失敗: サイト側のアクセス制限（403 Forbidden）です。時間をおいて再試行してください。")
            return
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 接続エラー: {e}")
        return
    data = resp.json()
    max_page = data.get("maxPage", 1)

    # 取得済みIDのセットを読み込む
    existing_ids = load_existing_ids()

    # 再開ページを決定
    if existing_ids:
        resume_page = find_resume_page(existing_ids, max_page, base_url, headers)
        print(f"▶ 既存カードIDに基づき、再開ページは {resume_page} から")
    else:
        resume_page = 1
        print("▶ 既存データなし → 1ページ目から開始")

    # データ取得（分類付き）
    pokemon_cards, non_pokemon_cards, basic_energy_cards, special_energy_cards = fetch_pokemon_data(
        base_url=base_url,
        max_page=max_page,
        headers=headers,
        pack_flag=False,
        threshold=None,
        start_page=resume_page
    )

    # 既存ファイル読み込み
    def load_cards_from_file(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["cards"] if isinstance(data, dict) and "cards" in data else data
        return []

    existing_pokemon = load_cards_from_file("pokemon_cards.json")
    existing_non_pokemon = load_cards_from_file("non_pokemon_cards.json")
    existing_basic_energy = load_cards_from_file("basic_energy_cards.json")
    existing_special_energy = load_cards_from_file("special_energy_cards.json")

    # 重複を除いてマージ
    def merge(existing, new):
        existing_ids = {c["id"] for c in existing}
        return existing + [c for c in new if c["id"] not in existing_ids]

    combined_pokemon = merge(existing_pokemon, pokemon_cards)
    combined_non_pokemon = merge(existing_non_pokemon, non_pokemon_cards)
    combined_basic_energy = merge(existing_basic_energy, basic_energy_cards)
    combined_special_energy = merge(existing_special_energy, special_energy_cards)

    # 保存
    save_to_json(
        pokemon_cards=combined_pokemon,
        non_pokemon_cards=combined_non_pokemon,
        basic_energy_cards=combined_basic_energy,
        special_energy_cards=combined_special_energy
    )

    # スクレイピング.json 更新
    update_scraping_json(combined_pokemon, combined_non_pokemon)

    # 結果出力
    print(f"✅ Pokémon: 新規追加 {len(combined_pokemon) - len(existing_pokemon)} 件、合計 {len(combined_pokemon)} 件")
    print(f"✅ 非Pokémon: 新規追加 {len(combined_non_pokemon) - len(existing_non_pokemon)} 件、合計 {len(combined_non_pokemon)} 件")
    print(f"✅ 基本エネルギー: 新規追加 {len(combined_basic_energy) - len(existing_basic_energy)} 件、合計 {len(combined_basic_energy)} 件")
    print(f"✅ 特殊エネルギー: 新規追加 {len(combined_special_energy) - len(existing_special_energy)} 件、合計 {len(combined_special_energy)} 件")

if __name__ == "__main__":
    main()