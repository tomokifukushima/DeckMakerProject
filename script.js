document.addEventListener("DOMContentLoaded", () => {
  const cardList = document.getElementById("cardList");
  const searchBox = document.getElementById("searchBox");
  const deckArea = document.getElementById("deckArea");

  const popup = document.getElementById("popup");
  const popupImage = document.getElementById("popup-image");
  const popupName = document.getElementById("popup-name");
  const plusBtn = document.getElementById("plus-btn");
  const minusBtn = document.getElementById("minus-btn");
  const cardCount = document.getElementById("card-count");
  const closeBtn = document.querySelector(".close-btn");

  const DEFAULT_IMAGE = "images/default.png"; // デフォルト画像パス

  const deck = {};
  let currentCard = null;

  fetch("pokemon_cards.json")
      .then(response => response.json())
      .then(cards => {
          searchBox.addEventListener("input", () => {
              const query = searchBox.value.toLowerCase();
              cardList.innerHTML = "";

              const filteredCards = cards.filter(card =>
                  card["カード名"]?.toLowerCase().includes(query)
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
                  cardList.appendChild(cardDiv);
              });
          });
      })
      .catch(error => console.error("JSONの読み込みに失敗:", error));

  function openPopup(card) {
      currentCard = card;
      popupImage.src = card["画像"] || DEFAULT_IMAGE;
      popupName.textContent = card["カード名"];
      cardCount.textContent = deck[card["カード名"]] || 0;
      updateButtonState();
      popup.style.display = "flex";
  }

  closeBtn.addEventListener("click", closePopup);
  popup.addEventListener("click", (e) => {
      if (e.target === popup) closePopup();
  });

  function closePopup() {
      popup.style.display = "none";
  }

  plusBtn.addEventListener("click", () => {
      if (!deck[currentCard["カード名"]]) {
          deck[currentCard["カード名"]] = 0;
          addCardToDeck(currentCard);
      }

      if (deck[currentCard["カード名"]] < 4) {
          deck[currentCard["カード名"]]++;
          document.getElementById(`deck-card-${cssId(currentCard["カード名"])}`)
              .querySelector(".count").textContent = `x${deck[currentCard["カード名"]]}`;
          cardCount.textContent = deck[currentCard["カード名"]];
      }

      updateButtonState();
  });

  minusBtn.addEventListener("click", () => {
      if (deck[currentCard["カード名"]] > 0) {
          deck[currentCard["カード名"]]--;
          cardCount.textContent = deck[currentCard["カード名"]];

          const deckCard = document.getElementById(`deck-card-${cssId(currentCard["カード名"])}`);
          if (deck[currentCard["カード名"]] === 0) {
              removeCardFromDeck(currentCard["カード名"]);
          } else {
              deckCard.querySelector(".count").textContent = `x${deck[currentCard["カード名"]]}`;
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
      deckArea.appendChild(deckCard);
  }

  function removeCardFromDeck(cardName) {
      const cardId = `deck-card-${cssId(cardName)}`;
      const cardElem = document.getElementById(cardId);
      if (cardElem) cardElem.remove();
      delete deck[cardName];
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
