document.addEventListener("DOMContentLoaded", () => {
    const cardList = document.getElementById("cardList");
    const searchBox = document.getElementById("searchBox");
    const typeFilter = document.getElementById("typeFilter");
    const categoryFilter = document.getElementById("categoryFilter");
    const deckArea = document.getElementById("deckArea");

    const popup = document.getElementById("popup");
    const popupImage = document.getElementById("popup-image");
    const popupName = document.getElementById("popup-name");
    const plusBtn = document.getElementById("plus-btn");
    const minusBtn = document.getElementById("minus-btn");
    const cardCount = document.getElementById("card-count");
    const closeBtn = document.querySelector(".close-btn");

    const DEFAULT_IMAGE = "images/default.png";

    const deck = {};//Idをキーとして管理する
    let currentCard = null;
    let cards = []; // 全カードデータ

    // 2つのJSONを並列で取得
    Promise.all([
        fetch("pokemon_cards.json").then(response => response.json()),
        fetch("non_pokemon_cards.json").then(response => response.json())
    ])
    .then(([pokemonData, nonPokemonData]) => {
        // 両方のデータを統合
        cards = [...pokemonData, ...nonPokemonData];

        // タイプフィルターを設定
        const allTypes = new Set(cards.map(card => card["ポケモンのタイプ"]).filter(Boolean));
        allTypes.forEach(type => {
            const option = document.createElement("option");
            option.value = type;
            option.textContent = type;
            typeFilter.appendChild(option);
        });

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
        typeFilter.addEventListener("change", renderCardList);
        categoryFilter.addEventListener("change", renderCardList);

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
    .catch(error => console.error("JSONの読み込みに失敗:", error));

    // カードリストをレンダリングする関数
    function renderCardList() {
        const query = searchBox.value.toLowerCase();
        const selectedType = typeFilter.value;
        const selectedCategory = categoryFilter.value;
        cardList.innerHTML = "";

        // フィルタリングされたカードを取得
        const filteredCards = cards.filter(card =>
            card["カード名"].toLowerCase().includes(query) &&
            (selectedType === "" || card["ポケモンのタイプ"] === selectedType) &&
            (selectedCategory === "" || card["カテゴリ"] === selectedCategory)
        );

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
            sameCardsContainer.textContent = "関連タグの処理を実行中...";
        } else if (buttonName === "関連情報") {
            // 関連情報の処理
            // sameCardsContainer.textContent = "関連情報の処理を実行中...";
            // sameCardsContainer.textContent = "https://www.pokemon-card.com/card-search/index.php?keyword=%E3%82%AD%E3%83%8E%E3%82%AC%E3%83%83%E3%82%B5&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true";
            sameCardsContainer.innerHTML = `
                <a href="https://www.pokemon-card.com/card-search/index.php?keyword=${card["カード名"]}&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true" 
                target="_blank" 
                rel="noopener noreferrer">
                ポケモンカード公式サイトで検索
                </a>
            `;
        }
    }

    closeBtn.addEventListener("click", () => popup.style.display = "none");
    popup.addEventListener("click", (e) => {
        if (e.target === popup) popup.style.display = "none";
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
        return name.replace(/[^a-zA-Z0-9]/g, "_");
    }
});