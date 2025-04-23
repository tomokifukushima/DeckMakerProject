import requests
from bs4 import BeautifulSoup

def main():
    base_url = "https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=XY&sc_type_ancient=1&pg=&illust=&sm_and_keyword=true&page={}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(base_url.format(1), headers=headers)

    if response.status_code != 200:
        print("データ取得失敗")
        return
    # data = response.json()
    
    c = None
    
    for page in range(1, 10):
        response = requests.get(base_url.format(page), headers=headers)
        detail = BeautifulSoup(response.text, "html.parser")
    
        if detail == c:
            print(page, "同じ")
            return
        else:
            c = detail
            print(page, "違う")
            a = c.find_all("a", id="card-show-id0")
            print(a)
    # print(c)

if __name__ == "__main__":
    main()