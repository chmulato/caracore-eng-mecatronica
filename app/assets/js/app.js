(() => {
  "use strict";

  const STORAGE_KEY = "universo-rebeldia-state-v1";
  const pageContent = document.querySelector("#page-content");
  const toast = document.querySelector("#toast");
  const searchInput = document.querySelector("#global-search-input");
  let chapters = [];
  let glossary = [];
  let conceptMap = { categories: [], connections: [] };
  let challengeData = { questions: [], missions: [], tracks: [], levels: [], badges: [], totalPoints: 0 };
  let timeline = [];
  let projects = [];
  let activeTrack = "";
  let activeTimelineCategory = "all";
  let missionSaveTimer = 0;
  let installPrompt = null;
  let activeRoute = "dashboard";
  let activeChapterId = "";
  let chapterFilter = "all";
  let activeConceptCategory = "";
  let activeGlossaryCategory = "all";
  let searchTerm = "";
  let toastTimer = 0;
  let saveTimer = 0;

  function emptyState() {
    return {
      read: [],
      favorites: [],
      notes: {},
      studiedConcepts: [],
      quizResults: {},
      missions: {},
      preferences: { theme: "dark", fontScale: 100, reduceMotion: false },
      lastChapter: ""
    };
  }

  function loadState() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return emptyState();
    try {
      const parsed = JSON.parse(stored);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Formato inválido");
      return {
        read: Array.isArray(parsed.read) ? parsed.read.filter((id) => typeof id === "string") : [],
        favorites: Array.isArray(parsed.favorites) ? parsed.favorites.filter((id) => typeof id === "string") : [],
        notes: parsed.notes && typeof parsed.notes === "object" && !Array.isArray(parsed.notes) ? parsed.notes : {},
        studiedConcepts: Array.isArray(parsed.studiedConcepts) ? parsed.studiedConcepts.filter((id) => typeof id === "string") : [],
        quizResults: parsed.quizResults && typeof parsed.quizResults === "object" && !Array.isArray(parsed.quizResults) ? parsed.quizResults : {},
        missions: parsed.missions && typeof parsed.missions === "object" && !Array.isArray(parsed.missions) ? parsed.missions : {},
        preferences: {
          theme: ["dark", "light", "system"].includes(parsed.preferences?.theme) ? parsed.preferences.theme : "dark",
          fontScale: Number.isFinite(parsed.preferences?.fontScale)
            ? Math.min(125, Math.max(90, parsed.preferences.fontScale))
            : 100,
          reduceMotion: parsed.preferences?.reduceMotion === true
        },
        lastChapter: typeof parsed.lastChapter === "string" ? parsed.lastChapter : ""
      };
    } catch (error) {
      console.error("Não foi possível ler o progresso local.", error);
      showToast("O progresso salvo estava inválido. Uma nova jornada foi iniciada.");
      return emptyState();
    }
  }

  let state;
  try {
    state = loadState();
  } catch (error) {
    console.error("O armazenamento local não está disponível.", error);
    state = emptyState();
    showToast("O armazenamento local está indisponível; as alterações não serão mantidas.");
  }
  applyPreferences();

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    if (activeRoute === "configuracoes") renderRoute();
  });
  window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
    if (state.preferences.theme === "system") applyPreferences();
  });

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch (error) {
      console.error("Não foi possível salvar o progresso local.", error);
      showToast("Não foi possível salvar. Verifique o espaço disponível no dispositivo.");
      return false;
    }
  }

  function applyPreferences() {
    const preferences = state.preferences;
    const systemLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    const resolvedTheme = preferences.theme === "system" ? (systemLight ? "light" : "dark") : preferences.theme;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.fontSize = `${preferences.fontScale}%`;
    document.documentElement.classList.toggle("reduce-motion", preferences.reduceMotion);
  }

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3000);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  function inlineMarkdown(text) {
    const codeTokens = [];
    let safe = escapeHtml(text);
    safe = safe.replace(/`([^`]+)`/g, (_, code) => {
      const token = `@@CODE${codeTokens.length}@@`;
      codeTokens.push(`<code>${code}</code>`);
      return token;
    });
    safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
    safe = safe.replace(/~~(.+?)~~/g, "<del>$1</del>");
    return safe.replace(/@@CODE(\d+)@@/g, (_, index) => codeTokens[Number(index)]);
  }

  function renderMarkdown(markdown) {
    const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
    const output = [];
    let paragraph = [];
    let listType = "";
    let codeLines = [];
    let inCode = false;

    const flushParagraph = () => {
      if (paragraph.length) output.push(`<p>${paragraph.map(inlineMarkdown).join("<br>")}</p>`);
      paragraph = [];
    };
    const flushList = () => {
      if (listType) output.push(`</${listType}>`);
      listType = "";
    };
    const addListItem = (type, value) => {
      flushParagraph();
      if (listType !== type) {
        flushList();
        output.push(`<${type}>`);
        listType = type;
      }
      output.push(`<li>${inlineMarkdown(value)}</li>`);
    };

    for (const line of lines) {
      if (/^\s*```/.test(line)) {
        flushParagraph();
        flushList();
        if (inCode) {
          output.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
          codeLines = [];
        }
        inCode = !inCode;
        continue;
      }
      if (inCode) {
        codeLines.push(line);
        continue;
      }
      if (!line.trim()) {
        flushParagraph();
        flushList();
        continue;
      }
      const heading = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (heading) {
        flushParagraph();
        flushList();
        const level = heading[1].length;
        output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
        continue;
      }
      if (/^\s*(---+|\*\*\*+|___+)\s*$/.test(line)) {
        flushParagraph();
        flushList();
        output.push("<hr>");
        continue;
      }
      const quote = line.match(/^\s*>\s?(.*)$/);
      if (quote) {
        flushParagraph();
        flushList();
        output.push(`<blockquote><p>${inlineMarkdown(quote[1])}</p></blockquote>`);
        continue;
      }
      const unordered = line.match(/^\s*[-*+]\s+(.+)$/);
      if (unordered) {
        addListItem("ul", unordered[1]);
        continue;
      }
      const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (ordered) {
        addListItem("ol", ordered[1]);
        continue;
      }
      flushList();
      paragraph.push(line.trim());
    }
    flushParagraph();
    flushList();
    if (inCode) output.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    return output.join("\n");
  }

  async function loadPage(route) {
    const response = await fetch(`pages/${route}.html`);
    if (!response.ok) throw new Error(`Falha ao carregar ${route}: HTTP ${response.status}`);
    return response.text();
  }

  function parseRoute() {
    const raw = location.hash.replace(/^#\/?/, "");
    const [routePart, queryPart = ""] = raw.split("?");
    const params = new URLSearchParams(queryPart);
    return {
      page: ["livro", "conceitos", "enciclopedia", "desafios", "laboratorio", "timeline", "configuracoes"].includes(routePart)
        ? routePart
        : "dashboard",
      chapter: params.get("c") || "",
      favoritesOnly: params.get("f") === "1",
      concept: params.get("t") || "",
      category: params.get("g") || "",
      track: params.get("tr") || "",
      challenge: params.get("d") || "",
      project: params.get("p") || ""
    };
  }

  function setRoute(route, params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    location.hash = `/${route}${query.size ? `?${query}` : ""}`;
  }

  function setShellHeading(title, route) {
    document.querySelector("#page-heading").textContent = title;
    document.querySelector("#breadcrumb-current").textContent = title;
    document.querySelectorAll(".primary-nav a").forEach((link) => {
      if (link.dataset.route === route) link.classList.add("active");
      else link.classList.remove("active");
    });
  }

  function getChapter(id) {
    return chapters.find((chapter) => chapter.id === id);
  }

  function getGlossaryTerm(id) {
    return glossary.find((term) => term.id === id);
  }

  function updateDashboard() {
    const readCount = state.read.filter((id) => getChapter(id)).length;
    const percentage = chapters.length ? Math.round(readCount / chapters.length * 100) : 0;
    const stat = document.querySelector("#reading-stat");
    if (!stat) return;
    stat.textContent = `${percentage}%`;
    document.querySelector("#reading-detail").textContent = `${readCount} de ${chapters.length} capítulos concluídos`;
    document.querySelector("#reading-progress-bar").style.width = `${percentage}%`;
    document.querySelector(".progress-track").setAttribute("aria-valuenow", String(percentage));
    document.querySelector("#concepts-stat").textContent = String(state.studiedConcepts.filter((id) => getGlossaryTerm(id)).length);
    const stats = challengeStats();
    const points = earnedPoints();
    document.querySelector("#challenges-stat").textContent = String(stats.completed);
    const challengesDetail = document.querySelector("#challenges-detail");
    if (challengesDetail) {
      challengesDetail.textContent = `${points} pontos · ${currentLevel(points).title}`;
    }
    window.UniverseDB.countProjects().then((count) => {
      const projectsStat = document.querySelector("#projects-stat");
      if (projectsStat) projectsStat.textContent = String(count);
    }).catch((error) => {
      console.error("Não foi possível contar os projetos.", error);
      const detail = document.querySelector("#projects-detail");
      if (detail) detail.textContent = "Armazenamento indisponível";
    });
    const lastChapter = getChapter(state.lastChapter);
    document.querySelector("#continue-description").textContent = lastChapter
      ? `Última leitura: ${lastChapter.title}`
      : "Sua jornada começa com o primeiro capítulo.";
    document.querySelector("#continue-link").href = lastChapter
      ? `#/livro?c=${encodeURIComponent(lastChapter.id)}`
      : "#/livro";

    const achievements = [
      { label: "Primeira conexão — abra um capítulo", done: Boolean(lastChapter) },
      { label: "Leitor em movimento — conclua um capítulo", done: readCount > 0 },
      { label: "Explorador — conclua 5 capítulos", done: readCount >= 5 },
      ...unlockedBadges().map((badge) => ({ label: `${badge.title} — ${badge.description}`, done: badge.unlocked }))
    ];
    document.querySelector("#achievements-list").innerHTML = achievements.map((item) =>
      `<div class="achievement-item${item.done ? " done" : ""}"><span aria-hidden="true">${item.done ? "✦" : "◇"}</span><span>${escapeHtml(item.label)}${item.done ? " · Conquistada" : ""}</span></div>`
    ).join("");
  }

  function termsInCategory(categoryId) {
    const category = conceptMap.categories.find((item) => item.id === categoryId);
    return category ? category.concepts.map(getGlossaryTerm).filter(Boolean) : [];
  }

  function renderConceptCategories() {
    const container = document.querySelector("#concept-categories");
    if (!container) return;
    container.innerHTML = conceptMap.categories.map((category) =>
      `<button class="concept-category${category.id === activeConceptCategory ? " active" : ""}" type="button" data-category-id="${escapeHtml(category.id)}" aria-pressed="${category.id === activeConceptCategory}">
        <strong>${escapeHtml(category.title)}</strong><span>${termsInCategory(category.id).length} conceitos</span>
      </button>`
    ).join("");
    container.querySelectorAll("[data-category-id]").forEach((button) => {
      button.addEventListener("click", () => {
        setRoute("conceitos", { g: button.dataset.categoryId });
      });
    });
    document.querySelector("#concepts-count").textContent = `${glossary.length} conceitos · ${conceptMap.connections.length} conexões`;
  }

  function renderConceptNodes(selectedId) {
    const container = document.querySelector("#concept-node-list");
    if (!container) return;
    const terms = termsInCategory(activeConceptCategory);
    container.innerHTML = terms.map((term) =>
      `<button class="concept-node${term.id === selectedId ? " active" : ""}" type="button" data-concept-id="${escapeHtml(term.id)}" aria-pressed="${term.id === selectedId}">
        <span class="concept-node-dot" aria-hidden="true"></span><span>${escapeHtml(term.title)}</span>
      </button>`
    ).join("");
    container.querySelectorAll("[data-concept-id]").forEach((button) => {
      button.addEventListener("click", () => {
        setRoute("conceitos", { g: activeConceptCategory, t: button.dataset.conceptId });
      });
    });
  }

  function chapterReferenceLink(reference) {
    const match = reference.match(/(\d+)/);
    const chapter = match
      ? chapters.find((item) => new RegExp(`^Capítulo\\s+${Number(match[1])}\\s*:`).test(item.title))
      : null;
    return chapter
      ? `<a class="reference-chip" href="#/livro?c=${encodeURIComponent(chapter.id)}">${escapeHtml(reference)}</a>`
      : `<span class="reference-chip">${escapeHtml(reference)}</span>`;
  }

  function renderConceptDetail(termId, category) {
    const container = document.querySelector("#concept-detail");
    if (!container) return;
    const term = getGlossaryTerm(termId);
    if (!term) {
      container.innerHTML = '<div class="empty-reader"><span aria-hidden="true">⌘</span><h2>Selecione um conceito</h2><p>As conexões e definições aparecem aqui.</p></div>';
      return;
    }
    const related = term.related.map(getGlossaryTerm).filter(Boolean);
    const studied = state.studiedConcepts.includes(term.id);
    container.innerHTML = `<p class="eyebrow">${escapeHtml(category?.title || activeConceptCategory)}</p>
      <h2>${escapeHtml(term.title)}</h2>
      <p class="concept-definition">${escapeHtml(term.definition)}</p>
      <div class="concept-insight"><h3>Analogia do livro</h3><p>${escapeHtml(term.analogy || "Consulte o capítulo relacionado para explorar este conceito.")}</p></div>
      <div class="concept-connections"><h3>Conceitos conectados <span>${related.length}</span></h3>
        <div class="reference-chip-list">${related.length
          ? related.map((item) => `<button class="reference-chip related-term" type="button" data-term-id="${escapeHtml(item.id)}">${escapeHtml(item.title)} <span aria-hidden="true">→</span></button>`).join("")
          : '<span class="muted">Ainda sem conexões registradas.</span>'}</div>
      </div>
      <button class="small-button concept-study-toggle" id="concept-study-toggle" type="button" aria-pressed="${studied}">${studied ? "✓ Estudado" : "Marcar como estudado"}</button>
      <a class="text-link concept-encyclopedia-link" href="#/enciclopedia?t=${encodeURIComponent(term.id)}">Abrir na enciclopédia <span aria-hidden="true">→</span></a>`;
    container.querySelectorAll(".related-term").forEach((button) => {
      button.addEventListener("click", () => setRoute("enciclopedia", { t: button.dataset.termId }));
    });
    container.querySelector("#concept-study-toggle").addEventListener("click", () => {
      state.studiedConcepts = studied
        ? state.studiedConcepts.filter((id) => id !== term.id)
        : [...state.studiedConcepts, term.id];
      saveState();
      updateDashboard();
      renderConceptDetail(term.id, category);
      showToast(studied ? "Conceito removido dos estudados." : "Conceito marcado como estudado.");
    });
  }

  function attachConceptsPage(route) {
    activeConceptCategory = conceptMap.categories.some((item) => item.id === route.category)
      ? route.category
      : conceptMap.categories[0]?.id || "";
    const term = getGlossaryTerm(route.concept) || termsInCategory(activeConceptCategory)[0];
    if (term && !termsInCategory(activeConceptCategory).some((item) => item.id === term.id)) {
      activeConceptCategory = conceptMap.categories.find((item) => item.concepts.includes(term.id))?.id || activeConceptCategory;
    }
    const category = conceptMap.categories.find((item) => item.id === activeConceptCategory);
    renderConceptCategories();
    renderConceptNodes(term?.id || "");
    renderConceptDetail(term?.id || "", category);
  }

  function matchingGlossaryTerms() {
    let result = glossary;
    if (activeGlossaryCategory !== "all") {
      const category = conceptMap.categories.find((item) => item.id === activeGlossaryCategory);
      result = category ? result.filter((term) => category.concepts.includes(term.id)) : result;
    }
    const localFilter = document.querySelector("#encyclopedia-filter")?.value.trim().toLocaleLowerCase("pt-BR");
    const terms = [searchTerm, localFilter].filter(Boolean).map((value) => value.toLocaleLowerCase("pt-BR"));
    return result.filter((term) => {
      const searchable = [term.title, term.definition, term.analogy, term.example, ...term.chapters]
        .join(" ").toLocaleLowerCase("pt-BR");
      return terms.every((value) => searchable.includes(value));
    });
  }

  function renderEncyclopediaCategories() {
    const container = document.querySelector("#encyclopedia-categories");
    if (!container) return;
    const filters = [{ id: "all", title: "Todos os termos" }, ...conceptMap.categories];
    container.innerHTML = filters.map((category) =>
      `<button class="encyclopedia-filter${category.id === activeGlossaryCategory ? " active" : ""}" type="button" data-category-id="${escapeHtml(category.id)}" aria-pressed="${category.id === activeGlossaryCategory}">${escapeHtml(category.title)}</button>`
    ).join("");
    container.querySelectorAll("[data-category-id]").forEach((button) => {
      button.addEventListener("click", () => {
        setRoute("enciclopedia", { g: button.dataset.categoryId });
      });
    });
  }

  function renderEncyclopediaList(selectedId) {
    const container = document.querySelector("#encyclopedia-list");
    if (!container) return;
    const terms = matchingGlossaryTerms();
    const selected = selectedId || document.querySelector(".encyclopedia-term.active")?.dataset.termId;
    document.querySelector("#encyclopedia-count").textContent = `${terms.length} de ${glossary.length} termos`;
    if (!terms.length) {
      container.innerHTML = '<p class="no-results">Nenhum termo corresponde à busca.</p>';
      return;
    }
    container.innerHTML = terms.map((term) =>
      `<button class="encyclopedia-term${term.id === selected ? " active" : ""}" type="button" data-term-id="${escapeHtml(term.id)}">
        <strong>${escapeHtml(term.title)}</strong><span>${escapeHtml(term.definition)}</span>
      </button>`
    ).join("");
    container.querySelectorAll("[data-term-id]").forEach((button) => {
      button.addEventListener("click", () => {
        setRoute("enciclopedia", { g: activeGlossaryCategory === "all" ? "" : activeGlossaryCategory, t: button.dataset.termId });
      });
    });
  }

  function renderEncyclopediaDetail(termId) {
    const container = document.querySelector("#encyclopedia-detail");
    if (!container) return;
    const term = getGlossaryTerm(termId);
    if (!term) {
      container.innerHTML = '<div class="empty-reader"><span aria-hidden="true">⌕</span><h2>Selecione um termo</h2><p>Consulte definições, exemplos e conexões com outros conceitos.</p></div>';
      return;
    }
    const related = term.related.map(getGlossaryTerm).filter(Boolean);
    const chaptersMarkup = term.chapters.length
      ? term.chapters.map(chapterReferenceLink).join("")
      : '<span class="muted">Sem referência de capítulo cadastrada.</span>';
    container.innerHTML = `<p class="eyebrow">GLOSSÁRIO DO LIVRO</p>
      <h2>${escapeHtml(term.title)}</h2>
      <section class="encyclopedia-entry"><h3>Definição</h3><p>${escapeHtml(term.definition)}</p></section>
      ${term.analogy ? `<section class="encyclopedia-entry"><h3>Analogia</h3><p>${escapeHtml(term.analogy)}</p></section>` : ""}
      ${term.example ? `<section class="encyclopedia-entry"><h3>Aplicação prática</h3><p>${escapeHtml(term.example)}</p></section>` : ""}
      <section class="encyclopedia-entry"><h3>Capítulos relacionados</h3><div class="reference-chip-list">${chaptersMarkup}</div></section>
      <section class="encyclopedia-entry"><h3>Conceitos conectados</h3><div class="reference-chip-list">${related.length
        ? related.map((item) => `<button class="reference-chip related-term" type="button" data-term-id="${escapeHtml(item.id)}">${escapeHtml(item.title)} <span aria-hidden="true">→</span></button>`).join("")
        : '<span class="muted">Ainda sem conexões registradas.</span>'}</div></section>
      <button class="small-button concept-study-toggle" id="encyclopedia-study-toggle" type="button" aria-pressed="${state.studiedConcepts.includes(term.id)}">${state.studiedConcepts.includes(term.id) ? "✓ Estudado" : "Marcar como estudado"}</button>`;
    container.querySelectorAll(".related-term").forEach((button) => {
      button.addEventListener("click", () => {
        renderEncyclopediaList(button.dataset.termId);
        renderEncyclopediaDetail(button.dataset.termId);
        setRoute("enciclopedia", { t: button.dataset.termId });
      });
    });
    container.querySelector("#encyclopedia-study-toggle").addEventListener("click", () => {
      const studied = state.studiedConcepts.includes(term.id);
      state.studiedConcepts = studied
        ? state.studiedConcepts.filter((id) => id !== term.id)
        : [...state.studiedConcepts, term.id];
      saveState();
      updateDashboard();
      renderEncyclopediaDetail(term.id);
      showToast(studied ? "Conceito removido dos estudados." : "Conceito marcado como estudado.");
    });
  }

  function attachEncyclopediaPage(route) {
    activeGlossaryCategory = route.category && conceptMap.categories.some((item) => item.id === route.category)
      ? route.category
      : "all";
    const filter = document.querySelector("#encyclopedia-filter");
    filter.value = searchTerm;
    filter.addEventListener("input", () => {
      const terms = matchingGlossaryTerms();
      const selected = terms.some((item) => item.id === route.concept) ? route.concept : terms[0]?.id || "";
      renderEncyclopediaList(selected);
      renderEncyclopediaDetail(selected);
    });
    renderEncyclopediaCategories();
    const terms = matchingGlossaryTerms();
    const selected = terms.some((item) => item.id === route.concept) ? route.concept : terms[0]?.id || "";
    renderEncyclopediaList(selected);
    renderEncyclopediaDetail(selected);
  }

  function allChallenges() {
    return [...challengeData.questions, ...challengeData.missions];
  }

  function getChallenge(id) {
    return allChallenges().find((item) => item.id === id);
  }

  function isMission(item) {
    return item.type === "missao" || item.type === "experimento";
  }

  function isChallengeDone(item) {
    if (!item) return false;
    if (isMission(item)) return state.missions[item.id]?.done === true;
    return state.quizResults[item.id]?.correct === true;
  }

  function trackItems(trackId) {
    const track = challengeData.tracks.find((item) => item.id === trackId);
    return track ? track.items.map(getChallenge).filter(Boolean) : [];
  }

  function earnedPoints() {
    return allChallenges().reduce((total, item) => total + (isChallengeDone(item) ? item.points : 0), 0);
  }

  function challengeStats() {
    const correctAnswers = challengeData.questions.filter((item) => isChallengeDone(item)).length;
    const caseAnswers = challengeData.questions.filter((item) => item.type === "caso" && isChallengeDone(item)).length;
    const missions = challengeData.missions.filter((item) => isChallengeDone(item)).length;
    const completedTracks = challengeData.tracks.filter((track) => {
      const items = trackItems(track.id);
      return items.length > 0 && items.every(isChallengeDone);
    }).length;
    return { correctAnswers, caseAnswers, missions, completedTracks, completed: correctAnswers + missions };
  }

  function currentLevel(points) {
    const levels = challengeData.levels;
    if (!levels.length) return { title: "Aprendiz de bancada", minPoints: 0 };
    return levels.reduce((best, level) => (points >= level.minPoints ? level : best), levels[0]);
  }

  function unlockedBadges() {
    const stats = challengeStats();
    return challengeData.badges.map((badge) => ({
      ...badge,
      unlocked: (stats[badge.rule] || 0) >= badge.threshold,
      progress: Math.min(stats[badge.rule] || 0, badge.threshold)
    }));
  }

  function renderGamification() {
    const container = document.querySelector("#score-value");
    if (!container) return;
    const points = earnedPoints();
    const total = challengeData.totalPoints || 1;
    const percentage = Math.min(100, Math.round(points / total * 100));
    container.textContent = String(points);
    document.querySelector("#score-rank").textContent = currentLevel(points).title;
    document.querySelector("#score-bar").style.width = `${percentage}%`;
    document.querySelector("#score-track").setAttribute("aria-valuenow", String(percentage));
    document.querySelector("#score-detail").textContent = `${points} de ${challengeData.totalPoints} pontos possíveis`;
    document.querySelector("#badge-list").innerHTML = unlockedBadges().map((badge) =>
      `<div class="badge-item${badge.unlocked ? " unlocked" : ""}">
        <span class="badge-icon" aria-hidden="true">${badge.unlocked ? "✦" : "◇"}</span>
        <span class="badge-copy"><strong>${escapeHtml(badge.title)}</strong><small>${escapeHtml(badge.description)}${badge.unlocked ? " · Conquistada" : ` · ${badge.progress}/${badge.threshold}`}</small></span>
      </div>`
    ).join("");
  }

  function renderChallengeTracks() {
    const container = document.querySelector("#challenge-tracks");
    if (!container) return;
    container.innerHTML = challengeData.tracks.map((track) => {
      const items = trackItems(track.id);
      const done = items.filter(isChallengeDone).length;
      const percentage = items.length ? Math.round(done / items.length * 100) : 0;
      return `<button class="challenge-track${track.id === activeTrack ? " active" : ""}" type="button" data-track-id="${escapeHtml(track.id)}" aria-pressed="${track.id === activeTrack}">
        <strong>${escapeHtml(track.title)}</strong>
        <small>${done} de ${items.length} concluídos</small>
        <span class="track-progress"><i style="width:${percentage}%"></i></span>
      </button>`;
    }).join("");
    container.querySelectorAll("[data-track-id]").forEach((button) => {
      button.addEventListener("click", () => setRoute("desafios", { tr: button.dataset.trackId }));
    });
  }

  function challengeTypeLabel(item) {
    if (item.type === "quiz") return "Quiz";
    if (item.type === "caso") return "Estudo de caso";
    if (item.type === "experimento") return "Experimento de campo";
    return `Missão maker · Nível ${item.level}`;
  }

  function challengeTitle(item) {
    if (isMission(item)) return item.title;
    const concept = getGlossaryTerm(item.conceptId)?.title || item.prompt;
    return item.facet ? `${concept} · ${item.facet}` : concept;
  }

  function renderChallengeList(selectedId) {
    const container = document.querySelector("#challenge-list");
    if (!container) return;
    const items = trackItems(activeTrack);
    const stats = challengeStats();
    document.querySelector("#challenge-count").textContent = `${stats.completed} de ${allChallenges().length} desafios concluídos`;
    if (!items.length) {
      container.innerHTML = '<p class="no-results">Nenhum desafio nesta trilha.</p>';
      return;
    }
    container.innerHTML = items.map((item) => {
      const done = isChallengeDone(item);
      const failed = !done && !isMission(item) && state.quizResults[item.id];
      return `<button class="challenge-item${item.id === selectedId ? " active" : ""}${done ? " done" : ""}" type="button" data-challenge-id="${escapeHtml(item.id)}">
        <span class="challenge-item-top"><span class="challenge-type">${escapeHtml(challengeTypeLabel(item))}</span><span class="challenge-points">${item.points} pts</span></span>
        <strong>${escapeHtml(challengeTitle(item))}</strong>
        <small>${done ? "✓ Concluído" : failed ? "Tente novamente" : escapeHtml(item.chapterTitle || "Desafio pendente")}</small>
      </button>`;
    }).join("");
    container.querySelectorAll("[data-challenge-id]").forEach((button) => {
      button.addEventListener("click", () => setRoute("desafios", { tr: activeTrack, d: button.dataset.challengeId }));
    });
  }

  function answerQuestion(item, optionIndex) {
    const correct = optionIndex === item.answer;
    state.quizResults[item.id] = { option: optionIndex, correct };
    saveState();
    renderChallengeTracks();
    renderChallengeList(item.id);
    renderChallengeDetail(item.id);
    renderGamification();
    showToast(correct ? `Correto! +${item.points} pontos.` : "Resposta incorreta. Reveja a explicação e tente de novo.");
  }

  function renderQuestionDetail(container, item) {
    const result = state.quizResults[item.id];
    const answered = Boolean(result);
    const chapterLink = item.chapterId
      ? `<a class="text-link" href="#/livro?c=${encodeURIComponent(item.chapterId)}">Revisar ${escapeHtml(item.chapterTitle)} <span aria-hidden="true">→</span></a>`
      : "";
    container.innerHTML = `<p class="eyebrow">${escapeHtml(challengeTypeLabel(item))} · ${item.points} PONTOS</p>
      <h2>${escapeHtml(item.prompt)}</h2>
      <blockquote class="challenge-statement">${escapeHtml(item.statement)}</blockquote>
      <div class="challenge-options" role="group" aria-label="Alternativas">${item.options.map((option, index) => {
        const chosen = answered && result.option === index;
        const reveal = answered && result.correct && index === item.answer;
        const modifier = reveal || (chosen && result.correct) ? " correct" : chosen ? " wrong" : "";
        return `<button class="challenge-option${modifier}" type="button" data-option="${index}"${answered && result.correct ? " disabled" : ""}>
          <span class="option-mark" aria-hidden="true">${String.fromCharCode(65 + index)}</span>${escapeHtml(option)}
        </button>`;
      }).join("")}</div>
      ${answered ? `<div class="challenge-feedback${result.correct ? " correct" : " wrong"}" role="status">
        <strong>${result.correct ? "Resposta correta" : "Ainda não é essa"}</strong>
        <p>${escapeHtml(result.correct ? item.explanation : "Revise o conceito na enciclopédia e escolha outra alternativa.")}</p>
      </div>` : ""}
      <div class="challenge-actions">
        ${answered ? '<button class="small-button" id="reset-answer" type="button">Responder novamente</button>' : ""}
        <a class="small-button ghost" href="#/enciclopedia?t=${encodeURIComponent(item.conceptId)}">Abrir conceito</a>
      </div>
      ${chapterLink}`;
    container.querySelectorAll("[data-option]").forEach((button) => {
      button.addEventListener("click", () => answerQuestion(item, Number(button.dataset.option)));
    });
    container.querySelector("#reset-answer")?.addEventListener("click", () => {
      delete state.quizResults[item.id];
      saveState();
      renderChallengeTracks();
      renderChallengeList(item.id);
      renderChallengeDetail(item.id);
      renderGamification();
    });
  }

  function renderMissionDetail(container, item) {
    const log = state.missions[item.id] || { done: false, report: "" };
    container.innerHTML = `<p class="eyebrow">${escapeHtml(challengeTypeLabel(item))} · ${item.points} PONTOS</p>
      <h2>${escapeHtml(item.title)}</h2>
      <p class="muted">${escapeHtml(item.chapterTitle)} · ${escapeHtml(item.section)}</p>
      <div class="challenge-briefing">${renderMarkdown(item.briefing)}</div>
      <label class="mission-label" for="mission-report">Registro da missão</label>
      <textarea id="mission-report" rows="5" placeholder="Descreva o que você construiu, mediu ou concluiu.">${escapeHtml(log.report || "")}</textarea>
      <div class="challenge-actions">
        <button class="small-button" id="mission-toggle" type="button" aria-pressed="${log.done}">${log.done ? "✓ Missão concluída" : "Registrar conclusão"}</button>
        <a class="small-button ghost" href="#/livro?c=${encodeURIComponent(item.chapterId)}">Abrir capítulo</a>
      </div>`;
    const report = container.querySelector("#mission-report");
    report.addEventListener("input", () => {
      window.clearTimeout(missionSaveTimer);
      missionSaveTimer = window.setTimeout(() => {
        const current = state.missions[item.id] || { done: false, report: "" };
        state.missions[item.id] = { ...current, report: report.value };
        saveState();
      }, 400);
    });
    container.querySelector("#mission-toggle").addEventListener("click", () => {
      const current = state.missions[item.id] || { done: false, report: "" };
      state.missions[item.id] = { done: !current.done, report: report.value };
      saveState();
      renderChallengeTracks();
      renderChallengeList(item.id);
      renderChallengeDetail(item.id);
      renderGamification();
      showToast(state.missions[item.id].done ? `Missão concluída! +${item.points} pontos.` : "Missão reaberta.");
    });
  }

  function renderChallengeDetail(challengeId) {
    const container = document.querySelector("#challenge-detail");
    if (!container) return;
    const item = getChallenge(challengeId);
    if (!item) {
      container.innerHTML = '<div class="empty-reader"><span aria-hidden="true">◇</span><h2>Escolha um desafio</h2><p>Responda quizzes e estudos de caso ou registre o resultado de uma missão prática.</p></div>';
      return;
    }
    if (isMission(item)) renderMissionDetail(container, item);
    else renderQuestionDetail(container, item);
  }

  function attachChallengesPage(route) {
    const fromChallenge = challengeData.tracks.find((track) => track.items.includes(route.challenge));
    activeTrack = challengeData.tracks.some((track) => track.id === route.track)
      ? route.track
      : fromChallenge?.id || challengeData.tracks[0]?.id || "";
    const items = trackItems(activeTrack);
    const selected = items.some((item) => item.id === route.challenge) ? route.challenge : "";
    renderGamification();
    renderChallengeTracks();
    renderChallengeList(selected);
    renderChallengeDetail(selected);
  }

  function missionOptions(selectedId) {
    const completed = challengeData.missions.filter((mission) => isChallengeDone(mission) || mission.id === selectedId);
    return `<option value="">Sem missão vinculada</option>${completed.map((mission) =>
      `<option value="${escapeHtml(mission.id)}"${mission.id === selectedId ? " selected" : ""}>${escapeHtml(mission.title)}</option>`
    ).join("")}`;
  }

  function projectForm(project = {}) {
    const editing = Boolean(project.id);
    return `<form class="project-form" id="project-form">
      <div class="project-form-heading">
        <div><p class="eyebrow">${editing ? "EDITAR PROJETO" : "NOVO PROJETO"}</p><h2>${editing ? escapeHtml(project.name) : "Ficha técnica maker"}</h2></div>
        ${editing ? '<button class="small-button danger-button" id="delete-project" type="button">Excluir</button>' : ""}
      </div>
      <input type="hidden" name="id" value="${escapeHtml(project.id || "")}">
      <input type="hidden" name="createdAt" value="${escapeHtml(project.createdAt || "")}">
      <label for="project-name">Nome do projeto *</label>
      <input id="project-name" name="name" required maxlength="100" value="${escapeHtml(project.name || "")}" placeholder="Ex.: Robô seguidor de linha">
      <label for="project-problem">Problema *</label>
      <textarea id="project-problem" name="problem" required rows="3" placeholder="Que necessidade será resolvida?">${escapeHtml(project.problem || "")}</textarea>
      <label for="project-solution">Solução proposta *</label>
      <textarea id="project-solution" name="solution" required rows="3" placeholder="Como o sistema deve funcionar?">${escapeHtml(project.solution || "")}</textarea>
      <label for="project-components">Componentes</label>
      <textarea id="project-components" name="components" rows="3" placeholder="Sensores, atuadores, controladores, materiais...">${escapeHtml(project.components || "")}</textarea>
      <label for="project-result">Resultado esperado</label>
      <textarea id="project-result" name="expectedResult" rows="3" placeholder="Como será possível verificar o sucesso?">${escapeHtml(project.expectedResult || "")}</textarea>
      <label for="project-observations">Observações</label>
      <textarea id="project-observations" name="observations" rows="3" placeholder="Medições, riscos, próximos testes...">${escapeHtml(project.observations || "")}</textarea>
      <label for="project-mission">Missão concluída relacionada</label>
      <select id="project-mission" name="missionId">${missionOptions(project.missionId || "")}</select>
      <div class="project-form-actions">
        <button class="button button-primary" type="submit">${editing ? "Salvar alterações" : "Criar projeto"}</button>
        <button class="small-button ghost" id="cancel-project" type="button">Cancelar</button>
      </div>
    </form>`;
  }

  function renderProjectList(selectedId = "") {
    const container = document.querySelector("#project-list");
    if (!container) return;
    const filter = document.querySelector("#project-filter")?.value.trim().toLocaleLowerCase("pt-BR") || "";
    const visible = projects.filter((project) =>
      [project.name, project.problem, project.solution, project.components]
        .join(" ").toLocaleLowerCase("pt-BR").includes(filter)
    );
    document.querySelector("#lab-project-count").textContent = String(projects.length);
    document.querySelector("#lab-linked-count").textContent = String(projects.filter((project) => project.missionId).length);
    if (!visible.length) {
      container.innerHTML = `<p class="no-results">${projects.length ? "Nenhum projeto corresponde à busca." : "Nenhum projeto registrado."}</p>`;
      return;
    }
    container.innerHTML = visible.map((project) => {
      const mission = challengeData.missions.find((item) => item.id === project.missionId);
      return `<button class="project-item${project.id === selectedId ? " active" : ""}" type="button" data-project-id="${escapeHtml(project.id)}">
        <strong>${escapeHtml(project.name)}</strong>
        <span>${escapeHtml(project.problem)}</span>
        <small>${mission ? `Missão: ${escapeHtml(mission.title)}` : `Atualizado em ${new Date(project.updatedAt).toLocaleDateString("pt-BR")}`}</small>
      </button>`;
    }).join("");
    container.querySelectorAll("[data-project-id]").forEach((button) => {
      button.addEventListener("click", () => setRoute("laboratorio", { p: button.dataset.projectId }));
    });
  }

  function closeProjectEditor() {
    const workspace = document.querySelector("#project-workspace");
    workspace.innerHTML = '<div class="empty-reader"><span aria-hidden="true">⌁</span><h2>Comece um projeto</h2><p>Crie uma ficha técnica ou selecione um projeto existente para continuar.</p></div>';
  }

  function attachProjectForm(project) {
    const workspace = document.querySelector("#project-workspace");
    workspace.innerHTML = projectForm(project);
    const form = workspace.querySelector("#project-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const values = Object.fromEntries(new FormData(form));
      try {
        const saved = await window.UniverseDB.saveProject(values);
        const index = projects.findIndex((item) => item.id === saved.id);
        if (index >= 0) projects[index] = saved;
        else projects.unshift(saved);
        projects.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
        renderProjectList(saved.id);
        setRoute("laboratorio", { p: saved.id });
        showToast(project.id ? "Projeto atualizado." : "Projeto criado no laboratório.");
      } catch (error) {
        console.error("Não foi possível salvar o projeto.", error);
        showToast("Não foi possível salvar o projeto no banco local.");
      }
    });
    workspace.querySelector("#cancel-project").addEventListener("click", closeProjectEditor);
    workspace.querySelector("#delete-project")?.addEventListener("click", async () => {
      if (!window.confirm(`Excluir o projeto "${project.name}"?`)) return;
      try {
        await window.UniverseDB.deleteProject(project.id);
        projects = projects.filter((item) => item.id !== project.id);
        renderProjectList();
        closeProjectEditor();
        setRoute("laboratorio");
        showToast("Projeto excluído.");
      } catch (error) {
        console.error("Não foi possível excluir o projeto.", error);
        showToast("Não foi possível excluir o projeto.");
      }
    });
  }

  async function attachLaboratoryPage(route) {
    try {
      projects = await window.UniverseDB.getProjects();
    } catch (error) {
      console.error("Não foi possível abrir o laboratório.", error);
      document.querySelector("#project-workspace").innerHTML = '<div class="error-panel"><h2>Banco local indisponível</h2><p>Permita o armazenamento do site e tente novamente.</p></div>';
      return;
    }
    const selected = projects.find((project) => project.id === route.project);
    renderProjectList(selected?.id || "");
    document.querySelector("#project-filter").addEventListener("input", () => renderProjectList(selected?.id || ""));
    document.querySelector("#new-project").addEventListener("click", () => attachProjectForm({}));
    if (selected) attachProjectForm(selected);
  }

  function timelineCategories() {
    const labels = {
      all: "Todos",
      industria: "Indústria",
      controle: "Controle",
      computacao: "Computação",
      redes: "Redes",
      robotica: "Robótica",
      inteligencia: "Inteligência"
    };
    const present = [...new Set(timeline.map((event) => event.category))];
    return ["all", ...present].map((id) => ({ id, title: labels[id] || id }));
  }

  function renderTimeline() {
    const events = activeTimelineCategory === "all"
      ? timeline
      : timeline.filter((event) => event.category === activeTimelineCategory);
    document.querySelector("#timeline-count").textContent = `${events.length} marcos`;
    document.querySelector("#timeline-filters").innerHTML = timelineCategories().map((category) =>
      `<button class="encyclopedia-filter${category.id === activeTimelineCategory ? " active" : ""}" type="button" data-timeline-category="${escapeHtml(category.id)}" aria-pressed="${category.id === activeTimelineCategory}">${escapeHtml(category.title)}</button>`
    ).join("");
    document.querySelector("#technology-timeline").innerHTML = events.map((event) =>
      `<li class="timeline-event">
        <div class="timeline-year">${event.year}</div>
        <article class="content-card timeline-card">
          <p class="eyebrow">${escapeHtml(event.category)}</p>
          <h2>${escapeHtml(event.title)}</h2>
          <p>${escapeHtml(event.description)}</p>
          ${event.chapterId ? `<a class="text-link" href="#/livro?c=${encodeURIComponent(event.chapterId)}">Abrir capítulo relacionado <span aria-hidden="true">→</span></a>` : ""}
        </article>
      </li>`
    ).join("");
    document.querySelectorAll("[data-timeline-category]").forEach((button) => {
      button.addEventListener("click", () => {
        activeTimelineCategory = button.dataset.timelineCategory;
        renderTimeline();
      });
    });
  }

  function attachTimelinePage() {
    activeTimelineCategory = "all";
    renderTimeline();
  }

  async function exportUserData() {
    try {
      const data = {
        format: "universo-rebeldia-backup",
        version: 1,
        exportedAt: new Date().toISOString(),
        state,
        projects: await window.UniverseDB.getProjects()
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `universo-rebeldia-backup-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      showToast("Backup exportado.");
    } catch (error) {
      console.error("Não foi possível exportar os dados.", error);
      showToast("Não foi possível criar o backup.");
    }
  }

  async function importUserData(file) {
    const text = await file.text();
    const backup = JSON.parse(text);
    if (backup?.format !== "universo-rebeldia-backup" || backup.version !== 1
      || !backup.state || typeof backup.state !== "object" || !Array.isArray(backup.projects)) {
      throw new Error("Formato de backup inválido.");
    }
    await window.UniverseDB.replaceProjects(backup.projects);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(backup.state));
    location.reload();
  }

  function attachSettingsPage() {
    const theme = document.querySelector("#theme-select");
    const fontScale = document.querySelector("#font-scale");
    const fontOutput = document.querySelector("#font-scale-output");
    const motion = document.querySelector("#motion-setting");
    theme.value = state.preferences.theme;
    fontScale.value = String(state.preferences.fontScale);
    fontOutput.value = `${state.preferences.fontScale}%`;
    motion.checked = state.preferences.reduceMotion;

    theme.addEventListener("change", () => {
      state.preferences.theme = theme.value;
      saveState();
      applyPreferences();
    });
    fontScale.addEventListener("input", () => {
      state.preferences.fontScale = Number(fontScale.value);
      fontOutput.value = `${fontScale.value}%`;
      saveState();
      applyPreferences();
    });
    motion.addEventListener("change", () => {
      state.preferences.reduceMotion = motion.checked;
      saveState();
      applyPreferences();
    });

    const installButton = document.querySelector("#install-app");
    if (installPrompt) {
      installButton.disabled = false;
      document.querySelector("#install-description").textContent = "Instale para abrir em tela própria e acessar rapidamente.";
    } else if (window.matchMedia("(display-mode: standalone)").matches) {
      document.querySelector("#install-description").textContent = "O Universo Rebeldia já está instalado.";
    }
    installButton.addEventListener("click", async () => {
      if (!installPrompt) return;
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      installButton.disabled = true;
    });

    document.querySelector("#export-data").addEventListener("click", exportUserData);
    document.querySelector("#import-data").addEventListener("change", async (event) => {
      const [file] = event.target.files;
      if (!file) return;
      try {
        await importUserData(file);
      } catch (error) {
        console.error("Não foi possível importar o backup.", error);
        showToast(error.message || "Não foi possível importar o backup.");
        event.target.value = "";
      }
    });
    document.querySelector("#reset-data").addEventListener("click", async () => {
      if (!window.confirm("Apagar progresso, preferências e projetos deste dispositivo?")) return;
      try {
        localStorage.removeItem(STORAGE_KEY);
        await window.UniverseDB.clearProjects();
        location.reload();
      } catch (error) {
        console.error("Não foi possível apagar os dados locais.", error);
        showToast("Não foi possível concluir a limpeza.");
      }
    });
  }

  function chaptersForList() {
    let result = chapters;
    if (chapterFilter === "favorites") result = result.filter((chapter) => state.favorites.includes(chapter.id));
    const localFilter = document.querySelector("#chapter-filter")?.value.trim().toLocaleLowerCase("pt-BR");
    if (localFilter) {
      result = result.filter((chapter) =>
        chapter.title.toLocaleLowerCase("pt-BR").includes(localFilter)
        || chapter.content.toLocaleLowerCase("pt-BR").includes(localFilter)
      );
    }
    if (searchTerm) {
      const term = searchTerm.toLocaleLowerCase("pt-BR");
      result = result.filter((chapter) =>
        chapter.title.toLocaleLowerCase("pt-BR").includes(term)
        || chapter.content.toLocaleLowerCase("pt-BR").includes(term)
      );
    }
    return result;
  }

  function renderChapterList() {
    const nav = document.querySelector("#chapter-list");
    if (!nav) return;
    const matches = chaptersForList();
    if (!matches.length) {
      nav.innerHTML = '<p class="no-results">Nenhum capítulo encontrado.</p>';
      return;
    }
    nav.innerHTML = matches.map((chapter, index) => {
      const read = state.read.includes(chapter.id);
      const favorite = state.favorites.includes(chapter.id);
      return `<a class="chapter-item${chapter.id === activeChapterId ? " active" : ""}" href="#/livro?c=${encodeURIComponent(chapter.id)}" data-chapter-id="${escapeHtml(chapter.id)}">
        <span class="chapter-item-title">${escapeHtml(chapter.title)}</span>
        <span class="chapter-item-icons" aria-label="${read ? "Concluído" : ""}${favorite ? " Favorito" : ""}">${read ? '<span aria-label="Lido">✓</span>' : ""}${favorite ? '<span aria-label="Favorito">★</span>' : ""}</span>
        <span class="chapter-item-meta">Capítulo ${String(chapters.indexOf(chapter) + 1).padStart(2, "0")}${read ? " · Concluído" : ""}</span>
      </a>`;
    }).join("");
  }

  function highlightSearchTerms(container, term) {
    const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp(escaped, "giu");
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const text = node.nodeValue;
      pattern.lastIndex = 0;
      let match;
      let cursor = 0;
      const fragment = document.createDocumentFragment();
      let found = false;
      while ((match = pattern.exec(text)) !== null) {
        found = true;
        fragment.append(document.createTextNode(text.slice(cursor, match.index)));
        const mark = document.createElement("mark");
        mark.className = "search-highlight";
        mark.textContent = match[0];
        fragment.append(mark);
        cursor = match.index + match[0].length;
      }
      if (found) {
        fragment.append(document.createTextNode(text.slice(cursor)));
        node.replaceWith(fragment);
      }
    });
  }

  function renderActiveChapter() {
    const panel = document.querySelector("#reading-panel");
    if (!panel) return;
    const chapter = getChapter(activeChapterId);
    if (!chapter) {
      panel.innerHTML = '<div class="empty-reader"><span aria-hidden="true">▤</span><h2>Escolha um capítulo</h2><p>Selecione um capítulo na lista para começar a leitura.</p></div>';
      return;
    }
    const isRead = state.read.includes(chapter.id);
    const isFavorite = state.favorites.includes(chapter.id);
    panel.innerHTML = `<div class="chapter-toolbar">
      <span class="chapter-toolbar-label">FONTE: ${escapeHtml(chapter.source)}</span>
      <div class="chapter-actions">
        <button class="small-button favorite-toggle" id="favorite-toggle" type="button" aria-pressed="${isFavorite}">${isFavorite ? "★ Favorito" : "☆ Favoritar"}</button>
        <button class="small-button" id="read-toggle" type="button" aria-pressed="${isRead}">${isRead ? "✓ Concluído" : "Marcar como lido"}</button>
      </div>
    </div>
    <div class="markdown-content" id="chapter-body">${renderMarkdown(chapter.content)}</div>
    <div class="note-panel"><label for="chapter-note">Anotação pessoal</label><textarea id="chapter-note" placeholder="Registre uma ideia, dúvida ou conexão...">${escapeHtml(state.notes[chapter.id] || "")}</textarea><span class="note-status" id="note-status" aria-live="polite">Anotações salvas apenas neste dispositivo.</span>    </div>`;
    if (searchTerm) {
      highlightSearchTerms(document.querySelector("#chapter-body"), searchTerm);
    }

    document.querySelector("#favorite-toggle").addEventListener("click", () => {
      state.favorites = isFavorite
        ? state.favorites.filter((id) => id !== chapter.id)
        : [...state.favorites, chapter.id];
      saveState();
      renderChapterList();
      renderActiveChapter();
      showToast(isFavorite ? "Capítulo removido dos favoritos." : "Capítulo adicionado aos favoritos.");
    });
    document.querySelector("#read-toggle").addEventListener("click", () => {
      state.read = isRead ? state.read.filter((id) => id !== chapter.id) : [...state.read, chapter.id];
      saveState();
      renderChapterList();
      renderActiveChapter();
      updateDashboard();
      showToast(isRead ? "Capítulo reaberto." : "Capítulo marcado como concluído.");
    });
    document.querySelector("#chapter-note").addEventListener("input", (event) => {
      state.notes[chapter.id] = event.currentTarget.value;
      document.querySelector("#note-status").textContent = "Salvando…";
      window.clearTimeout(saveTimer);
      saveTimer = window.setTimeout(() => {
        if (saveState()) document.querySelector("#note-status").textContent = "Salvo neste dispositivo.";
      }, 250);
    });
    document.querySelector("#chapter-count").textContent = `${chapters.indexOf(chapter) + 1} / ${chapters.length}`;
    document.querySelector("#reading-panel").scrollIntoView({ block: "start", behavior: "smooth" });
  }

  function attachReaderEvents(route) {
    const filterInput = document.querySelector("#chapter-filter");
    if (filterInput) filterInput.addEventListener("input", renderChapterList);
    document.querySelectorAll(".filter-chip").forEach((button) => {
      button.addEventListener("click", () => {
        chapterFilter = button.dataset.filter;
        document.querySelectorAll(".filter-chip").forEach((chip) => chip.classList.toggle("active", chip === button));
        renderChapterList();
      });
    });
    const firstChapter = route.chapter || state.lastChapter || chapters[0]?.id || "";
    if (getChapter(firstChapter)) {
      activeChapterId = firstChapter;
      state.lastChapter = activeChapterId;
      saveState();
    } else {
      activeChapterId = "";
    }
    if (route.favoritesOnly) {
      chapterFilter = "favorites";
      document.querySelector('[data-filter="favorites"]')?.classList.add("active");
      document.querySelector('[data-filter="all"]')?.classList.remove("active");
    } else {
      chapterFilter = "all";
    }
    renderChapterList();
    renderActiveChapter();
  }

  async function renderRoute() {
    const route = parseRoute();
    activeRoute = route.page;
    const titles = {
      dashboard: "Dashboard",
      livro: "Livro interativo",
      conceitos: "Mapa de conceitos",
      enciclopedia: "Enciclopédia",
      desafios: "Desafios e missões",
      laboratorio: "Laboratório Maker",
      timeline: "Linha do tempo",
      configuracoes: "Configurações"
    };
    const title = titles[route.page];
    setShellHeading(title, route.page);
    try {
      pageContent.innerHTML = await loadPage(route.page);
    } catch (error) {
      console.error("Não foi possível carregar a tela.", error);
      pageContent.innerHTML = `<section class="error-panel"><h1>Não foi possível abrir esta tela</h1><p>${escapeHtml(error.message)}</p><button class="small-button" id="retry-page" type="button">Tentar novamente</button></section>`;
      document.querySelector("#retry-page").addEventListener("click", renderRoute);
      return;
    }
    if (route.page === "dashboard") updateDashboard();
    if (route.page === "livro") attachReaderEvents(route);
    if (route.page === "conceitos") attachConceptsPage(route);
    if (route.page === "enciclopedia") attachEncyclopediaPage(route);
    if (route.page === "desafios") attachChallengesPage(route);
    if (route.page === "laboratorio") await attachLaboratoryPage(route);
    if (route.page === "timeline") attachTimelinePage();
    if (route.page === "configuracoes") attachSettingsPage();
    if (searchTerm) searchInput.value = searchTerm;
    document.querySelector("#main-content").focus({ preventScroll: true });
  }

  async function runGlobalSearch(event) {
    event.preventDefault();
    searchTerm = searchInput.value.trim();
    const term = searchTerm.toLocaleLowerCase("pt-BR");
    const firstMatch = term
      ? chapters.find((chapter) =>
        chapter.title.toLocaleLowerCase("pt-BR").includes(term)
        || chapter.content.toLocaleLowerCase("pt-BR").includes(term)
      )
      : null;
    if (!term) {
      if (activeRoute === "livro") {
        renderChapterList();
        renderActiveChapter();
      }
      if (activeRoute === "enciclopedia") {
        document.querySelector("#encyclopedia-filter").value = "";
        renderEncyclopediaList();
        renderEncyclopediaDetail(parseRoute().concept);
      }
      return;
    }
    const termMatch = glossary.find((item) =>
      [item.title, item.definition, item.analogy, item.example]
        .some((value) => value.toLocaleLowerCase("pt-BR").includes(term))
    );
    if (termMatch) {
      const nextHash = `/enciclopedia?t=${encodeURIComponent(termMatch.id)}`;
      if (location.hash.replace(/^#/, "") === nextHash) renderRoute();
      else setRoute("enciclopedia", { t: termMatch.id });
      return;
    }
    const timelineMatch = timeline.find((item) =>
      [item.title, item.description, item.category, item.year]
        .some((value) => String(value).toLocaleLowerCase("pt-BR").includes(term))
    );
    if (timelineMatch) {
      setRoute("timeline");
      return;
    }
    try {
      const projectMatch = (await window.UniverseDB.getProjects()).find((project) =>
        [project.name, project.problem, project.solution, project.components, project.expectedResult, project.observations]
          .some((value) => String(value).toLocaleLowerCase("pt-BR").includes(term))
      );
      if (projectMatch) {
        setRoute("laboratorio", { p: projectMatch.id });
        return;
      }
    } catch (error) {
      console.error("Não foi possível pesquisar os projetos locais.", error);
    }
    if (!firstMatch) {
      const missionMatch = challengeData.missions.find((item) =>
        [item.title, item.briefing, item.section].some((value) => String(value).toLocaleLowerCase("pt-BR").includes(term))
      );
      if (missionMatch) {
        setRoute("desafios", { tr: "campo", d: missionMatch.id });
        return;
      }
      showToast("Nenhum conteúdo corresponde à busca.");
      return;
    }
    const nextHash = `/livro?c=${encodeURIComponent(firstMatch.id)}`;
    if (location.hash.replace(/^#/, "") === nextHash) renderRoute();
    else setRoute("livro", { c: firstMatch.id });
  }

  async function start() {
    try {
      const response = await fetch("data/capitulos.json");
      if (!response.ok) throw new Error(`Falha ao carregar capítulos: HTTP ${response.status}`);
      const loaded = await response.json();
      if (!Array.isArray(loaded) || loaded.some((chapter) => !chapter.id || !chapter.title || !chapter.content)) {
        throw new Error("O índice de capítulos possui um formato inválido.");
      }
      chapters = loaded;
      const [glossaryResponse, conceptsResponse, challengesResponse, timelineResponse] = await Promise.all([
        fetch("data/glossario.json"),
        fetch("data/conceitos.json"),
        fetch("data/desafios.json"),
        fetch("data/timeline.json")
      ]);
      if (!glossaryResponse.ok || !conceptsResponse.ok) {
        throw new Error("Falha ao carregar o glossário ou mapa de conceitos.");
      }
      if (!challengesResponse.ok) {
        throw new Error("Falha ao carregar o catálogo de desafios.");
      }
      if (!timelineResponse.ok) {
        throw new Error("Falha ao carregar a linha do tempo.");
      }
      const [glossaryData, conceptsData, challengesData, timelineData] = await Promise.all([
        glossaryResponse.json(),
        conceptsResponse.json(),
        challengesResponse.json(),
        timelineResponse.json()
      ]);
      if (!Array.isArray(glossaryData) || !Array.isArray(conceptsData.categories) || !Array.isArray(conceptsData.connections)) {
        throw new Error("Os dados da Fase 2 possuem um formato inválido.");
      }
      if (!challengesData || !Array.isArray(challengesData.questions) || !Array.isArray(challengesData.missions)
        || !Array.isArray(challengesData.tracks) || !Array.isArray(challengesData.levels) || !Array.isArray(challengesData.badges)) {
        throw new Error("O catálogo de desafios possui um formato inválido.");
      }
      if (!Array.isArray(timelineData) || timelineData.some((item) =>
        !Number.isInteger(item.year) || !item.title || !item.description || !item.category
      )) {
        throw new Error("A linha do tempo possui um formato inválido.");
      }
      glossary = glossaryData;
      conceptMap = conceptsData;
      challengeData = {
        ...challengesData,
        totalPoints: Number(challengesData.totalPoints) || 0
      };
      timeline = timelineData.sort((left, right) => left.year - right.year);
      window.addEventListener("hashchange", renderRoute);
      document.querySelector("#global-search").addEventListener("submit", runGlobalSearch);
      searchInput.addEventListener("input", () => {
        if (!searchInput.value && activeRoute === "livro") {
          searchTerm = "";
          renderChapterList();
          renderActiveChapter();
        }
        if (!searchInput.value && activeRoute === "enciclopedia") {
          searchTerm = "";
          document.querySelector("#encyclopedia-filter").value = "";
          renderEncyclopediaList();
          renderEncyclopediaDetail(parseRoute().concept);
        }
      });
      document.querySelector("#back-button").addEventListener("click", () => {
        if (history.length > 1) history.back();
        else setRoute("dashboard");
      });
      const menu = document.querySelector("#menu-toggle");
      menu.addEventListener("click", () => {
        const isOpen = document.querySelector("#sidebar").classList.toggle("open");
        menu.setAttribute("aria-expanded", String(isOpen));
        menu.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
      });
      document.querySelector("#sidebar").addEventListener("click", (event) => {
        if (event.target.closest("a")) {
          document.querySelector("#sidebar").classList.remove("open");
          menu.setAttribute("aria-expanded", "false");
          menu.setAttribute("aria-label", "Abrir menu");
        }
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
          event.preventDefault();
          searchInput.focus();
        }
      });
      await renderRoute();
    } catch (error) {
      console.error("Falha ao iniciar o Universo Rebeldia.", error);
      pageContent.innerHTML = `<section class="error-panel"><h1>Não foi possível iniciar o livro</h1><p>${escapeHtml(error.message)}</p><p>Se estiver em modo offline, conecte-se e abra o aplicativo uma vez para armazenar os arquivos.</p></section>`;
    }
  }

  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {
    navigator.serviceWorker.register("service-worker.js").catch((error) => {
      console.error("Falha ao registrar o service worker.", error);
      showToast("Não foi possível ativar a leitura offline neste navegador.");
    });
  }

  start();
})();
