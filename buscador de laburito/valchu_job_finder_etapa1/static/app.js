/* ============================================================
   VALCHU JOB FINDER
   FRONTEND JAVASCRIPT
============================================================ */


/* ============================================================
   ELEMENTOS
============================================================ */

const searchInput =
    document.getElementById("searchInput");

const locationFilter =
    document.getElementById("locationFilter");

const scoreFilter =
    document.getElementById("scoreFilter");

const clearFilters =
    document.getElementById("clearFilters");

const visibleCount =
    document.getElementById("visibleCount");

const noFilterResults =
    document.getElementById("noFilterResults");

const refreshButton =
    document.getElementById("refreshButton");

const refreshIcon =
    document.getElementById("refreshIcon");


/* ============================================================
   OFERTAS
============================================================ */

const jobCards =
    Array.from(
        document.querySelectorAll(".job-card")
    );


/* ============================================================
   NORMALIZAR TEXTO
============================================================ */

function normalizeText(text) {

    return String(text || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim();

}


/* ============================================================
   FILTRAR OFERTAS
============================================================ */

function filterJobs() {

    const search =
        normalizeText(
            searchInput.value
        );


    const location =
        normalizeText(
            locationFilter.value
        );


    const minimumScore =
        Number(
            scoreFilter.value
        );


    let visible = 0;


    jobCards.forEach(card => {

        const title =
            normalizeText(
                card.dataset.title
            );


        const company =
            normalizeText(
                card.dataset.company
            );


        const locationScope =
            normalizeText(
                card.dataset.location
            );


        const locationText =
            normalizeText(
                card.dataset.locationText
            );


        const skills =
            normalizeText(
                card.dataset.skills
            );


        const score =
            Number(
                card.dataset.score || 0
            );


        /* ----------------------------------------------------
           BUSCADOR
        ---------------------------------------------------- */

        const matchesSearch =

            !search ||

            title.includes(search) ||

            company.includes(search) ||

            skills.includes(search);


        /* ----------------------------------------------------
           UBICACIÓN
        ---------------------------------------------------- */

        let matchesLocation = true;


        if (
            location &&
            location !== "all"
        ) {

            matchesLocation =

                locationScope === location ||

                locationText.includes(location);

        }


        /* ----------------------------------------------------
           SCORE
        ---------------------------------------------------- */

        const matchesScore =

            score >= minimumScore;


        /* ----------------------------------------------------
           RESULTADO
        ---------------------------------------------------- */

        const visibleCard =

            matchesSearch &&
            matchesLocation &&
            matchesScore;


        if (visibleCard) {

            card.classList.remove(
                "hidden"
            );

            visible++;

        } else {

            card.classList.add(
                "hidden"
            );

        }

    });


    /* ========================================================
       CONTADOR
    ======================================================== */

    visibleCount.textContent =

        visible === 1

            ? "1 oferta"

            : `${visible} ofertas`;


    /* ========================================================
       MENSAJE SIN RESULTADOS
    ======================================================== */

    if (
        visible === 0 &&
        jobCards.length > 0
    ) {

        noFilterResults.classList.remove(
            "hidden"
        );

    } else {

        noFilterResults.classList.add(
            "hidden"
        );

    }

}


/* ============================================================
   EVENTOS DE FILTROS
============================================================ */

if (searchInput) {

    searchInput.addEventListener(
        "input",
        filterJobs
    );

}


if (locationFilter) {

    locationFilter.addEventListener(
        "change",
        filterJobs
    );

}


if (scoreFilter) {

    scoreFilter.addEventListener(
        "change",
        filterJobs
    );

}


if (clearFilters) {

    clearFilters.addEventListener(
        "click",
        () => {

            searchInput.value = "";

            locationFilter.value = "ALL";

            scoreFilter.value = "0";

            filterJobs();

        }
    );

}


/* ============================================================
   ACTUALIZAR OFERTAS
============================================================ */

if (refreshButton) {

    refreshButton.addEventListener(
        "click",
        async () => {

            refreshButton.classList.add(
                "loading"
            );

            refreshIcon.textContent = "⟳";


            try {

                const response =
                    await fetch(
                        "/refresh",
                        {
                            method: "POST"
                        }
                    );


                const result =
                    await response.json();


                if (!result.success) {

                    throw new Error(
                        result.message ||
                        "No se pudieron actualizar las ofertas."
                    );

                }


                refreshIcon.textContent = "✓";


                setTimeout(
                    () => {
                        window.location.reload();
                    },
                    500
                );


            } catch (error) {

                console.error(
                    "Error actualizando ofertas:",
                    error
                );


                alert(
                    "No se pudieron actualizar las ofertas.\n\n" +
                    error.message
                );


                refreshIcon.textContent = "↻";

                refreshButton.classList.remove(
                    "loading"
                );

            }

        }
    );

}


/* ============================================================
   INICIALIZAR
============================================================ */

filterJobs();