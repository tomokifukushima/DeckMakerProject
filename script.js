document.addEventListener("DOMContentLoaded", () => {
    const cardList = document.getElementById("cardList");
    const searchBox = document.getElementById("searchBox");
    const categoryFilter = document.getElementById("categoryFilter");
    const addConditionBtn = document.getElementById("add-condition-btn");
    const conditionPopup = document.getElementById("condition-popup");
    const deckArea = document.getElementById("deckArea");

    const popup = document.getElementById("popup");
    const popupImage = document.getElementById("popup-image");
    const popupName = document.getElementById("popup-name");
    const plusBtn = document.getElementById("plus-btn");
    const minusBtn = document.getElementById("minus-btn");
    const cardCount = document.getElementById("card-count");
    const closeBtn = document.querySelector(".close-btn");
    const generateDeckBtn = document.getElementById("generateDeckBtn");
    const DEFAULT_IMAGE = "images/default.png";

    const selectedTags = new Map(); // 選択されたタグを管理するMap
    const conditionContainer = document.getElementById("condition-container");

    const deck = {};//Idをキーとして管理する
    let currentCard = null;
    let cards = []; // 全カードデータ
    let conditionData = {}; // 条件データ

    // 2つのJSONを並列で取得
    Promise.all([
        fetch("pokemon_cards.json").then(response => response.json()),
        fetch("non_pokemon_cards.json").then(response => response.json())
    ])
    .then(([pokemonData, nonPokemonData]) => {
        // 両方のデータを統合
        cards = [...pokemonData, ...nonPokemonData];

        // カテゴリフィルターを設定
        const allCategories = new Set(cards.map(card => card["カテゴリ"]).filter(Boolean));
        allCategories.forEach(category => {
            const option = document.createElement("option");
            option.value = category;
            option.textContent = category;
            categoryFilter.appendChild(option);
        });


        // 検索ボックス、タイプフィルター、カテゴリフィルターのイベントリスナーを設定
        searchBox.addEventListener("input", renderCardList);
        categoryFilter.addEventListener("change", renderCardList);

        // TODO:
        conditionContainer.innerHTML = "";
        categoryFilter.addEventListener("change", e => {
            conditionContainer.innerHTML = ""
            selectedTags.clear();
        });

        // ドラッグ＆ドロップのイベントリスナーを設定
        deckArea.addEventListener("dragover", e => e.preventDefault());
        deckArea.addEventListener("drop", e => {
            e.preventDefault();
            const cardId = e.dataTransfer.getData("card-id");
            const card = cards.find(c => c.id === cardId);
            if (!card) return;

            if (!deck[card.id]) {
                deck[card.id] = 0;
                addCardToDeck(card);
            }

            if (deck[card.id] < 4) {
                deck[card.id]++;
                document.getElementById(`deck-card-${cssId(card.id)}`)
                    .querySelector(".count").textContent = `x${deck[card.id]}`;
            }
        });

        // カードリストをレンダリング
        renderCardList();
    })
    .catch(error => {
        console.error("JSONの読み込みに失敗:", error);
    });

    // 条件データを取得
    fetch("condition_data.json")
    .then(response => {
        if (!response.ok) {
            throw new Error("HTTP error " + response.status);
        }
        return response.json(); // レスポンスをJSON形式に変換
    })
    .then(data => {
        conditionData = data;
    })
    .catch(error => {
        console.error("JSONの読み込みに失敗:", error);
    });

    // カードリストをレンダリングする関数
    function renderCardList() {
        const query = searchBox.value.toLowerCase();
        const selectedCategory = categoryFilter.value;
        cardList.innerHTML = "";

        // フィルタリングされたカードを取得
        const _filteredCards = cards.filter(card =>
            card["カード名"].toLowerCase().includes(query) &&
            (selectedCategory === "" || card["カテゴリ"] === selectedCategory)
        );

        const filteredCards = _filteredCards.filter(card => {
            return Array.from(selectedTags.entries()).every(([category, values]) => {
                if (Array.isArray(card[category])) {
                    // 複数の値の場合
                    return card[category].some(value => values.has(value));
                  } else {
                     // 単一の値の場合
                    return values.has(card[category]);
                  }
            });
        });

        // フィルタリングされたカードをリストに追加
        filteredCards.forEach(card => {
            const cardDiv = document.createElement("div");
            cardDiv.classList.add("card");
            const imgSrc = card["画像"] || DEFAULT_IMAGE;
            const cardName = card["カード名"];

            cardDiv.innerHTML = `
                <img src="${imgSrc}" alt="${cardName}">
                <p>${cardName}</p>
            `;

            cardDiv.addEventListener("click", () => openPopup(card));

            cardDiv.setAttribute("draggable", true);
            cardDiv.addEventListener("dragstart", (e) => {
                e.dataTransfer.setData("card-id", card.id);
            });

            // ドラッグしてデッキエリアに追加する設定
            cardList.appendChild(cardDiv);
        });
    }

    addConditionBtn.addEventListener("click", () => {
        const selectedCategory = categoryFilter.value;

        if (conditionContainer.innerHTML == "") {

        conditionContainer.style.width = "100%";

        Object.keys(conditionData).forEach(mainCondition => {
            const wrapper = document.createElement("div");
            wrapper.style.display = "flex";
            wrapper.style.background = "#e7e7e7";

            const boxL = document.createElement("div");
            boxL.style.width = "200px";
            boxL.style.padding = "4px";
            boxL.textContent = mainCondition;
            boxL.style.textAlign = "left";
            boxL.style.background = "#a0a0a0";
            boxL.style.borderTop = "1px solid #c3c3c3";
            wrapper.appendChild(boxL);

            const boxR = document.createElement("div");
            boxR.style.flexDirection = "column";
            boxR.style.width = "100%";

            const subConditions = conditionData[mainCondition];
            subConditions.forEach(subCondition => {
                const subBoxT = document.createElement("div");
                subBoxT.style.borderBottom = "1px solid #c3c3c3";
                if (subConditions.length > 1) {
                    subBoxT.textContent = subCondition.label;
                    subBoxT.style.padding = "4px";
                    subBoxT.style.textAlign = "left";
                    subBoxT.style.background = "#dddddd";
                }
                boxR.appendChild(subBoxT);

                const subBoxB = document.createElement("div");
                subBoxB.style.padding = "4px";
                subBoxB.style.display = "flex";
                subBoxB.style.textAlign = "left";
                subBoxB.style.flexDirection = "row";
                subBoxB.style.flexWrap = "wrap";

                const type = subCondition.type;
                const category = subCondition.category;
                const details = subCondition.details;
                const cssClass = subCondition.cssClass;
                if (type === "checkbox") {
                    details.forEach((detail, index) => {
                        // checkboxの表示エリア
                        const checkBoxField = document.createElement("div");
                        checkBoxField.classList.add("checkbox-field");

                        // checkbox
                        const checkbox = document.createElement("input");
                        checkbox.type = "checkbox";
                        checkbox.addEventListener("click", (e) => {
                            const isChecked = e.target.checked;
                            selectCondition(isChecked, category, detail)
                        });
                        checkBoxField.appendChild(checkbox);

                        // checkboxのラベル
                        const label = document.createElement("div");
                        label.style.display = "flex";
                        label.style.alignItems = "center";

                        const text = document.createElement("span");
                        if (cssClass) {
                            text.classList.add(cssClass[index]);
                        }
                        text.textContent = detail;
                        label.appendChild(text);
                        checkBoxField.appendChild(label);

                        subBoxB.appendChild(checkBoxField);
                    });
                } else if (type === "range-dropdown") {
                    const select1 = document.createElement("select");
                    select1.style.width = "80px";
                    details[0].forEach((detail, index) => {
                        const option = document.createElement("option");
                        option.value = detail;
                        option.textContent = detail;

                        // 最初の選択肢をデフォルトで選択
                        if (index === 0) {
                            option.selected = true;
                        }

                        select1.appendChild(option);
                    });
                    subBoxB.appendChild(select1);

                    const text = document.createElement("div");
                    text.style.width = "20px";
                    text.style.textAlign = "center";
                    text.textContent = "～";
                    subBoxB.appendChild(text);


                    const select2 = document.createElement("select");
                    select2.style.width = "80px";
                    details[1].forEach((detail, index) => {
                        const option = document.createElement("option");
                        option.value = detail;
                        option.textContent = detail;

                        // 最後の選択肢をデフォルトで選択
                        if (index === details[1].length - 1) {
                            option.selected = true;
                        }

                        select2.appendChild(option);
                    });
                    subBoxB.appendChild(select2);
                } else if (type === "text") {
                    const input = document.createElement("input");
                    input.type = "text";
                    subBoxB.appendChild(input);
                }

                boxR.appendChild(subBoxB);
            });

            wrapper.appendChild(boxR);

            conditionContainer.appendChild(wrapper);
        });

        }

        conditionPopup.style.display = "flex";
    });

    function selectCondition(isChecked, category, tag) {
        if (isChecked) {
            if (!selectedTags.has(category)) {
                selectedTags.set(category, new Set());
            }
            selectedTags.get(category).add(tag);
            console.log("タグ追加:", category, tag);
        } else {
            if (selectedTags.has(category)) {
                selectedTags.get(category).delete(tag);
                if (selectedTags.get(category).size === 0) {
                    selectedTags.delete(category);
                }
            }
            console.log("タグ解除:", category, tag);
        }
        console.log("現在選択されているタグ:", Array.from(selectedTags));

        renderCardList();
    }

    document.addEventListener("dragover", e => e.preventDefault());
    document.addEventListener("drop", (e) => {
        const droppedCardId = e.dataTransfer.getData("deck-card-id");
        if (!droppedCardId) return;
        const isInsideDeck = deckArea.contains(e.target) || e.target === deckArea;
        if (isInsideDeck) return;

        if (deck[droppedCardId] > 0) {
            deck[droppedCardId]--;
            if (deck[droppedCardId] === 0) {
                removeCardFromDeck(droppedCardId);
            } else {
                document.getElementById(`deck-card-${cssId(droppedCardId)}`)
                    .querySelector(".count").textContent = `x${deck[droppedCardId]}`;
            }
            if (currentCard && currentCard["カード名"] === droppedCardId) {
                cardCount.textContent = deck[droppedCardId] || 0;
                updateButtonState();
            }
        }
    });

    function openPopup(card) {
        currentCard = card;

        // メインのカード画像を設定
        popupImage.src = card["画像"] || DEFAULT_IMAGE;

        // ボタンコンテナを作成
        const buttonContainer = document.getElementById("button-container");
        buttonContainer.innerHTML = ""; // コンテナを初期化

        // ボタンを4つ作成して追加
        const buttonNames = ["イラスト\n変更", "進化系統\nカード", "関連タグ", "関連情報"]; // ボタンの名前をリストで指定

        buttonNames.forEach((name, index) => {
            const button = document.createElement("button");
            button.textContent = name; // 指定した名前をボタンに設定
            button.classList.add("popup-button");

            // 最初のボタン（"イラスト\n変更"）を押された状態にする
            if (index === 0) {
                button.classList.add("active");
                handleButtonClick(card, name);
            }

            // ボタンをクリックしたときの動作
            button.addEventListener("click", () => {
                // 他のボタンの "active" クラスを解除
                const allButtons = document.querySelectorAll(".popup-button");
                allButtons.forEach(btn => btn.classList.remove("active"));

                // 押されたボタンに "active" クラスを追加
                button.classList.add("active");

                // 押されたボタンに応じた処理を実行
                handleButtonClick(card, name);
            });

            buttonContainer.appendChild(button);
        });

        popupName.textContent = card["カード名"];
        cardCount.textContent = deck[card.id] || 0;
        updateButtonState();
        popup.style.display = "flex";
    }

    // ボタンに応じた処理を実行する関数
    function handleButtonClick(card, buttonName) {
        const sameCardsContainer = document.getElementById("same-cards-container");
        sameCardsContainer.innerHTML = ""; // コンテナを初期化

        if (buttonName === "イラスト\n変更") {
            // イラスト変更の処理
            // "同じカードid" が存在する場合のみ処理を実行
            const sameCardsContainer = document.getElementById("same-cards-container");
            sameCardsContainer.innerHTML = ""; // コンテナを初期化

            if (card["同じカードid"] && Array.isArray(card["同じカードid"])) {
                const otherCards = cards.filter(c => card["同じカードid"].includes(c["id"]));

                // 同じカードの画像を追加
                otherCards.forEach(otherCard => {
                    const img = document.createElement("img");
                    img.src = otherCard["画像"] || DEFAULT_IMAGE;
                    img.alt = otherCard["カード名"];
                    img.addEventListener("click", () => openPopup(otherCard)); // クリックでポップアップを開く
                    sameCardsContainer.appendChild(img);
                });
            }
        } else if (buttonName === "進化系統\nカード") {
            // 進化系統カードの処理
            // "進化系統カードid" が存在する場合のみ処理を実行
            const sameCardsContainer = document.getElementById("same-cards-container");
            sameCardsContainer.innerHTML = ""; // コンテナを初期化

            if (card["進化系統カードid"] && Array.isArray(card["進化系統カードid"])) {
                const otherCards = cards.filter(c => card["進化系統カードid"].includes(c["id"]));

                // 進化系統カードの画像を追加
                otherCards.forEach(otherCard => {
                    const img = document.createElement("img");
                    img.src = otherCard["画像"] || DEFAULT_IMAGE;
                    img.alt = otherCard["カード名"];
                    img.addEventListener("click", () => openPopup(otherCard)); // クリックでポップアップを開く
                    sameCardsContainer.appendChild(img);
                });
            }
        } else if (buttonName === "関連タグ") {
            // 関連タグの処理
            if (card["特別なルール"]) {
                sameCardsContainer.textContent = `特別なルール: ${card["特別なルール"]}`;
            }
        } else if (buttonName === "関連情報") {
            // 関連情報の処理
            // sameCardsContainer.innerHTML = `
            //     <a href="https://www.pokemon-card.com/card-search/index.php?keyword=${card["カード名"]}&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true"
            //     target="_blank"
            //     rel="noopener noreferrer">
            //     ポケモンカード公式サイトで検索
            //     </a>
            // `;
            sameCardsContainer.innerHTML = `
                <a href="https://www.pokemon-card.com/card-search/details.php/card/${card["id"]}/regu/XY"
                target="_blank"
                rel="noopener noreferrer">
                ポケモンカード公式サイトで検索
                </a>
            `;
        }
    }

    // 全てのclose-btnにイベントリスナーを追加
    document.querySelectorAll(".close-btn").forEach(closeBtn => {
        closeBtn.addEventListener("click", (e) => {
            // ボタンが属するポップアップを閉じる
            const popup = e.target.closest(".popup");
            if (popup) {
                popup.style.display = "none";
            }
        });
    });

    // ポップアップの外側をクリックしたら閉じる処理も共通化
    document.querySelectorAll(".popup").forEach(popup => {
        popup.addEventListener("click", (e) => {
            if (e.target === popup) {
                popup.style.display = "none";
            }
        });
    });

    plusBtn.addEventListener("click", () => {//ポップアップのブラスボタンクリック時のイベント
        const id = currentCard.id;
        if (!deck[id]) {
            deck[id] = 0;
            addCardToDeck(currentCard);
        }

        if (deck[id] < 4) {
            deck[id]++;
            document.getElementById(`deck-card-${cssId(id)}`)
                .querySelector(".count").textContent = `x${deck[id]}`;
            cardCount.textContent = deck[id];
        }

        updateButtonState();
    });

    minusBtn.addEventListener("click", () => {
        const id = currentCard.id;
        if (deck[id] > 0) {
            deck[id]--;
            cardCount.textContent = deck[id];

            const deckCard = document.getElementById(`deck-card-${cssId(id)}`);
            if (deck[id] === 0) {
                removeCardFromDeck(id);
            } else {
                deckCard.querySelector(".count").textContent = `x${deck[id]}`;
            }
        }
        updateButtonState();
    });

    //deck生成ボタンのイベント処理
    generateDeckBtn.addEventListener("click", () => {
        generateDeckImage();//デッキリスト画像作成関数呼び出し
    });

    function addCardToDeck(card) {
        const deckCard = document.createElement("div");
        deckCard.classList.add("deck-card");
        deckCard.id = `deck-card-${cssId(card.id)}`;
        const imgSrc = card["画像"] || DEFAULT_IMAGE;
        deckCard.innerHTML = `
            <img src="${imgSrc}" alt="${card["カード名"]}">
            <span class="count">x1</span>
        `;
        deckCard.addEventListener("click", () => openPopup(card));

        // ドラッグして削除する設定
        deckCard.setAttribute("draggable", true);
        deckCard.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("deck-card-id", card.id);
        });

        deckArea.appendChild(deckCard);
    }

    function removeCardFromDeck(name) {
        const cardId = `deck-card-${cssId(name)}`;
        const elem = document.getElementById(cardId);
        if (elem) elem.remove();
        delete deck[name];
    }

    function updateButtonState() {
        if(currentCard === null) return;
        const count = deck[currentCard.id] || 0;
        minusBtn.disabled = count === 0;
        plusBtn.disabled = count >= 4;
        minusBtn.classList.toggle("disabled", count === 0);
        plusBtn.classList.toggle("disabled", count >= 4);
    }

    function cssId(name) {
        // return name.replace(/[^a-zA-Z0-9]/g, "_");
        return name
    }

    //デッキリスト画像作成関数
    function generateDeckImage() {
        
        const deckEntries = Object.entries(deck).filter(([id, count]) => count > 0);
        //デッキにカードが登録されていなければアラート
        if (deckEntries.length === 0) {
            alert("デッキにカードがありません！");
            return;
        }

        const cardWidth = 250;
        const cardHeight = 350;
        const cardsPerRow = 8;
        const margin = 10;
        const canvasWidth = (cardWidth + margin) * cardsPerRow;
        const rows = Math.ceil(deckEntries.length / cardsPerRow);
        const canvasHeight = (cardHeight + margin) * rows;

        //canvas作成
        const canvas = document.createElement("canvas");
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        const ctx = canvas.getContext("2d");

        //canvasにカード画像貼り付け
        const promises = deckEntries.map(([id, count], index) => {
            const card = cards.find(c => c.id === id);
            return new Promise((resolve) => {
                const img = new Image();
                img.crossOrigin = "anonymous"; 
                img.src = card["画像"] || DEFAULT_IMAGE;
                img.onload = () => {
                    const x = (index % cardsPerRow) * (cardWidth + margin);
                    const y = Math.floor(index / cardsPerRow) * (cardHeight + margin);
                    ctx.drawImage(img, x, y, cardWidth, cardHeight);
    
                    ctx.font = "30px Arial";
                    ctx.fillStyle = "white";
                    ctx.strokeStyle = "black";
                    ctx.lineWidth = 3;
                    const text = `x${count}`;
                    ctx.strokeText(text, x + cardWidth - 50, y + cardHeight - 10);
                    ctx.fillText(text, x + cardWidth - 50, y + cardHeight - 10);
    
                    resolve();
                };
            });
        });
        //canvasを画像変換してダウンロード
        Promise.all(promises).then(() => {
            const imageUrl = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = imageUrl;
            link.download = "decklist.png";
            link.click();
        });

    }
});