(() => {
  "use strict";

  const DATABASE_NAME = "universo-rebeldia";
  const DATABASE_VERSION = 1;
  const PROJECT_STORE = "projects";

  function requestToPromise(request) {
    return new Promise((resolve, reject) => {
      request.addEventListener("success", () => resolve(request.result));
      request.addEventListener("error", () => reject(request.error));
    });
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
      request.addEventListener("upgradeneeded", () => {
        const database = request.result;
        if (!database.objectStoreNames.contains(PROJECT_STORE)) {
          const store = database.createObjectStore(PROJECT_STORE, { keyPath: "id" });
          store.createIndex("updatedAt", "updatedAt");
        }
      });
      request.addEventListener("success", () => resolve(request.result));
      request.addEventListener("error", () => reject(request.error));
      request.addEventListener("blocked", () => reject(new Error("O banco local está bloqueado por outra aba.")));
    });
  }

  async function withStore(mode, action) {
    const database = await openDatabase();
    try {
      const transaction = database.transaction(PROJECT_STORE, mode);
      const result = await action(transaction.objectStore(PROJECT_STORE));
      await new Promise((resolve, reject) => {
        transaction.addEventListener("complete", resolve);
        transaction.addEventListener("abort", () => reject(transaction.error));
        transaction.addEventListener("error", () => reject(transaction.error));
      });
      return result;
    } finally {
      database.close();
    }
  }

  function normalizeProject(project) {
    const now = new Date().toISOString();
    const normalized = {
      id: typeof project.id === "string" && project.id
        ? project.id
        : (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`),
      name: String(project.name || "").trim(),
      problem: String(project.problem || "").trim(),
      solution: String(project.solution || "").trim(),
      components: String(project.components || "").trim(),
      expectedResult: String(project.expectedResult || "").trim(),
      observations: String(project.observations || "").trim(),
      missionId: String(project.missionId || ""),
      createdAt: typeof project.createdAt === "string" && project.createdAt ? project.createdAt : now,
      updatedAt: now
    };
    if (!normalized.name || !normalized.problem || !normalized.solution) {
      throw new TypeError("Projeto sem nome, problema ou solução.");
    }
    return normalized;
  }

  async function getProjects() {
    const projects = await withStore("readonly", (store) => requestToPromise(store.getAll()));
    return projects.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  }

  async function getProject(id) {
    return withStore("readonly", (store) => requestToPromise(store.get(id)));
  }

  async function saveProject(project) {
    const normalized = normalizeProject(project);
    await withStore("readwrite", (store) => requestToPromise(store.put(normalized)));
    return normalized;
  }

  async function deleteProject(id) {
    await withStore("readwrite", (store) => requestToPromise(store.delete(id)));
  }

  async function countProjects() {
    return withStore("readonly", (store) => requestToPromise(store.count()));
  }

  async function replaceProjects(projects) {
    if (!Array.isArray(projects)) throw new TypeError("A lista de projetos é inválida.");
    const normalized = projects.map(normalizeProject);
    await withStore("readwrite", (store) => {
      const requests = [requestToPromise(store.clear())];
      normalized.forEach((project) => requests.push(requestToPromise(store.put(project))));
      return Promise.all(requests);
    });
    return normalized;
  }

  async function clearProjects() {
    await withStore("readwrite", (store) => requestToPromise(store.clear()));
  }

  window.UniverseDB = {
    getProjects,
    getProject,
    saveProject,
    deleteProject,
    countProjects,
    replaceProjects,
    clearProjects
  };
})();
