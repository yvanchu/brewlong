(async function () {
  "use strict";

  // ===== Load tea data =====
  const res = await fetch("teas.json");
  const data = await res.json();
  const TEAS = data.teas;

  const app = document.getElementById("app");

  // ===== Helpers =====
  function formatTime(seconds) {
    if (seconds <= 0) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m > 0) return `${m}:${s.toString().padStart(2, "0")}`;
    return `:${s.toString().padStart(2, "0")}`;
  }

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  // ===== Stage states =====
  const IDLE = "idle";
  const RUNNING = "running";
  const PAUSED = "paused";
  const COMPLETED = "completed";
  const DONE = "done";

  // ===== Column controller =====
  function createColumn() {
    const col = el("div", "column");
    const state = {
      selectedTea: null,
      selectedType: null,
      stages: [], // { state, remaining, total, volume, el, timerEl, intervalId }
      infoOutlined: true,
    };

    // --- Selection screen ---
    const selScreen = el("div", "selection");

    // Tea list
    const teaGroup = el("div", "list-group");
    teaGroup.appendChild(el("div", "list-label", "Tea"));
    const teaItems = el("div", "list-items");
    TEAS.forEach((tea, i) => {
      const item = el("div", "list-item", tea.name);
      item.addEventListener("click", () => selectTea(i));
      teaItems.appendChild(item);
    });
    teaGroup.appendChild(teaItems);
    selScreen.appendChild(teaGroup);

    // Type list
    const typeGroup = el("div", "list-group");
    typeGroup.appendChild(el("div", "list-label", "Type"));
    const typeItems = el("div", "list-items");
    ["hot", "ice", "milk"].forEach((type) => {
      const label = type.charAt(0).toUpperCase() + type.slice(1);
      const item = el("div", "list-item", label);
      item.dataset.type = type;
      item.addEventListener("click", () => selectType(type));
      typeItems.appendChild(item);
    });
    typeGroup.appendChild(typeItems);
    selScreen.appendChild(typeGroup);

    // Start button
    const startBtn = el("button", "btn-start", "Start");
    startBtn.disabled = true;
    startBtn.addEventListener("click", startBrew);
    selScreen.appendChild(startBtn);

    col.appendChild(selScreen);

    // --- Brewing screen ---
    const brewScreen = el("div", "brewing");

    const infoBox = el("div", "info-box outlined");
    const infoName = el("div", "info-tea-name");
    const infoGrams = el("div", "info-grams");
    infoBox.appendChild(infoName);
    infoBox.appendChild(infoGrams);
    brewScreen.appendChild(infoBox);

    const stagesContainer = el("div", "stages-container");
    brewScreen.appendChild(stagesContainer);

    const cancelBtn = el("button", "btn-cancel", "Cancel");
    cancelBtn.addEventListener("click", resetColumn);
    brewScreen.appendChild(cancelBtn);

    col.appendChild(brewScreen);
    app.appendChild(col);

    // --- Selection logic ---
    function selectTea(index) {
      state.selectedTea = index;
      state.selectedType = null;

      // Highlight tea
      Array.from(teaItems.children).forEach((item, i) => {
        item.classList.toggle("selected", i === index);
      });

      // Update type availability
      const tea = TEAS[index];
      Array.from(typeItems.children).forEach((item) => {
        const t = item.dataset.type;
        const available = t in tea.types;
        item.classList.toggle("disabled", !available);
        item.classList.remove("selected");
      });

      updateStartBtn();
    }

    function selectType(type) {
      if (state.selectedTea === null) return;
      const tea = TEAS[state.selectedTea];
      if (!(type in tea.types)) return;

      state.selectedType = type;

      Array.from(typeItems.children).forEach((item) => {
        item.classList.toggle("selected", item.dataset.type === type);
      });

      updateStartBtn();
    }

    function updateStartBtn() {
      startBtn.disabled =
        state.selectedTea === null || state.selectedType === null;
    }

    // --- Brewing logic ---
    function startBrew() {
      const tea = TEAS[state.selectedTea];
      const config = tea.types[state.selectedType];
      const typeLabel =
        state.selectedType.charAt(0).toUpperCase() +
        state.selectedType.slice(1);

      // Set info box
      infoName.textContent = `${typeLabel} ${tea.name}`;
      infoGrams.textContent = `${config.grams}g`;
      infoBox.classList.add("outlined");
      state.infoOutlined = true;

      // Build stage boxes
      stagesContainer.innerHTML = "";
      state.stages = [];

      config.stages.forEach((stageConfig, i) => {
        const box = el("div", "stage-box idle");
        const label = el("div", "stage-label", `Stage ${i + 1}`);
        const timer = el("div", "stage-timer", formatTime(stageConfig.time));
        const volume = el("div", "stage-volume", `${stageConfig.volume}ml`);
        const check = el("div", "stage-done-check", "✓");

        box.appendChild(label);
        box.appendChild(volume);
        box.appendChild(timer);
        box.appendChild(check);

        box.addEventListener("click", () => tapStage(i));
        stagesContainer.appendChild(box);

        state.stages.push({
          state: IDLE,
          remaining: stageConfig.time,
          total: stageConfig.time,
          volume: stageConfig.volume,
          el: box,
          timerEl: timer,
          intervalId: null,
        });
      });

      // Outline first stage as expected if there's only info to look at
      // (info box is outlined initially; first stage gets expected after info is dismissed)

      // Switch screens
      selScreen.classList.add("hidden");
      brewScreen.classList.add("active");
    }

    function tapStage(index) {
      const stage = state.stages[index];

      switch (stage.state) {
        case IDLE:
          // Pause any running stage
          pauseAllRunning();
          removeInfoOutline();
          startStageTimer(index);
          break;
        case RUNNING:
          pauseStageTimer(index);
          break;
        case PAUSED:
          pauseAllRunning();
          resumeStageTimer(index);
          break;
        case COMPLETED:
          dismissStage(index);
          break;
        case DONE:
          // No action
          break;
      }
    }

    function removeInfoOutline() {
      if (state.infoOutlined) {
        infoBox.classList.remove("outlined");
        state.infoOutlined = false;
      }
    }

    function pauseAllRunning() {
      state.stages.forEach((s, i) => {
        if (s.state === RUNNING) {
          pauseStageTimer(i);
        }
      });
    }

    function startStageTimer(index) {
      const stage = state.stages[index];
      setStageState(index, RUNNING);

      // Remove expected from all, this one is now running
      clearExpectedOutlines();

      stage.startedAt = Date.now();
      stage.intervalId = setInterval(() => {
        const elapsed = Math.floor((Date.now() - stage.startedAt) / 1000);
        const newRemaining = Math.max(0, stage.remaining - elapsed);

        stage.timerEl.textContent = formatTime(newRemaining);

        if (newRemaining <= 0) {
          clearInterval(stage.intervalId);
          stage.intervalId = null;
          stage.remaining = 0;
          setStageState(index, COMPLETED);
        }
      }, 250); // Update 4x/sec for accuracy
    }

    function pauseStageTimer(index) {
      const stage = state.stages[index];
      if (stage.intervalId) {
        clearInterval(stage.intervalId);
        stage.intervalId = null;

        // Calculate accurate remaining
        const elapsed = Math.floor((Date.now() - stage.startedAt) / 1000);
        stage.remaining = Math.max(0, stage.remaining - elapsed);
        stage.timerEl.textContent = formatTime(stage.remaining);
      }
      setStageState(index, PAUSED);
    }

    function resumeStageTimer(index) {
      const stage = state.stages[index];
      clearExpectedOutlines();

      stage.startedAt = Date.now();
      stage.intervalId = setInterval(() => {
        const elapsed = Math.floor((Date.now() - stage.startedAt) / 1000);
        const newRemaining = Math.max(0, stage.remaining - elapsed);

        stage.timerEl.textContent = formatTime(newRemaining);

        if (newRemaining <= 0) {
          clearInterval(stage.intervalId);
          stage.intervalId = null;
          stage.remaining = 0;
          setStageState(index, COMPLETED);
        }
      }, 250);

      setStageState(index, RUNNING);
    }

    function dismissStage(index) {
      setStageState(index, DONE);

      // Check if all stages are done
      const allDone = state.stages.every((s) => s.state === DONE);
      if (allDone) {
        setTimeout(resetColumn, 1000);
        return;
      }

      // Outline next idle stage
      for (let i = index + 1; i < state.stages.length; i++) {
        if (state.stages[i].state === IDLE) {
          state.stages[i].el.classList.add("expected");
          break;
        }
      }
    }

    function clearExpectedOutlines() {
      state.stages.forEach((s) => s.el.classList.remove("expected"));
    }

    function setStageState(index, newState) {
      const stage = state.stages[index];
      stage.el.classList.remove(
        IDLE,
        RUNNING,
        PAUSED,
        COMPLETED,
        DONE,
        "expected",
      );
      stage.state = newState;
      stage.el.classList.add(newState);
    }

    function resetColumn() {
      // Clear all timers
      state.stages.forEach((s) => {
        if (s.intervalId) {
          clearInterval(s.intervalId);
          s.intervalId = null;
        }
      });

      state.stages = [];
      state.selectedTea = null;
      state.selectedType = null;
      state.infoOutlined = true;

      // Reset selection UI
      Array.from(teaItems.children).forEach((item) =>
        item.classList.remove("selected"),
      );
      Array.from(typeItems.children).forEach((item) => {
        item.classList.remove("selected", "disabled");
      });
      startBtn.disabled = true;

      // Switch screens
      brewScreen.classList.remove("active");
      selScreen.classList.remove("hidden");
    }
  }

  // ===== Initialize 4 columns =====
  for (let i = 0; i < 4; i++) {
    createColumn();
  }
})();
