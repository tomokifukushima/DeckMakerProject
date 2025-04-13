from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import math

def create_decklist_image(card_dict, output_path="decklist.jpg"):
    """
    card_dict: { 'http://example.com/card1.jpg': 4, ... }
    output_path: 出力画像ファイル名
    """
    print("aaaaa")

    max_columns = 8
    card_width = 150
    card_height = 210
    spacing = 10
    text_height = 20

    # フォントの設定（OS依存：ここではデフォルトの PIL 内フォント）
    font = ImageFont.load_default()

    cards = list(card_dict.items())
    total_cards = len(cards)

    rows = math.ceil(total_cards / max_columns)
    img_width = max_columns * (card_width + spacing) + spacing
    img_height = rows * (card_height + spacing + text_height) + spacing

    # 空のキャンバスを作成
    deck_image = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(deck_image)

    for idx, (url, count) in enumerate(cards):
        try:
            response = requests.get(url)
            card_img = Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"Error loading image from {url}: {e}")
            continue

        # サイズ調整
        card_img = card_img.resize((card_width, card_height))

        # 数字（枚数）を画像の下部中央に黒背景＋白文字で入れる
        count_text = str(count)
        font_size = 20
        font = ImageFont.truetype("arial.ttf", font_size)

                # 配置座標
        x = spacing + (idx % max_columns) * (card_width + spacing)
        y = spacing + (idx // max_columns) * (card_height + spacing + text_height)

        # カード画像を貼る
        deck_image.paste(card_img, (x, y))

        # 数字（枚数）を画像の下部中央に黒背景＋白文字で入れる
        count_text = str(count)
        font_size = 20
        font = ImageFont.truetype("arial.ttf", font_size)

        # 数字のサイズを取得（新しい方法）
        bbox = draw.textbbox((0, 0), count_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 背景の黒い長方形サイズ（少し余裕持たせる）
        padding = 4
        rect_width = text_width + padding * 2
        rect_height = text_height + padding * 2

        # 背景の位置（画像下部に貼る）
        rect_x = x + (card_width - rect_width) // 2
        rect_y = y + card_height - rect_height - 5  # 下に少し余白

        # 黒背景を描画
        draw.rectangle(
            [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
            fill="black"
        )

        # 数字を白で描画（中央寄せ）
        text_x = rect_x + padding
        text_y = rect_y + padding
        draw.text((text_x, text_y), count_text, fill="white", font=font)




    # 保存
    deck_image.save(output_path)
    print(f"デッキリスト画像を保存しました: {output_path}")

def main():
    '''
    "現在は画像のURLを直接指定しているが、組み込む際はデッキゾーンに入れたら辞書に追加されるようにする"
    "また，デッキリストを作成する際に並べ替える機能がほしい．追加した順とは関係なく"
    "ポケモン→グッズ→どうぐ→サポート→スタジアム→エネルギー"
    "になるように"
    '''
    card_dict={
        'https://www.pokemon-card.com/assets/images/card_images/large/SV1S/042574_P_SANAITOEX.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV1S/042573_P_KIRURIA.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV4a/044603_P_RARUTOSU.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV6/045746_P_MASHIMASHIRA.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV8a/046732_P_SAKEBUSHIPPO.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV4a/044599_P_MIXYUUEX.jpg':1,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV9/047041_P_RIRIENOPIPPIEX.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV8a/046662_P_SUBOMI.jpg':1,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV9a/047301_P_SHIEIMI.jpg':1,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVOD/047282_T_HAIPABORU.jpg':4,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVOD/047281_T_NAKAYOSHIPOFUIN.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047189_T_DAICHINOUTSUWA.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047198_T_YORUNOTANKA.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047186_T_KAUNTAKIXYATCHIXYA.jpg':1,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV6/045783_T_SHIKURETTOBOKKUSU.jpg':1,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047203_T_YUUKINOOMAMORI.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047204_T_WAZAMASHINEVUORIXYUSHIXYON.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047212_T_PEPA.jpg':4,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVOD/047287_T_HAKASENOKENKIXYUU.jpg':4,
        'https://www.pokemon-card.com/assets/images/card_images/large/SV4a/045136_T_NANJIXYAMO.jpg':3,
        'https://www.pokemon-card.com/assets/images/card_images/large/SVN/047216_T_BOURUTAUN.jpg':2,
        'https://www.pokemon-card.com/assets/images/card_images/large/ENE/046120_E_KIHONCHIXYOUENERUGI.jpg':7,
        'https://www.pokemon-card.com/assets/images/card_images/large/ENE/046122_E_KIHONAKUENERUGI.jpg':3,
    }
    create_decklist_image(card_dict,output_path="decklist.jpg")

if __name__ == "__main__":
    main()