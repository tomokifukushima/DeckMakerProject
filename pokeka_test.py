import requests
import re
import json
from bs4 import BeautifulSoup


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
    "icon-dark": "悪",
    "icon-void": "なし"
}

# カードのレアリティ対応表
rarity_dict = {
    "c_c": "C",
    "u_c": "U",
    "r_c": "R",
    "rr": "RR",
    "ar": "AR",
    "sr_c": "SR",
    "sar": "SAR",
    "ur_c": "UR",
    "s_2": "S",
    "ssr": "SSR"
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
                if (card_j["カード名"] in card_i["進化系統"]):
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
    attacks_energy = []
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
                        if not type_dict[class_name] in attacks_energy:
                            attacks_energy.append(type_dict[class_name])
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
            
    return attacks, attacks_energy


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
    カードIDを使って、カードの詳細情報を取得する。
    """
    detail_url = f"https://www.pokemon-card.com/card-search/details.php/card/{card_id}/"
    detail_response = requests.get(detail_url, headers=headers)
    if detail_response.status_code != 200:
        return None
    return BeautifulSoup(detail_response.text, "html.parser")


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
    special_rule = []
    if "ex" in detail_soup.find("h1", class_="Heading1").text:
        special_rule.append("ポケモンex")
    if detail_soup.find("p", class_="mt20", string="このポケモンは、ベンチにいるかぎり、ワザのダメージを受けない。"):
        special_rule.append("「テラスタル」のポケモン")
    card_type = detail_soup.find("span", class_="type").text.strip()
    card_type = re.sub(r"\s", "", card_type) # スペースを削除
    hp = detail_soup.find("span", class_="hp-num").text.strip()
    pokemon_type = get_pokemon_type(detail_soup)
    weakness_type, resistance_type = get_weakness_and_resistance(detail_soup)
    escape_energy = get_escape_energy(detail_soup)
    evolution = [a.text.strip() for a in detail_soup.find_all("a", href=lambda x: x and "pokemon=" in x)]
    abilities = get_abilities(detail_soup)
    has_abilitie = "特性あり" if len(abilities) > 0 else "特性なし"
    attacks, attacks_energy = get_attacks(detail_soup)

    return {
        "id": card_id,
        "カード名": detail_soup.find("h1", class_="Heading1").text.strip(),
        "カテゴリ": "ポケモン",
        "進化": card_type,
        "HP": hp,
        "特別なルール": special_rule,
        "画像": image_url,
        "レギュレーション": regulation,
        "カード番号": card_number,
        "レアリティ": card_rarity,
        "イラストレーター": illustrator,
        "ポケモンのタイプ": pokemon_type,
        "特性の有無": has_abilitie,
        "特性": abilities,
        "ワザ": attacks,
        "ワザのエネルギー": attacks_energy,
        "弱点": weakness_type,
        "抵抗": resistance_type,
        "逃げるために必要なエネルギー": escape_energy,
        "進化系統": evolution,
        "収録パック": pack_name
    }


# カードデータを取得するメイン関数
def fetch_pokemon_data(base_url, max_page, headers, ids, pack_flag):
    """
    ページごとにポケモンカードの情報を取得し、ポケモンカードと非ポケモンカードを分けて保存する。
    """
    pokemon_cards = []
    non_pokemon_cards = []
    exit_loop = False
    id_order = [] # ソート用

    for page in range(1, max_page + 1):
        response = requests.get(base_url.format(page), headers=headers)
        if response.status_code != 200:
            continue
        data = response.json()

        for card in data["cardList"]:
            card_id = card["cardID"]
            id_order.append(card_id)
            if card_id in ids:
                continue
            detail_soup = get_card_details(card_id, headers)
            if not detail_soup:
                continue

            category_header = detail_soup.find("h2", class_="mt20")
            category_text = category_header.text.strip() if category_header else ""

            image_url = detail_soup.find("img", class_="fit")["src"]
            image_url="https://www.pokemon-card.com/"+image_url
            regulation = detail_soup.find("img", class_="img-regulation")["alt"]
            card_number = detail_soup.find("div", class_="subtext").text.strip().split()[0]
            illustrator = detail_soup.find("a", href=lambda x: x and "regulation_illust" in x)
            illustrator = illustrator.text.strip() if illustrator else "なし"
            pack_name = get_pack_name(detail_soup)
            rarity_img = detail_soup.find("img", src=lambda x: x and "/assets/images/card/rarity/" in x)
            if rarity_img:
                card_rarity = rarity_dict[rarity_img["src"].split("ic_rare_")[-1].split(".")[0]]
            else:
                card_rarity = "なし"

            if exit_loop:
                break

            if is_pokemon_card(category_text):
                pokemon_cards.append(get_pokemon_card_info(detail_soup, card_id, pack_name, image_url, regulation, card_number, illustrator, card_rarity))
                print(pokemon_cards[-1]["カード名"])
            else:
                non_pokemon_cards.append(get_non_pokemon_card_info(detail_soup, card_id, category_text, image_url, regulation, card_number, illustrator, pack_name, card_rarity))
                print(non_pokemon_cards[-1]["カード名"])

            if(pack_flag):
                # 収録パックが変わった場合や同じカードが続く場合はループを抜ける
                if len(pokemon_cards) >= 2:
                    current = pokemon_cards[-1]
                    previous = pokemon_cards[-2]
                    if current["収録パック"] != previous["収録パック"] or current["id"] == previous["id"]:
                        del pokemon_cards[-1]
                        print("収録パックが変わった or 同じカードが続く")
                        exit_loop = True
                        break

        if exit_loop:
            break

    return pokemon_cards, non_pokemon_cards, id_order


# JSONファイルを読み込む関数
def load_json(file_path):
    """
    指定されたJSONファイルを読み込む。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ファイルが見つかりません: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ JSONの読み込みに失敗しました: {file_path}")
        return []


# データをJSONとして保存する関数
def save_to_json(pokemon_cards, non_pokemon_cards):
    """
    取得したポケモンカードと非ポケモンカードのデータをJSONファイルに保存する。
    """
    with open("pokemon_cards.json", "w", encoding="utf-8") as f:
        json.dump(pokemon_cards, f, ensure_ascii=False, indent=4)
    with open("non_pokemon_cards.json", "w", encoding="utf-8") as f:
        json.dump(non_pokemon_cards, f, ensure_ascii=False, indent=4)
    print(f"✅ ポケモン: {len(pokemon_cards)}枚, トレーナーズ: {len(non_pokemon_cards)}枚 を保存しました！")


def sort_by_specified_ids(data_list, id_order):
    """
    指定したIDの順序に基づいてデータをソートする。
    """
    id_to_index = {id_: index for index, id_ in enumerate(id_order)}
    return sorted(data_list, key=lambda x: id_to_index.get(x["id"], float("inf")))


# メイン処理
def main():
    """
    メイン処理: ポケモンカードのデータを取得し、JSONファイルに保存する。
    """
    base_url = "https://www.pokemon-card.com/card-search/resultAPI.php?page={}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url.format(1), headers=headers)
    if response.status_code != 200:
        print("データ取得失敗")
        return
    data = response.json()
    
    # 既存のIDを抽出
    parsed_pokemon_data = load_json("pokemon_cards.json")
    parsed_non_pokemon_data = load_json("non_pokemon_cards.json")
    parsed_data = parsed_pokemon_data + parsed_non_pokemon_data
    ids = [item["id"] for item in parsed_data]
    
    max_page = data.get("maxPage", 1)
    print(max_page)
    print(f"32ページ目でへばるので{max_page-147}ページだけやります")
    pokemon_cards, non_pokemon_cards, id_order = fetch_pokemon_data(base_url, max_page-147, headers, ids, pack_flag=False)
    # 同じカードidを追加する
    find_same_card(pokemon_cards,True)
    find_same_card(non_pokemon_cards,False)
    
    # 進化系統カードidを追加する
    add_evolution_chain_ids(pokemon_cards)

    # データを結合
    combined_pokemon_data = pokemon_cards + parsed_pokemon_data
    combined_non_pokemon_data = non_pokemon_cards + parsed_non_pokemon_data

    # idでソート（数値としてソートする場合はintに変換）
    sorted_pokemon_data = sort_by_specified_ids(combined_pokemon_data, id_order)
    sorted_non_pokemon_data = sort_by_specified_ids(combined_non_pokemon_data, id_order)

    save_to_json(sorted_pokemon_data, sorted_non_pokemon_data)


if __name__ == "__main__":
    main()
