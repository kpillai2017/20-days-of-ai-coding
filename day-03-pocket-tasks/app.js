/* The model knows tasks; this file connects it to forms and browser storage.
   An IIFE keeps changing UI variables out of the global namespace. */
(() => {
  "use strict";
  const model = globalThis.PocketTasks;
  const STORAGE_KEY = "20-days-of-ai-coding:pocket-tasks:v1";
  const form = document.getElementById("task-form");
  const input = document.getElementById("task-input");
  const list = document.getElementById("task-list");
  const warning = document.getElementById("storage-warning");
  const resetButton = document.getElementById("reset-storage");
  const saveState = document.getElementById("save-state");
  const errorOutput = document.getElementById("form-error");
  const announcement = document.getElementById("announcement");
  const clearButton = document.getElementById("clear-completed");
  const filters = [...document.querySelectorAll("[data-filter]")];
  let tasks = [];
  let filter = "all";
  let invalidSavedData = false;

  function showWarning(message) {
    warning.textContent = message;
    warning.hidden = !message;
  }

  /** Reading localStorage can throw, even when its property exists. Never
      overwrite invalid data silently: the user must explicitly discard it. */
  function load() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      try {
        tasks = model.parseTasks(raw);
        saveState.textContent = "Saved on this browser";
      } catch {
        invalidSavedData = true;
        resetButton.hidden = false;
        saveState.textContent = "Saving blocked";
        showWarning("The saved list is invalid or from an unsupported version. It has not been changed. You can work temporarily, or discard it to enable saving. Back up the storage value in Developer Tools first if you need it.");
      }
    } catch {
      saveState.textContent = "Temporary list";
      showWarning("Browser storage is unavailable. You can use this list, but changes may disappear when you reload. Try serving the app locally or allowing site storage.");
    }
  }

  /** A failed save must not crash the app or falsely claim data was saved. */
  function save() {
    if (invalidSavedData) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, model.serializeTasks(tasks));
      saveState.textContent = "Saved on this browser";
      showWarning("");
    } catch {
      saveState.textContent = "Unsaved changes";
      showWarning("Could not save your changes. They remain in this tab only. Browser storage may be blocked or full; try again after correcting that. Do not reload if you need these changes.");
    }
  }

  function announce(message) {
    announcement.textContent = message;
  }

  /** Rebuild a tiny list from state. textContent treats task text literally,
      including strings such as <img ...>; never insert task text with innerHTML. */
  function render() {
    const visible = model.filterTasks(tasks, filter);
    list.replaceChildren();
    visible.forEach(task => {
      const item = document.createElement("li");
      item.className = task.completed ? "task completed" : "task";
      const label = document.createElement("label");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = task.completed;
      checkbox.dataset.id = task.id;
      checkbox.dataset.action = "toggle";
      const text = document.createElement("span");
      text.textContent = task.text;
      label.append(checkbox, text);
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "delete";
      deleteButton.textContent = "Delete";
      deleteButton.setAttribute("aria-label", `Delete task: ${task.text}`);
      deleteButton.dataset.id = task.id;
      deleteButton.dataset.action = "delete";
      item.append(label, deleteButton);
      list.append(item);
    });
    const active = model.countActive(tasks);
    document.getElementById("remaining").textContent = `${active} ${active === 1 ? "task" : "tasks"} left`;
    document.getElementById("total").textContent = `${tasks.length} ${tasks.length === 1 ? "task" : "tasks"} total`;
    clearButton.disabled = tasks.every(task => !task.completed);
    const empty = document.getElementById("empty-state");
    empty.hidden = visible.length !== 0;
    empty.textContent = tasks.length === 0
      ? "Your list is clear. Add your first small step above."
      : `No ${filter} tasks. Try another filter or add a task.`;
    filters.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.filter === filter)));
  }

  /** After a render removes the focused control, deliberately restore focus.
      Match data using equality rather than putting saved IDs into a selector. */
  function focusTask(id, action) {
    const target = [...list.querySelectorAll("[data-action]")].find(
      element => element.dataset.id === id && element.dataset.action === action
    );
    (target || input).focus();
  }

  function commit(nextTasks, message) {
    tasks = nextTasks;
    save();
    render();
    announce(message);
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    try {
      // randomUUID is available on localhost/secure origins in modern browsers.
      // A timestamp plus random suffix is a fallback, not a security token.
      let id;
      do {
        id = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      } while (tasks.some(task => task.id === id));
      const result = model.addTask(tasks, input.value, id);
      // Show a newly added task even if the Completed filter was selected.
      filter = "all";
      commit(result.tasks, "Task added.");
      input.value = "";
      errorOutput.hidden = true;
      input.removeAttribute("aria-invalid");
      input.focus();
    } catch (error) {
      errorOutput.textContent = error.message;
      errorOutput.hidden = false;
      input.setAttribute("aria-invalid", "true");
      input.focus();
    }
  });

  // Event delegation uses two listeners for the whole list, rather than one
  // handler per task. Checkbox CHANGE includes keyboard and pointer activation.
  list.addEventListener("change", event => {
    const control = event.target;
    if (control.dataset.action !== "toggle") return;
    commit(model.toggleTask(tasks, control.dataset.id), "Task updated.");
    focusTask(control.dataset.id, "toggle");
  });
  list.addEventListener("click", event => {
    const control = event.target.closest("button[data-action='delete']");
    if (!control) return;
    commit(model.deleteTask(tasks, control.dataset.id), "Task deleted.");
    input.focus();
  });
  filters.forEach(button => button.addEventListener("click", () => {
    filter = button.dataset.filter;
    render();
    announce(`Showing ${filter} tasks.`);
  }));
  clearButton.addEventListener("click", () => {
    commit(model.clearCompleted(tasks), "Completed tasks cleared.");
    // The clear button becomes disabled, so move focus somewhere usable.
    input.focus();
  });
  resetButton.addEventListener("click", () => {
    if (!window.confirm("Discard the invalid saved list and save the list currently shown? This cannot be undone.")) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, model.serializeTasks(tasks));
      invalidSavedData = false;
      resetButton.hidden = true;
      showWarning("");
      saveState.textContent = "Saved on this browser";
      announce("Invalid saved list replaced with the current list.");
      input.focus();
    } catch {
      showWarning("Could not replace the saved list. Storage is blocked or full. The old value has not been discarded by this app.");
    }
  });

  load();
  render();
})();
