/* =========================================================
   SPOTIFY RECOMMENDER FRONTEND
   HTML + CSS + JavaScript
   Backend: FastAPI
========================================================= */


// =========================================================
// API CONFIGURATION
// =========================================================

const API_URL = "/recommend";
const HEALTH_URL = "/health";
const SONGS_URL = "songs.json";


// =========================================================
// GET HTML ELEMENTS
// =========================================================

const songNameInput =
    document.getElementById("songName");

const artistNameInput =
    document.getElementById("artistName");

const filteringTypeSelect =
    document.getElementById("filteringType");

const recommendationCountSelect =
    document.getElementById(
        "recommendationCount"
    );

const diversitySlider =
    document.getElementById("diversity");

const diversityValue =
    document.getElementById(
        "diversityValue"
    );

const recommendButton =
    document.getElementById(
        "recommendButton"
    );

const buttonText =
    document.getElementById(
        "buttonText"
    );

const buttonIcon =
    document.getElementById(
        "buttonIcon"
    );

const errorMessage =
    document.getElementById(
        "errorMessage"
    );

const errorText =
    document.getElementById(
        "errorText"
    );

const resultsSection =
    document.getElementById(
        "resultsSection"
    );

const resultCount =
    document.getElementById(
        "resultCount"
    );

const currentSongName =
    document.getElementById(
        "currentSongName"
    );

const currentArtistName =
    document.getElementById(
        "currentArtistName"
    );

const methodBadge =
    document.getElementById(
        "methodBadge"
    );

const recommendationsGrid =
    document.getElementById(
        "recommendationsGrid"
    );

const songCatalogElement =
    document.getElementById("songCatalog");

const songCatalogStatus =
    document.getElementById("songCatalogStatus");

const songSearchInput =
    document.getElementById("songSearch");

const randomSongButton =
    document.getElementById("randomSongButton");


// =========================================================
// AUDIO STATE
// =========================================================

let currentAudio = null;

let currentPlayButton = null;

let songCatalog = [];

let selectedSong = null;


// =========================================================
// INITIALIZATION
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        updateDiversity();

        checkBackend();

        loadSongCatalog();

    }
);


// =========================================================
// SONG PICKER
// =========================================================

randomSongButton.addEventListener(
    "click",
    () => {

        if (songCatalog.length === 0) {
            return;
        }

        const randomIndex =
            Math.floor(
                Math.random() * songCatalog.length
            );

        songSearchInput.value = "";
        renderSongCatalog();
        selectSong(songCatalog[randomIndex], randomIndex);

    }
);

songSearchInput.addEventListener(
    "input",
    renderSongCatalog
);


async function loadSongCatalog() {

    try {

        const response =
            await fetch(SONGS_URL);

        if (!response.ok) {
            throw new Error(
                `Song catalog request failed (${response.status}).`
            );
        }

        const data =
            await response.json();

        if (!Array.isArray(data.songs)) {
            throw new Error(
                "The song catalog response is invalid."
            );
        }

        songCatalog =
            data.songs.filter(
                (song) =>
                    typeof song.name === "string" &&
                    typeof song.artist === "string"
            );

        renderSongCatalog();

        randomSongButton.disabled =
            songCatalog.length === 0;

        songCatalogStatus.textContent =
            songCatalog.length > 0
                ? `Showing ${songCatalog.length} songs. Select one or pick at random.`
                : "No songs are available right now.";

    } catch (error) {

        console.error("Could not load the song catalog:", error);

        songCatalogStatus.textContent =
            "Couldn't load the song list. Please try again later.";

    }
}


function renderSongCatalog() {

    songCatalogElement.replaceChildren();

    const query =
        songSearchInput.value.trim().toLocaleLowerCase();

    const visibleSongs =
        songCatalog
            .map((song, index) => ({ song, index }))
            .filter(
                ({ song }) =>
                    `${song.name} ${song.artist}`
                        .toLocaleLowerCase()
                        .includes(query)
            );

    songCatalogStatus.textContent =
        query
            ? `Showing ${visibleSongs.length} of ${songCatalog.length} songs.`
            : `Showing ${songCatalog.length} songs. Select one or pick at random.`;

    if (visibleSongs.length === 0) {

        const emptyItem =
            document.createElement("li");

        emptyItem.className = "catalog-empty";
        emptyItem.textContent = "No songs match that search.";
        songCatalogElement.append(emptyItem);

        return;
    }

    visibleSongs.forEach(
        ({ song, index }) => {

            const item =
                document.createElement("li");

            const button =
                document.createElement("button");

            button.type = "button";
            button.className = "song-picker-item";
            button.dataset.songIndex = String(index);

            const isSelected =
                selectedSong?.name === song.name &&
                selectedSong?.artist === song.artist;

            button.classList.toggle("selected", isSelected);
            button.setAttribute("aria-pressed", String(isSelected));

            const icon =
                document.createElement("span");

            icon.className = "catalog-track-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = "♫";

            const copy =
                document.createElement("span");

            copy.className = "catalog-track-copy";

            const songName =
                document.createElement("span");

            songName.className = "song-picker-name";
            songName.textContent = song.name;

            const artistName =
                document.createElement("span");

            artistName.className = "song-picker-artist";
            artistName.textContent = song.artist;

            copy.append(songName, artistName);
            button.append(icon, copy);

            button.addEventListener(
                "click",
                () => selectSong(song, index)
            );

            item.append(button);
            songCatalogElement.append(item);

        }
    );
}


function selectSong(song, selectedIndex) {

    selectedSong = song;

    songNameInput.value = song.name;
    artistNameInput.value = song.artist;

    songCatalogElement
        .querySelectorAll(".song-picker-item")
        .forEach(
            (button, index) => {

                const isSelected =
                    Number(button.dataset.songIndex) === selectedIndex;

                button.classList.toggle(
                    "selected",
                    isSelected
                );

                button.setAttribute(
                    "aria-pressed",
                    String(isSelected)
                );

            }
        );

    songCatalogStatus.textContent =
        `Selected "${song.name}" by ${song.artist}.`;
}


// =========================================================
// DIVERSITY SLIDER
// =========================================================

diversitySlider.addEventListener(
    "input",
    updateDiversity
);


function updateDiversity() {

    const value =
        Number(
            diversitySlider.value
        );

    diversityValue.textContent =
        `${value}/10`;


    /*
        Create a green progress effect
        on the range slider.
    */

    const percentage =
        ((value - 1) / 9) * 100;


    diversitySlider.style.background =
        `linear-gradient(
            to right,
            #1ed760 0%,
            #1ed760 ${percentage}%,
            #303036 ${percentage}%,
            #303036 100%
        )`;
}


// =========================================================
// FILTERING TYPE CHANGE
// =========================================================

filteringTypeSelect.addEventListener(
    "change",
    () => {

        const filteringType =
            filteringTypeSelect.value;


        /*
            Diversity is mainly useful
            for Hybrid recommendation.
        */

        if (
            filteringType ===
            "Hybrid Recommender System"
        ) {

            diversitySlider.disabled =
                false;

            diversitySlider.style.opacity =
                "1";

        } else {

            diversitySlider.disabled =
                false;

            diversitySlider.style.opacity =
                "0.7";
        }

    }
);


// =========================================================
// BACKEND HEALTH CHECK
// =========================================================

async function checkBackend() {

    try {

        const response = await fetch(HEALTH_URL);


        if (!response.ok) {

            setBackendStatus(false);

            return;
        }


        const data =
            await response.json();


        setBackendStatus(
            data.models_loaded === true
        );


    } catch (error) {

        console.warn(
            "Backend is not running."
        );

        setBackendStatus(false);

    }
}


// =========================================================
// BACKEND STATUS UI
// =========================================================

function setBackendStatus(
    isOnline
) {

    const statusDot =
        document.querySelector(
            ".status-dot"
        );

    const statusText =
        document.querySelector(
            ".api-status span:last-child"
        );


    if (!statusDot || !statusText) {

        return;
    }


    if (isOnline) {

        statusDot.style.background =
            "#d3fb65";

        statusDot.style.boxShadow =
            "0 0 12px rgba(211, 251, 101, 0.55)";

        statusText.textContent =
            "AI Recommendation Engine";

    } else {

        statusDot.style.background =
            "#ff5c5c";

        statusDot.style.boxShadow =
            "0 0 10px rgba(255, 92, 92, 0.7)";

        statusText.textContent =
            "Backend Offline";

    }
}


// =========================================================
// BUTTON CLICK
// =========================================================

recommendButton.addEventListener(
    "click",
    getRecommendations
);


// =========================================================
// ENTER KEY
// =========================================================

songNameInput.addEventListener(
    "keydown",
    handleEnter
);


artistNameInput.addEventListener(
    "keydown",
    handleEnter
);


function handleEnter(event) {

    if (
        event.key ===
        "Enter"
    ) {

        getRecommendations();

    }
}


// =========================================================
// GET RECOMMENDATIONS
// =========================================================

async function getRecommendations() {

    clearError();


    // -----------------------------------------------------
    // Get values
    // -----------------------------------------------------

    const songName =
        songNameInput.value.trim();

    const artistName =
        artistNameInput.value.trim();

    const filteringType =
        filteringTypeSelect.value;

    const k =
        Number(
            recommendationCountSelect.value
        );

    const diversity =
        Number(
            diversitySlider.value
        );


    // -----------------------------------------------------
    // Validation
    // -----------------------------------------------------

    if (!songName) {

        showError(
            "Please enter a song name."
        );

        songNameInput.focus();

        return;
    }


    if (!artistName) {

        showError(
            "Please enter an artist name."
        );

        artistNameInput.focus();

        return;
    }


    // -----------------------------------------------------
    // Start loading
    // -----------------------------------------------------

    setLoading(true);


    // Stop currently playing audio
    stopAudio();


    try {

        // -------------------------------------------------
        // API REQUEST
        // -------------------------------------------------

        const response =
            await fetch(
                API_URL,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        song_name:
                            songName,

                        artist_name:
                            artistName,

                        k:
                            k,

                        filtering_type:
                            filteringType,

                        diversity:
                            diversity

                    })

                }
            );


        // -------------------------------------------------
        // Read response
        // -------------------------------------------------

        const responseBody =
            await response.text();

        let data = null;

        if (responseBody.trim()) {

            try {

                data = JSON.parse(responseBody);

            } catch {

                if (response.ok) {
                    throw new Error(
                        "The recommendation service returned an invalid response."
                    );
                }

            }

        }


        // -------------------------------------------------
        // API ERROR
        // -------------------------------------------------

        if (!response.ok) {

            throw new Error(
                data?.detail ||
                `Recommendation service returned HTTP ${response.status}. Please try again shortly.`
            );

        }

        if (!data) {

            throw new Error(
                "The recommendation service returned an empty response. Please try again shortly."
            );

        }


        // -------------------------------------------------
        // SUCCESS
        // -------------------------------------------------

        displayRecommendations(
            data
        );


        setBackendStatus(true);


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );


        let message =
            error.message;


        /*
            Browser cannot connect to FastAPI.
        */

        if (
            error instanceof
            TypeError
        ) {

            message =
                "Cannot connect to the backend. " +
                "Make sure FastAPI is running.";

            setBackendStatus(false);

        }

        if (
            error.message.includes("HTTP 502") ||
            error.message.includes("HTTP 503")
        ) {

            setBackendStatus(false);

        }


        showError(
            message
        );


    } finally {

        setLoading(false);

    }

}


// =========================================================
// DISPLAY RECOMMENDATIONS
// =========================================================

function displayRecommendations(
    data
) {

    const recommendations =
        data.recommendations || [];


    // -----------------------------------------------------
    // Show results section
    // -----------------------------------------------------

    resultsSection.classList.remove(
        "hidden"
    );


    // -----------------------------------------------------
    // Update header
    // -----------------------------------------------------

    resultCount.textContent =
        recommendations.length;


    currentSongName.textContent =
        data.song_name || songNameInput.value;


    currentArtistName.textContent =
        data.artist_name ||
        artistNameInput.value;


    methodBadge.textContent =
        data.filtering_type ||
        filteringTypeSelect.value;


    // -----------------------------------------------------
    // Clear old cards
    // -----------------------------------------------------

    recommendationsGrid.innerHTML =
        "";


    // -----------------------------------------------------
    // No recommendations
    // -----------------------------------------------------

    if (
        recommendations.length === 0
    ) {

        showEmptyResults();

        return;
    }


    // -----------------------------------------------------
    // Create cards
    // -----------------------------------------------------

    recommendations.forEach(
        (song, index) => {

            const card =
                createSongCard(
                    song,
                    index
                );

            recommendationsGrid.appendChild(
                card
            );

        }
    );


    // -----------------------------------------------------
    // Scroll to results
    // -----------------------------------------------------

    setTimeout(
        () => {

            resultsSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        },
        100
    );

}


// =========================================================
// CREATE SONG CARD
// =========================================================

function createSongCard(
    song,
    index
) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        "song-card";


    // -----------------------------------------------------
    // Song number
    // -----------------------------------------------------

    const number =
        document.createElement(
            "div"
        );

    number.className =
        "song-number";

    number.textContent =
        String(
            index + 1
        ).padStart(
            2,
            "0"
        );


    // -----------------------------------------------------
    // Album artwork placeholder
    // -----------------------------------------------------

    const artwork =
        document.createElement(
            "div"
        );

    artwork.className =
        "song-art";

    artwork.textContent =
        "♪";


    // -----------------------------------------------------
    // Song information
    // -----------------------------------------------------

    const info =
        document.createElement(
            "div"
        );

    info.className =
        "song-info";


    const title =
        document.createElement(
            "h3"
        );

    title.textContent =
        song.name ||
        "Unknown Song";


    const artist =
        document.createElement(
            "p"
        );

    artist.textContent =
        song.artist ||
        "Unknown Artist";


    info.appendChild(
        title
    );

    info.appendChild(
        artist
    );


    // -----------------------------------------------------
    // Similarity score
    // -----------------------------------------------------

    if (
        song.score !== undefined &&
        song.score !== null &&
        song.score !== ""
    ) {

        const scoreRow =
            document.createElement(
                "div"
            );

        scoreRow.className =
            "score-row";


        const scoreLabel =
            document.createElement(
                "span"
            );

        scoreLabel.textContent =
            "Match";


        const score =
            document.createElement(
                "strong"
            );

        score.textContent =
            formatScore(
                song.score
            );


        scoreRow.appendChild(
            scoreLabel
        );

        scoreRow.appendChild(
            score
        );

        info.appendChild(
            scoreRow
        );

    }


    // -----------------------------------------------------
    // Play button
    // -----------------------------------------------------

    const playButton =
        document.createElement(
            "button"
        );

    playButton.className =
        "play-button";


    playButton.type =
        "button";


    playButton.textContent =
        "▶";


    playButton.title =
        "Play preview";


    const previewUrl =
        song.spotify_preview_url;


    if (!previewUrl) {

        playButton.style.opacity =
            "0.35";

        playButton.title =
            "Preview unavailable";

    }


    playButton.addEventListener(
        "click",
        () => {

            playPreview(
                previewUrl,
                playButton
            );

        }
    );


    // -----------------------------------------------------
    // Build card
    // -----------------------------------------------------

    card.appendChild(
        number
    );

    card.appendChild(
        artwork
    );

    card.appendChild(
        info
    );

    card.appendChild(
        playButton
    );


    return card;
}


// =========================================================
// FORMAT SCORE
// =========================================================

function formatScore(
    score
) {

    const numericScore =
        Number(score);


    if (
        Number.isNaN(
            numericScore
        )
    ) {

        return "-";

    }


    /*
        The backend returns similarity
        between 0 and 1.

        Convert to percentage.
    */

    const percentage =
        Math.max(
            0,
            Math.min(
                100,
                numericScore * 100
            )
        );


    return (
        percentage.toFixed(1)
        + "%"
    );
}


// =========================================================
// AUDIO PREVIEW
// =========================================================

function playPreview(
    previewUrl,
    button
) {

    if (!previewUrl) {

        showError(
            "Preview is not available for this song."
        );

        return;
    }


    // -----------------------------------------------------
    // Clicking currently playing song
    // -----------------------------------------------------

    if (
        currentAudio &&
        currentPlayButton === button
    ) {

        if (
            currentAudio.paused
        ) {

            currentAudio.play();

            button.textContent =
                "❚❚";

        } else {

            currentAudio.pause();

            button.textContent =
                "▶";

        }

        return;
    }


    // -----------------------------------------------------
    // Stop previous audio
    // -----------------------------------------------------

    stopAudio();


    // -----------------------------------------------------
    // Create audio
    // -----------------------------------------------------

    const audio =
        new Audio(
            previewUrl
        );


    currentAudio =
        audio;

    currentPlayButton =
        button;


    button.textContent =
        "❚❚";


    audio.volume =
        0.8;


    // -----------------------------------------------------
    // Play
    // -----------------------------------------------------

    audio.play()
        .catch(
            () => {

                showError(
                    "Unable to play this preview."
                );

                resetPlayButton();

            }
        );


    // -----------------------------------------------------
    // Audio ended
    // -----------------------------------------------------

    audio.addEventListener(
        "ended",
        () => {

            resetPlayButton();

        }
    );


    // -----------------------------------------------------
    // Audio error
    // -----------------------------------------------------

    audio.addEventListener(
        "error",
        () => {

            showError(
                "This preview could not be played."
            );

            resetPlayButton();

        }
    );

}


// =========================================================
// STOP AUDIO
// =========================================================

function stopAudio() {

    if (currentAudio) {

        currentAudio.pause();

        currentAudio.currentTime =
            0;

    }


    resetPlayButton();


    currentAudio =
        null;

    currentPlayButton =
        null;
}


// =========================================================
// RESET PLAY BUTTON
// =========================================================

function resetPlayButton() {

    if (
        currentPlayButton
    ) {

        currentPlayButton.textContent =
            "▶";

    }

}


// =========================================================
// SHOW EMPTY RESULTS
// =========================================================

function showEmptyResults() {

    const emptyState =
        document.createElement("div");

    emptyState.className = "empty-results";

    const icon =
        document.createElement("span");

    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "♫";

    const heading =
        document.createElement("h3");

    heading.textContent = "No recommendations found";

    const description =
        document.createElement("p");

    description.textContent = "Try another song and artist.";

    emptyState.append(icon, heading, description);
    recommendationsGrid.replaceChildren(emptyState);
}


// =========================================================
// SHOW ERROR
// =========================================================

function showError(
    message
) {

    errorText.textContent =
        message;

    errorMessage.classList.remove(
        "hidden"
    );


    errorMessage.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// =========================================================
// CLEAR ERROR
// =========================================================

function clearError() {

    errorText.textContent =
        "";

    errorMessage.classList.add(
        "hidden"
    );

}


// =========================================================
// LOADING STATE
// =========================================================

function setLoading(
    isLoading
) {

    recommendButton.disabled =
        isLoading;


    if (isLoading) {

        buttonIcon.innerHTML =
            `<span class="loading-spinner"></span>`;

        buttonText.textContent =
            "Finding Songs...";

    } else {

        buttonIcon.textContent =
            "↗";

        buttonText.textContent =
            "Find my next favorite";

    }

}