document.addEventListener("DOMContentLoaded", () => {
    const cardList = document.getElementById("cardList");
    const searchBox = document.getElementById("searchBox");
    const typeFilter = document.getElementById("typeFilter");
    const deckArea = document.getElementById("deckArea");

    const popup = document.getElementById("popup");
    const popupImage = document.getElementById("popup-image");
    const popupName = document.getElementById("popup-name");
    const plusBtn = document.getElementById("plus-btn");
    const minusBtn = document.getElementById("minus-btn");
    const cardCount = document.getElementById("card-count");
    const closeBtn = document.querySelector(".close-btn");

    const DEFAULT_IMAGE = "images/default.png";

    const deck = {};
    let currentCard = null;
    let cards = []; // 全カードデータ

    fetch("pokemon_cards.json")
        .then(response => response.json())
        .then(data => {
            cards = data; // データをグローバル変数に代入
            const allTypes = new Set(cards.map(card => card["ポケモンのタイプ"]).filter(Boolean));
            allTypes.forEach(type => {
                const option = document.createElement("option");
                option.value = type;
                option.textContent = type;
                typeFilter.appendChild(option);
            });

            function renderCardList() {
                const query = searchBox.value.toLowerCase();
                const selectedType = typeFilter.value;
                cardList.innerHTML = "";

                const filteredCards = cards.filter(card =>
                    card["カード名"].toLowerCase().includes(query) &&
                    (selectedType === "" || card["ポケモンのタイプ"] === selectedType)
                );

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
                        e.dataTransfer.setData("card-name", cardName);
                    });

                    cardList.appendChild(cardDiv);
                });
            }

            searchBox.addEventListener("input", renderCardList);
            typeFilter.addEventListener("change", renderCardList);

            deckArea.addEventListener("dragover", e => e.preventDefault());
            deckArea.addEventListener("drop", e => {
                e.preventDefault();
                const cardName = e.dataTransfer.getData("card-name");
                const card = cards.find(c => c["カード名"] === cardName);
                if (!card) return;

                if (!deck[cardName]) {
                    deck[cardName] = 0;
                    addCardToDeck(card);
                }

                if (deck[cardName] < 4) {
                    deck[cardName]++;
                    document.getElementById(`deck-card-${cssId(cardName)}`)
                        .querySelector(".count").textContent = `x${deck[cardName]}`;
                }
            });

            renderCardList();
        })
        .catch(error => console.error("JSONの読み込みに失敗:", error));

    document.addEventListener("dragover", e => e.preventDefault());
    document.addEventListener("drop", (e) => {
        const droppedCardName = e.dataTransfer.getData("deck-card-name");
        if (!droppedCardName) return;
        const isInsideDeck = deckArea.contains(e.target) || e.target === deckArea;
        if (isInsideDeck) return;

        if (deck[droppedCardName] > 0) {
            deck[droppedCardName]--;
            if (deck[droppedCardName] === 0) {
                removeCardFromDeck(droppedCardName);
            } else {
                document.getElementById(`deck-card-${cssId(droppedCardName)}`)
                    .querySelector(".count").textContent = `x${deck[droppedCardName]}`;
            }
            if (currentCard && currentCard["カード名"] === droppedCardName) {
                cardCount.textContent = deck[droppedCardName] || 0;
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
        cardCount.textContent = deck[card["カード名"]] || 0;
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
            sameCardsContainer.textContent = "関連タグの処理を実行中...";
        } else if (buttonName === "関連情報") {
            // 関連情報の処理
            sameCardsContainer.textContent = "関連情報の処理を実行中...";
        }
    }

    closeBtn.addEventListener("click", () => popup.style.display = "none");
    popup.addEventListener("click", (e) => {
        if (e.target === popup) popup.style.display = "none";
    });

    plusBtn.addEventListener("click", () => {
        const name = currentCard["カード名"];
        if (!deck[name]) {
            deck[name] = 0;
            addCardToDeck(currentCard);
        }

        if (deck[name] < 4) {
            deck[name]++;
            document.getElementById(`deck-card-${cssId(name)}`)
                .querySelector(".count").textContent = `x${deck[name]}`;
            cardCount.textContent = deck[name];
        }

        updateButtonState();
    });

    minusBtn.addEventListener("click", () => {
        const name = currentCard["カード名"];
        if (deck[name] > 0) {
            deck[name]--;
            cardCount.textContent = deck[name];

            const deckCard = document.getElementById(`deck-card-${cssId(name)}`);
            if (deck[name] === 0) {
                removeCardFromDeck(name);
            } else {
                deckCard.querySelector(".count").textContent = `x${deck[name]}`;
            }
        }
        updateButtonState();
    });

    function addCardToDeck(card) {
        const deckCard = document.createElement("div");
        deckCard.classList.add("deck-card");
        deckCard.id = `deck-card-${cssId(card["カード名"])}`;
        const imgSrc = card["画像"] || DEFAULT_IMAGE;
        deckCard.innerHTML = `
            <img src="${imgSrc}" alt="${card["カード名"]}">
            <span class="count">x1</span>
        `;
        deckCard.addEventListener("click", () => openPopup(card));

        // ドラッグして削除する設定
        deckCard.setAttribute("draggable", true);
        deckCard.addEventListener("dragstart", (e) => {
            e.dataTransfer.setData("deck-card-name", card["カード名"]);
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
        const count = deck[currentCard["カード名"]] || 0;
        minusBtn.disabled = count === 0;
        plusBtn.disabled = count >= 4;
        minusBtn.classList.toggle("disabled", count === 0);
        plusBtn.classList.toggle("disabled", count >= 4);
    }

    function cssId(name) {
        return name.replace(/[^a-zA-Z0-9]/g, "_");
    }
});